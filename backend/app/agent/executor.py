"""Policy-gated ordered action execution with verified compensating rollback."""
from __future__ import annotations

from typing import Awaitable, Callable, Sequence

from pydantic import BaseModel, Field

from app.agent.replan import replan_plan
from app.audit.logger import RunAuditRecord, log_run
from app.connectors.base import get_connector
from app.core.constants import AutonomyDecision
from app.models.schemas import ActionContract, ActionResult, AgentState
from app.policy.engine import decide_autonomy, evaluate_policy
from app.tools.registry import compensation_for, execute_action
from app.verification.verifier import VerificationResult, verify_action


class OrderedPlan(BaseModel):
    steps: list[ActionContract] = Field(min_length=1, max_length=5)


class CompensationRecord(BaseModel):
    original_action_id: str
    action: ActionContract
    result: ActionResult
    verification: VerificationResult


class ExecutionOutcome(BaseModel):
    state: AgentState
    audit: RunAuditRecord
    compensations: list[CompensationRecord] = Field(default_factory=list)


Replanner = Callable[..., Awaitable[list[ActionContract]]]
ToolRunner = Callable[[ActionContract], Awaitable[ActionResult]]
Verifier = Callable[[ActionContract, object | None], Awaitable[VerificationResult]]


async def execute_plan(
    state: AgentState,
    *,
    plan: Sequence[ActionContract] | None = None,
    replan: Replanner | None = None,
    tool_runner: ToolRunner = execute_action,
    verifier: Verifier = verify_action,
) -> ExecutionOutcome:
    """Execute at most five ordered steps, replan once, and compensate writes on final failure."""
    ordered = OrderedPlan(steps=list(plan if plan is not None else state.proposed_actions)).steps
    allowed_evidence = {item.id for item in state.evidence}
    attempted: list[tuple[ActionContract, ActionResult, VerificationResult]] = []
    completed: list[tuple[ActionContract, ActionResult]] = []
    compensations: list[CompensationRecord] = []
    failure_reason: str | None = None
    final_decision = AutonomyDecision.EXECUTE
    replanned = False
    index = 0

    if state.autonomy_decision != AutonomyDecision.EXECUTE:
        failure_reason = f"Workflow decision blocks execution: {state.autonomy_decision.value}"
        final_decision = state.autonomy_decision

    while failure_reason is None and index < len(ordered):
        action = ordered[index]
        invalid_ids = set(action.evidence_ids) - allowed_evidence
        if invalid_ids:
            failure_reason = f"Action cites unavailable evidence IDs: {', '.join(sorted(invalid_ids))}"
            final_decision = AutonomyDecision.ESCALATE
            break

        per_step = evaluate_policy(action)
        gate = decide_autonomy(
            per_step,
            state.evidence_confidence,
            has_evidence=bool(state.evidence),
            amount=_amount(action),
        )
        if gate != AutonomyDecision.EXECUTE:
            failure_reason = f"Policy gate blocked {action.action_type}: {per_step.reason}"
            final_decision = gate
            break

        result = await tool_runner(action)
        if result.success:
            completed.append((action, result))
            verification = await verifier(action, result)
        else:
            verification = VerificationResult(
                action_id=action.id, status="FAILED", verified=False,
                details=f"Execution failed: {result.error or 'unspecified tool failure'}",
            )
        attempted.append((action, result, verification))
        if result.success and verification.status == "VERIFIED":
            index += 1
            continue

        failure_reason = verification.details
        if result.success and verification.status == "FAILED":
            # A failed read-back requires immediate rollback; it cannot be retried as a new plan.
            final_decision = AutonomyDecision.ESCALATE
            break
        if replanned:
            final_decision = AutonomyDecision.ESCALATE
            break

        replanned = True
        try:
            planner = replan or replan_plan
            revised = await planner(
                request=state.request,
                failure_reason=failure_reason,
                completed_steps=[step for step, _ in completed],
                remaining_steps=ordered[index:],
                allowed_evidence_ids=allowed_evidence,
            )
            ordered = OrderedPlan(steps=revised).steps
            index = 0
            failure_reason = None
        except Exception as exc:
            failure_reason = f"Replanning failed: {exc}"
            final_decision = AutonomyDecision.ESCALATE
            break

    if failure_reason is not None:
        for original, original_result in reversed(completed):
            compensation = compensation_for(original, original_result)
            if compensation is None:
                continue
            result = await tool_runner(compensation)
            verification = await _verify_compensation(compensation) if result.success else VerificationResult(
                action_id=compensation.id, status="FAILED", verified=False,
                details=f"Compensation failed: {result.error or 'unspecified tool failure'}",
            )
            compensations.append(CompensationRecord(
                original_action_id=original.id, action=compensation,
                result=result, verification=verification,
            ))
            if verification.status != "VERIFIED":
                final_decision = AutonomyDecision.ESCALATE
                failure_reason = (
                    f"{failure_reason}; rollback failed for {original.action_type}: "
                    f"{verification.details}"
                )

    execution_results = [item[1] for item in attempted] + [item.result for item in compensations]
    verification_results = [item[2].model_dump(mode="json") for item in attempted]
    verification_results.extend(item.verification.model_dump(mode="json") for item in compensations)
    updated_state = state.model_copy(update={
        "execution_results": execution_results,
        "verification_results": verification_results,
        "autonomy_decision": final_decision,
        "status": final_decision.value,
        "error": failure_reason,
    })
    audit_actions = [
        {"phase": "EXECUTE", "action": action.model_dump(mode="json"),
         "result": result.model_dump(mode="json")}
        for action, result, _ in attempted
    ]
    audit_actions.extend(
        {"phase": "COMPENSATE", "original_action_id": item.original_action_id,
         "action": item.action.model_dump(mode="json"), "result": item.result.model_dump(mode="json")}
        for item in compensations
    )
    audit_verification = [
        {"phase": "EXECUTE", **verification.model_dump(mode="json")}
        for _, _, verification in attempted
    ]
    audit_verification.extend(
        {"phase": "ROLLBACK", "original_action_id": item.original_action_id,
         **item.verification.model_dump(mode="json")}
        for item in compensations
    )
    policy_rule = updated_state.policy_result.matched_policy if updated_state.policy_result else ""
    audit = log_run(
        run_id=updated_state.run_id,
        prompt=updated_state.request,
        evidence_ids=sorted(allowed_evidence),
        policy_rule=policy_rule,
        decision=final_decision.value,
        actions=audit_actions,
        verification=audit_verification,
        snapshot={
            "agent_state": updated_state.model_dump(mode="json"),
            "ordered_plan": [step.model_dump(mode="json") for step in ordered],
            "failure_reason": failure_reason,
        },
    )
    return ExecutionOutcome(state=updated_state, audit=audit, compensations=compensations)


async def _verify_compensation(action: ActionContract) -> VerificationResult:
    """Verify the inverse operation through an independent connector read-back."""
    try:
        if action.action_type not in {"cancel_ticket", "unassign_technician"}:
            return VerificationResult(action_id=action.id, status="FAILED", verified=False,
                                      details=f"No rollback verifier for {action.action_type}.")
        ticket = await get_connector().get_ticket(action.arguments["ticket_id"])
        if action.action_type == "cancel_ticket":
            ok = ticket is not None and ticket.status == "CANCELLED"
            detail = "Ticket cancellation persisted." if ok else "Ticket is not cancelled."
        else:
            ok = ticket is not None and ticket.assignee_id is None
            detail = "Technician unassignment persisted." if ok else "Technician assignment is not cleared."
    except Exception as exc:
        return VerificationResult(action_id=action.id, status="FAILED", verified=False,
                                  details=f"Could not verify rollback: {exc}")
    return VerificationResult(action_id=action.id, status="VERIFIED" if ok else "FAILED",
                              verified=ok, details=detail)


def _amount(action: ActionContract) -> float:
    raw = action.arguments.get("amount", action.arguments.get("cost", 0))
    try:
        return float(str(raw).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return 0.0
