"""Policy engine — deterministic rules, risk classification, and permission checks.

The LLM proposes actions. This module makes the authorization decision.
"""

from app.core.constants import AutonomyDecision, RiskLevel
from app.models.schemas import ActionContract, PolicyResult

# ── Policy rules — deterministic, config-driven ─────────────────────────

POLICIES: dict[str, dict] = {
    "create_service_ticket": {
        "allowed": True,
        "max_risk": RiskLevel.HIGH,
        "requires_approval": False,
    },
    "assign_technician": {
        "allowed": True,
        "max_risk": RiskLevel.MEDIUM,
        "requires_approval": False,
    },
    "replace_product": {
        "allowed": True,
        "max_risk": RiskLevel.HIGH,
        "requires_approval": True,
    },
    "issue_refund": {
        "allowed": True,
        "requires_approval_above": 50000,
    },
    "send_notification": {
        "allowed": True,
        "max_risk": RiskLevel.MEDIUM,
        "requires_approval": False,
    },
    "lookup_customer": {
        "allowed": True,
        "max_risk": RiskLevel.LOW,
        "requires_approval": False,
    },
}

# ── Risk classification ─────────────────────────────────────────────────

RISK_MAP: dict[str, RiskLevel] = {
    "create_service_ticket": RiskLevel.LOW,
    "assign_technician": RiskLevel.MEDIUM,
    "lookup_customer": RiskLevel.LOW,
    "send_notification": RiskLevel.MEDIUM,
    "replace_product": RiskLevel.HIGH,
    "issue_refund": RiskLevel.HIGH,
}


def classify_risk(action_type: str) -> RiskLevel:
    """Classify the risk level of an action type."""
    return RISK_MAP.get(action_type, RiskLevel.UNKNOWN)


def evaluate_policy(action: ActionContract) -> PolicyResult:
    """Evaluate a proposed action against deterministic policy rules."""
    policy = POLICIES.get(action.action_type)

    if policy is None:
        return PolicyResult(
            allowed=False,
            risk_level=RiskLevel.UNKNOWN,
            reason=f"No policy defined for action type: {action.action_type}",
        )

    if not policy.get("allowed", False):
        return PolicyResult(
            allowed=False,
            risk_level=classify_risk(action.action_type),
            reason=f"Action '{action.action_type}' is explicitly disallowed by policy.",
            matched_policy=action.action_type,
        )

    risk = classify_risk(action.action_type)
    requires_approval = policy.get("requires_approval", False)

    # Check risk threshold
    max_risk = policy.get("max_risk")
    if max_risk and _risk_exceeds(risk, max_risk):
        requires_approval = True

    return PolicyResult(
        allowed=True,
        requires_approval=requires_approval,
        risk_level=risk,
        reason="Policy permits this action." + (" Approval required." if requires_approval else ""),
        matched_policy=action.action_type,
    )


def decide_autonomy(
    policy_result: PolicyResult, evidence_confidence: float
) -> AutonomyDecision:
    """Determine whether to execute, request approval, or escalate."""
    if not policy_result.allowed:
        return AutonomyDecision.ESCALATE

    if evidence_confidence < 0.5:
        return AutonomyDecision.ESCALATE

    if policy_result.requires_approval or policy_result.risk_level == RiskLevel.HIGH:
        return AutonomyDecision.APPROVAL_REQUIRED

    return AutonomyDecision.EXECUTE


_RISK_ORDER = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2, RiskLevel.UNKNOWN: 3}


def _risk_exceeds(actual: RiskLevel, threshold: RiskLevel) -> bool:
    return _RISK_ORDER.get(actual, 3) > _RISK_ORDER.get(threshold, 3)
