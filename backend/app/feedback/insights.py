"""Human-reviewable feedback metrics and policy-change suggestions."""
from __future__ import annotations

import hashlib
from collections import Counter, defaultdict

from pydantic import BaseModel, ConfigDict, Field

from app.feedback.store import FeedbackRecord, KnowledgeGap, list_feedback, list_knowledge_gaps
from app.policy.loader import load_active_rules


class SopOverrideRate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sop_id: str
    decisions: int = Field(ge=0)
    overrides: int = Field(ge=0)
    override_rate: float = Field(ge=0.0, le=1.0)


class PolicyChangeSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    policy_version: int
    policy_field: str
    current_value: float
    suggested_value: float
    reason_code: str
    sop_ids: list[str]
    rationale: str
    status: str = "PENDING_HUMAN_REVIEW"


class InsightsReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: int
    sop_override_rates: list[SopOverrideRate] = Field(default_factory=list)
    knowledge_gaps: list[KnowledgeGap] = Field(default_factory=list)
    suggested_policy_changes: list[PolicyChangeSuggestion] = Field(default_factory=list)


_SUGGESTIONS: dict[str, tuple[str, float, str]] = {
    "APPROVAL_THRESHOLD_TOO_HIGH": (
        "approval_amount_threshold", -0.10,
        "Human overrides report that the approval amount threshold is too high.",
    ),
    "APPROVAL_THRESHOLD_TOO_LOW": (
        "approval_amount_threshold", 0.10,
        "Human overrides report that the approval amount threshold is too low.",
    ),
    "CONFIDENCE_THRESHOLD_TOO_LOW": (
        "confidence_threshold", 0.05,
        "Human overrides report that the confidence threshold is too low.",
    ),
    "CONFIDENCE_THRESHOLD_TOO_HIGH": (
        "confidence_threshold", -0.05,
        "Human overrides report that the confidence threshold is too high.",
    ),
}


def build_insights(*, limit: int = 1000) -> InsightsReport:
    """Summarize stored human feedback; suggestions are data only and never activate policy."""
    rules = load_active_rules()
    feedback = list_feedback(limit=limit)
    totals: Counter[str] = Counter()
    overrides: Counter[str] = Counter()

    for event in feedback:
        sop_ids = _sop_ids(event.evidence_ids)
        for sop_id in sop_ids:
            totals[sop_id] += 1
            if event.event_type == "override":
                overrides[sop_id] += 1

    rates = [
        SopOverrideRate(sop_id=sop_id, decisions=totals[sop_id], overrides=overrides[sop_id],
                        override_rate=round(overrides[sop_id] / totals[sop_id], 4))
        for sop_id in sorted(totals)
    ]
    suggestions = _policy_suggestions(feedback, rules.version,
                                      rules.approval_amount_threshold, rules.confidence_threshold)
    return InsightsReport(policy_version=rules.version, sop_override_rates=rates,
                          knowledge_gaps=list_knowledge_gaps(limit=limit),
                          suggested_policy_changes=suggestions)


def _sop_ids(evidence_ids: list[str]) -> list[str]:
    return sorted({evidence_id.split("::", 1)[0] for evidence_id in evidence_ids
                   if evidence_id.startswith("SOP-")})


def _policy_suggestions(
    feedback: list[FeedbackRecord], policy_version: int,
    amount_threshold: float, confidence_threshold: float,
) -> list[PolicyChangeSuggestion]:
    by_reason: dict[str, set[str]] = defaultdict(set)
    for event in feedback:
        if event.event_type == "override" and event.reason_code in _SUGGESTIONS:
            by_reason[event.reason_code].update(_sop_ids(event.evidence_ids))

    suggestions = []
    for reason_code, sop_ids in sorted(by_reason.items()):
        field, delta, rationale = _SUGGESTIONS[reason_code]
        current = amount_threshold if field == "approval_amount_threshold" else confidence_threshold
        if field == "approval_amount_threshold":
            recommended = max(0.0, current * (1 + delta))
        else:
            recommended = min(1.0, max(0.0, current + delta))
        identity = f"{reason_code}:{','.join(sorted(sop_ids))}:{policy_version}"
        suggestions.append(PolicyChangeSuggestion(
            id="SUG-" + hashlib.sha256(identity.encode()).hexdigest()[:12],
            policy_version=policy_version, policy_field=field, current_value=current,
            suggested_value=round(recommended, 4), reason_code=reason_code,
            sop_ids=sorted(sop_ids),
            rationale=(rationale + " This proposal requires human review and is not applied."),
        ))
    return suggestions
