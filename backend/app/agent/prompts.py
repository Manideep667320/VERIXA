"""Versioned prompts and typed-output contracts for the agent's LLM tasks."""
from __future__ import annotations
import json
from pydantic import BaseModel, ConfigDict, Field

SYSTEM_PROMPT = """You are an enterprise service-resolution assistant. Interpret requests,
reason only from supplied evidence, and propose bounded structured actions.
Never invent facts, policies, permissions, or evidence IDs. The application, not you,
will make the final authorization decision."""

class StrictOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

class IntentOutput(StrictOutput):
    request_type: str
    entities: dict[str, object] = Field(default_factory=dict)
    desired_outcome: str
    urgency: str

class ReasoningOutput(StrictOutput):
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    cited_evidence_ids: list[str] = Field(default_factory=list)
    conflicting_evidence: bool = False
    severity: str

class ProposedAction(StrictOutput):
    action_type: str
    arguments: dict[str, object] = Field(default_factory=dict)
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)

class ActionPlanOutput(StrictOutput):
    actions: list[ProposedAction] = Field(default_factory=list)

def intent_extraction_prompt(request: str) -> str:
    return f"""Extract the request type, entities, desired outcome, and urgency from this request.
REQUEST:\n{request}\nUse concise values. Return only JSON matching the supplied schema."""

def reasoning_prompt(request: str, evidence: list[dict[str, str]]) -> str:
    return f"""Reason from retrieved evidence only. Identify gaps or contradictions.
Every cited_evidence_id must exactly match an ID in the evidence list. Confidence is 0 to 1.
REQUEST:\n{request}\nRETRIEVED EVIDENCE:\n{json.dumps(evidence, ensure_ascii=False, indent=2)}
Return only JSON matching the supplied schema."""

def action_planning_prompt(request: str, reasoning: ReasoningOutput, entities: dict,
                           valid_evidence_ids: list[str]) -> str:
    return f"""Propose actions supported by the request and evidence. Cite only IDs in VALID EVIDENCE IDS.
Do not decide authorization; deterministic policy code does that. Supported actions: create_service_ticket,
assign_technician, lookup_customer, send_notification, replace_product, issue_refund.
Put monetary amount in arguments.amount.
REQUEST:\n{request}\nREASONING:\n{reasoning.model_dump_json()}\nENTITIES:\n{json.dumps(entities)}
VALID EVIDENCE IDS:\n{json.dumps(valid_evidence_ids)}\nReturn only JSON matching the supplied schema."""
