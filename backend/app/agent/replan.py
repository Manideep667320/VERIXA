"""Typed, single-attempt replanning for failed ordered action plans."""
from __future__ import annotations

import json
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.llm.provider import LLMProvider, get_llm
from app.models.schemas import ActionContract


class ReplanOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    steps: list[ActionContract] = Field(max_length=5)


async def replan_plan(
    *,
    request: str,
    failure_reason: str,
    completed_steps: Sequence[ActionContract],
    remaining_steps: Sequence[ActionContract],
    allowed_evidence_ids: set[str],
    llm: LLMProvider | None = None,
) -> list[ActionContract]:
    """Ask the model for one revised ordered plan; policy authorization stays in executor."""
    prompt = (
        "Revise the remaining ordered action plan after a failed step. Keep the plan minimal, "
        "use only supported action types and cite only allowed evidence IDs. Do not make policy "
        "decisions or claim approval. Return JSON with a steps array matching the supplied schema.\n"
        f"REQUEST:\n{request}\nFAILURE:\n{failure_reason}\n"
        f"COMPLETED STEPS:\n{json.dumps([item.model_dump(mode='json') for item in completed_steps])}\n"
        f"REMAINING STEPS:\n{json.dumps([item.model_dump(mode='json') for item in remaining_steps])}\n"
        f"ALLOWED EVIDENCE IDS:\n{json.dumps(sorted(allowed_evidence_ids))}"
    )
    output = await (llm or get_llm()).structured_model(prompt, ReplanOutput)
    if len(output.steps) > 5:
        raise ValueError("Replanned action plan cannot exceed five steps")
    invalid = {evidence_id for step in output.steps for evidence_id in step.evidence_ids} - allowed_evidence_ids
    if invalid:
        raise ValueError(f"Replan cited evidence IDs not retrieved: {', '.join(sorted(invalid))}")
    return output.steps
