"""Typed state-machine orchestration for evidence-backed action decisions."""
from __future__ import annotations
import inspect
from typing import Callable
from pydantic import BaseModel, Field
from app.agent.prompts import (SYSTEM_PROMPT, ActionPlanOutput, IntentOutput, ReasoningOutput,
                               action_planning_prompt, intent_extraction_prompt, reasoning_prompt)
from app.core.constants import AutonomyDecision, RiskLevel, Severity
from app.feedback.store import record_knowledge_gap
from app.knowledge.retrieval import retrieve
from app.llm.provider import (
    RATE_LIMIT_MESSAGE,
    UNAVAILABLE_MESSAGE,
    LLMProvider,
    get_llm,
    is_rate_limit_error,
    is_unavailable_error,
)
from app.models.schemas import ActionContract, AgentState, EvidenceItem, PolicyResult
from app.policy.engine import decide_autonomy, evaluate_policy

class RequestNodeOutput(BaseModel):
    request: str

class RetrievalNodeOutput(BaseModel):
    evidence: list[EvidenceItem] = Field(default_factory=list)

class PolicyCheckNodeOutput(BaseModel):
    policy_results: list[PolicyResult] = Field(default_factory=list)
    amount: float = 0

class DecisionNodeOutput(BaseModel):
    decision: AutonomyDecision
    reason: str

Retriever = Callable[[str], list[EvidenceItem]]

async def _llm_output(llm: LLMProvider, prompt: str, model: type[BaseModel]) -> BaseModel:
    return await llm.structured_model(prompt, model, system=SYSTEM_PROMPT)

async def request_node(state: AgentState) -> tuple[AgentState, RequestNodeOutput]:
    output = RequestNodeOutput(request=state.request)
    return state.model_copy(update={"request": output.request}), output

async def intent_node(state: AgentState, llm: LLMProvider) -> AgentState:
    output = await _llm_output(llm, intent_extraction_prompt(state.request), IntentOutput)
    assert isinstance(output, IntentOutput)
    return state.model_copy(update={"intent": output.request_type,
                                    "entities": {**output.entities, "desired_outcome": output.desired_outcome,
                                                 "urgency": output.urgency},
                                    "stage_statuses": _complete_stage(state, "understanding_request")})

async def retrieval_node(state: AgentState, retriever: Retriever) -> tuple[AgentState, RetrievalNodeOutput]:
    raw = retriever(state.request)
    evidence = await raw if inspect.isawaitable(raw) else raw
    output = RetrievalNodeOutput(evidence=evidence)
    best_score = max((item.relevance_score for item in output.evidence), default=0.0)
    if best_score < 0.70:
        record_knowledge_gap(
            run_id=state.run_id, query=state.request, confidence=best_score,
            evidence_ids=[item.id for item in output.evidence],
        )
    return state.model_copy(update={"evidence": output.evidence,
                                    "stage_statuses": _complete_stage(state, "retrieving_evidence")}), output

async def reasoning_node(state: AgentState, llm: LLMProvider) -> tuple[AgentState, ReasoningOutput]:
    evidence_payload = [{"id": e.id, "source": e.source, "section": e.section, "text": e.text}
                        for e in state.evidence]
    output = await _llm_output(llm, reasoning_prompt(state.request, evidence_payload), ReasoningOutput)
    assert isinstance(output, ReasoningOutput)
    allowed = {e.id for e in state.evidence}
    invalid = set(output.cited_evidence_ids) - allowed
    if invalid:
        raise ValueError(f"LLM cited evidence IDs not retrieved: {', '.join(sorted(invalid))}")
    return state.model_copy(update={"reasoning_summary": output.summary,
                                    "evidence_confidence": output.confidence,
                                    "severity": Severity(output.severity.upper()),
                                    "stage_statuses": _complete_stage(state, "reasoning")}), output

async def action_plan_node(state: AgentState, llm: LLMProvider,
                           reasoning: ReasoningOutput) -> tuple[AgentState, ActionPlanOutput]:
    valid_ids = {item.id for item in state.evidence}
    output = await _llm_output(llm, action_planning_prompt(state.request, reasoning, state.entities,
                                                           sorted(valid_ids)), ActionPlanOutput)
    assert isinstance(output, ActionPlanOutput)
    actions = [ActionContract(action_type=item.action_type, arguments=item.arguments, reason=item.reason,
                              evidence_ids=item.evidence_ids) for item in output.actions]
    invalid = {evidence_id for action in actions for evidence_id in action.evidence_ids} - valid_ids
    if invalid:
        raise ValueError(f"LLM cited evidence IDs not retrieved: {', '.join(sorted(invalid))}")
    return state.model_copy(update={"proposed_actions": actions,
                                    "stage_statuses": _complete_stage(state, "preparing_action_plan")}), output

