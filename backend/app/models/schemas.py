"""All Pydantic models — consolidated single source of truth for data shapes."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.constants import (
    ActionStatus,
    ApprovalStatus,
    AutonomyDecision,
    DocumentType,
    RiskLevel,
    Severity,
)


def _uuid() -> str:
    return str(uuid4())[:8].upper()


# ── Evidence ────────────────────────────────────────────────────────────


class EvidenceItem(BaseModel):
    """A single piece of retrieved enterprise evidence."""

    id: str
    source: str
    section: str = ""
    text: str
    relevance_score: float = 0.0
    document_type: DocumentType = DocumentType.SOP
    metadata: dict = Field(default_factory=dict)


# ── Action Contract ─────────────────────────────────────────────────────


class ActionContract(BaseModel):
    """Structured action proposed by the agent, validated by the control layer."""

    id: str = Field(default_factory=lambda: f"ACT-{_uuid()}")
    action_type: str
    arguments: dict = Field(default_factory=dict)
    reason: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    requires_approval: bool = False
    status: ActionStatus = ActionStatus.PENDING


class ActionResult(BaseModel):
    """Result of executing an action through a tool."""

    success: bool
    action_id: str
    data: dict = Field(default_factory=dict)
    error: str | None = None


# ── Policy ──────────────────────────────────────────────────────────────


class PolicyResult(BaseModel):
    """Output of the deterministic policy engine."""

    allowed: bool
    requires_approval: bool = False
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    reason: str = ""
    matched_policy: str = ""


# ── Agent State ─────────────────────────────────────────────────────────


class AgentState(BaseModel):
    """Full state object flowing through the agent graph. Immutable per node transition."""

    run_id: str = Field(default_factory=lambda: f"RUN-{_uuid()}")

    # Input
    request: str = ""
    intent: str = ""
    entities: dict = Field(default_factory=dict)

    # Evidence
    evidence: list[EvidenceItem] = Field(default_factory=list)
    evidence_confidence: float = 0.0

    # Reasoning
    reasoning_summary: str = ""
    severity: Severity = Severity.MEDIUM

    # Actions
    proposed_actions: list[ActionContract] = Field(default_factory=list)

    # Policy / Risk
    policy_result: PolicyResult | None = None
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    autonomy_decision: AutonomyDecision = AutonomyDecision.ESCALATE

    # Execution
    approval_required: bool = False
    approval_id: str | None = None
    execution_results: list[ActionResult] = Field(default_factory=list)
    verification_results: list[dict] = Field(default_factory=list)

    # Output
    final_response: str = ""
    status: str = "PENDING"
    error: str | None = None
    workflow_mode: Literal["shadow", "supervised", "autonomous"] = "shadow"
    failed_stage: str | None = None
    stage_statuses: dict[str, Literal["queued", "complete", "failed", "skipped"]] = Field(
        default_factory=lambda: {
            "understanding_request": "queued",
            "retrieving_evidence": "queued",
            "reasoning": "queued",
            "preparing_action_plan": "queued",
            "evaluating_policy": "queued",
            "executing_actions": "queued",
            "verifying_outcome": "queued",
        }
    )


# ── Approval ────────────────────────────────────────────────────────────


class ApprovalRequest(BaseModel):
    """Approval record persisted in the database."""

    id: str = Field(default_factory=lambda: f"APR-{_uuid()}")
    run_id: str
    action_id: str
    reason: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_by: str | None = None
    decided_at: datetime | None = None


class ApprovalDecision(BaseModel):
    """Input from a human approver."""

    decision: ApprovalStatus
    decided_by: str = "manager"
    comment: str = ""


# ── Audit ───────────────────────────────────────────────────────────────


class AuditEvent(BaseModel):
    """Single event in the audit trail."""

    id: str = Field(default_factory=lambda: f"EVT-{_uuid()}")
    run_id: str
    event_type: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── API Request / Response ──────────────────────────────────────────────


class AgentRunRequest(BaseModel):
    """Incoming user request to the agent."""

    request: str
    user_id: str = "employee-1"


class AgentRunResponse(BaseModel):
    """API response after an agent run."""

    run_id: str
    status: str
    decision: dict = Field(default_factory=dict)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    actions: list[ActionContract] = Field(default_factory=list)
    approval_id: str | None = None
    final_response: str = ""
    audit_events: list[AuditEvent] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
