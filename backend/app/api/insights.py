"""Read-only human insights and explicit policy-override feedback capture."""
from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field

from app.feedback.insights import InsightsReport, build_insights
from app.feedback.store import FeedbackEvent, FeedbackRecord, record_feedback

router = APIRouter(prefix="/insights", tags=["insights"])


class OverrideSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=2, max_length=80)
    prompt: str = ""
    decision: str = "OVERRIDDEN"
    actor: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    policy_version: int | None = Field(default=None, ge=1)


@router.get("", response_model=InsightsReport)
async def get_insights() -> InsightsReport:
    """Return override rates, knowledge gaps, and suggestions awaiting human review."""
    return build_insights()


@router.post("/feedback/override", response_model=FeedbackRecord, status_code=status.HTTP_201_CREATED)
async def capture_override(submission: OverrideSubmission) -> FeedbackRecord:
    """Record a human override and reason code; this endpoint never edits active policy."""
    return record_feedback(FeedbackEvent(
        run_id=submission.run_id, event_type="override", reason_code=submission.reason_code,
        prompt=submission.prompt, decision=submission.decision, actor=submission.actor,
        evidence_ids=submission.evidence_ids, policy_version=submission.policy_version,
    ))