async def policy_check_node(state: AgentState) -> tuple[AgentState, PolicyCheckNodeOutput]:
    results = [evaluate_policy(action) for action in state.proposed_actions]
    amounts = [_amount(action) for action in state.proposed_actions]
    amounts.extend(
        _coerce_amount(state.entities.get(key))
        for key in ("amount", "cost", "estimated_cost", "replacement_cost")
    )
    amount = max(amounts, default=0.0)
    output = PolicyCheckNodeOutput(policy_results=results, amount=amount)
    if results:
        risk = max((result.risk_level for result in results), key=lambda level: {
            RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2, RiskLevel.UNKNOWN: 3
        }[level])
        combined = PolicyResult(allowed=all(r.allowed for r in results),
                                requires_approval=any(r.requires_approval for r in results),
                                risk_level=risk,
                                reason=" ".join(r.reason for r in results),
                                matched_policy=", ".join(r.matched_policy for r in results if r.matched_policy))
    else:
        combined = PolicyResult(allowed=False, reason="No actions were proposed.")
    return state.model_copy(update={"policy_result": combined, "risk_level": combined.risk_level}), output

async def decision_node(state: AgentState, policy_output: PolicyCheckNodeOutput,
                        reasoning: ReasoningOutput) -> tuple[AgentState, DecisionNodeOutput]:
    policy = state.policy_result or PolicyResult(allowed=False, reason="Policy check missing.")
    cited_ids = set(reasoning.cited_evidence_ids) | {eid for a in state.proposed_actions for eid in a.evidence_ids}
    eval_evidence = [e for e in state.evidence if e.id in cited_ids] if cited_ids else state.evidence
    decision = decide_autonomy(policy, state.evidence_confidence, has_evidence=bool(state.evidence),
                               conflicting_evidence=reasoning.conflicting_evidence,
                               evidence=eval_evidence,
                               amount=policy_output.amount)
    reason = ("Evidence is missing, conflicting, or below 0.70 confidence." if decision == AutonomyDecision.ESCALATE
              else "Policy requires human approval." if decision == AutonomyDecision.APPROVAL_REQUIRED
              else "Evidence and policy permit execution.")
    output = DecisionNodeOutput(decision=decision, reason=reason)
    return state.model_copy(update={"autonomy_decision": output.decision,
                                    "approval_required": output.decision == AutonomyDecision.APPROVAL_REQUIRED,
                                    "status": output.decision.value,
                                    "final_response": reason,
                                    "stage_statuses": _complete_stage(state, "evaluating_policy")}), output

async def run_agent(request: str, *, llm: LLMProvider | None = None,
                    retriever: Retriever | None = None) -> AgentState:
    """Run REQUEST → INTENT → RETRIEVAL → REASONING → ACTION_PLAN → POLICY_CHECK → DECISION."""
    state = AgentState(request=request)
    evidence_retriever = retriever or retrieve
    state, _ = await request_node(state)
    active_stage = "understanding_request"
    try:
        provider = llm or get_llm()
        state = await intent_node(state, provider)
        active_stage = "retrieving_evidence"
        state, _ = await retrieval_node(state, evidence_retriever)
        active_stage = "reasoning"
        state, reasoning = await reasoning_node(state, provider)
        active_stage = "preparing_action_plan"
        state, _ = await action_plan_node(state, provider, reasoning)
        active_stage = "evaluating_policy"
        state, policy_output = await policy_check_node(state)
        state, _ = await decision_node(state, policy_output, reasoning)
    except Exception as exc:
        stage_statuses = dict(state.stage_statuses)
        stage_statuses[active_stage] = "failed"
        error = (
            RATE_LIMIT_MESSAGE if is_rate_limit_error(exc)
            else UNAVAILABLE_MESSAGE if is_unavailable_error(exc)
            else str(exc)
        )
        state = state.model_copy(update={"autonomy_decision": AutonomyDecision.ESCALATE,
                                         "status": AutonomyDecision.ESCALATE.value,
                                         "error": error,
                                         "failed_stage": active_stage,
                                         "stage_statuses": stage_statuses})
    return state

def _complete_stage(state: AgentState, stage: str) -> dict[str, str]:
    statuses = dict(state.stage_statuses)
    statuses[stage] = "complete"
    return statuses

def _amount(action: ActionContract) -> float:
    return _coerce_amount(action.arguments.get("amount", action.arguments.get("cost", 0)))

def _coerce_amount(value: object) -> float:
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return 0.0
