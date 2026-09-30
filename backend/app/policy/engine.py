"""Deterministic policy evaluation using the active, versioned YAML rules."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel

from app.core.constants import AutonomyDecision, RiskLevel
from app.models.schemas import ActionContract, EvidenceItem, PolicyResult
from app.policy.loader import PolicyRules, load_active_rules


class VersionedPolicyResult(PolicyResult):
    policy_version: int


class PolicyDecision(BaseModel):
    decision: AutonomyDecision
    policy_version: int
    policy_result: VersionedPolicyResult


def classify_risk(action_type: str, rules: PolicyRules | None = None) -> RiskLevel:
    active = rules or load_active_rules()
    rule = active.actions.get(action_type)
    return rule.risk_level if rule else RiskLevel.UNKNOWN


def evaluate_policy(action: ActionContract, rules: PolicyRules | None = None) -> VersionedPolicyResult:
    """Evaluate one action against a specific rules snapshot."""
    active = rules or load_active_rules()
    rule = active.actions.get(action.action_type)
    if rule is None:
        return VersionedPolicyResult(
            allowed=False,
            risk_level=RiskLevel.UNKNOWN,
            reason=f"No policy defined for action type: {action.action_type}",
            policy_version=active.version,
        )
    if not rule.allowed:
        return VersionedPolicyResult(
            allowed=False,
            risk_level=rule.risk_level,
            reason=f"Action '{action.action_type}' is explicitly disallowed by policy.",
            matched_policy=action.action_type,
            policy_version=active.version,
        )

    requires_approval = rule.requires_approval
    if (rule.requires_approval_above is not None
            and _action_amount(action) > rule.requires_approval_above):
        requires_approval = True
    return VersionedPolicyResult(
        allowed=True,
        requires_approval=requires_approval,
        risk_level=rule.risk_level,
        reason="Policy permits this action." + (" Approval required." if requires_approval else ""),
        matched_policy=action.action_type,
        policy_version=active.version,
    )


def combine_policy_results(
    results: list[VersionedPolicyResult], rules: PolicyRules | None = None,
) -> VersionedPolicyResult:
    """Combine action-level rules into one fail-closed run-level policy result."""
    active = rules or load_active_rules()
    if not results:
        return VersionedPolicyResult(allowed=False, reason="No actions were proposed.", policy_version=active.version)
    highest_risk = max(results, key=lambda result: active.risk_levels[result.risk_level]).risk_level
    return VersionedPolicyResult(
        allowed=all(result.allowed for result in results),
        requires_approval=any(result.requires_approval for result in results),
        risk_level=highest_risk,
        reason=" ".join(result.reason for result in results),
        matched_policy=", ".join(result.matched_policy for result in results if result.matched_policy),
        policy_version=active.version,
    )


def decide_autonomy(
    policy_result: PolicyResult,
    evidence_confidence: float,
    *,
    has_evidence: bool = True,
    conflicting_evidence: bool = False,
    evidence: Sequence[EvidenceItem] | None = None,
    amount: float = 0,
    rules: PolicyRules | None = None,
) -> AutonomyDecision:
    """Apply confidence/evidence gates, then configured risk and amount approval rules."""
    active = rules or load_active_rules()
    retrieval_conflict = bool(evidence) and any(
        item.metadata.get("conflict_warning", False) for item in evidence
    )
    if (evidence_confidence < active.confidence_threshold
            or not has_evidence or conflicting_evidence or retrieval_conflict):
        return AutonomyDecision.ESCALATE
    if not policy_result.allowed:
        return AutonomyDecision.ESCALATE
    if (amount > active.approval_amount_threshold
            or policy_result.requires_approval
            or policy_result.risk_level in active.approval_risk_levels):
        return AutonomyDecision.APPROVAL_REQUIRED
    return AutonomyDecision.EXECUTE


def evaluate_actions(
    actions: list[ActionContract],
    evidence_confidence: float,
    *,
    has_evidence: bool,
    conflicting_evidence: bool = False,
    amount: float | None = None,
    rules: PolicyRules | None = None,
) -> PolicyDecision:
    """Return a policy decision and the exact version used to produce it."""
    active = rules or load_active_rules()
    results = [evaluate_policy(action, active) for action in actions]
    policy_result = combine_policy_results(results, active)
    total_amount = max(
        [amount or 0.0, *(_action_amount(action) for action in actions)],
        default=0.0,
    )
    return PolicyDecision(
        decision=decide_autonomy(
            policy_result,
            evidence_confidence,
            has_evidence=has_evidence,
            conflicting_evidence=conflicting_evidence,
            amount=total_amount,
            rules=active,
        ),
        policy_version=active.version,
        policy_result=policy_result,
    )


def _action_amount(action: ActionContract) -> float:
    value = action.arguments.get("amount", action.arguments.get("cost", 0))
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return 0.0
