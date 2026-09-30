"""Workflow mode selection and shadow evaluation reports."""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field

from app.agent.shadow import RunMode, build_shadow_report, run_workflow
from app.models.schemas import AgentState

router = APIRouter(prefix="/shadow", tags=["shadow"])


class ShadowRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request: str = Field(min_length=1)
    mode: RunMode = RunMode.SHADOW


@router.post("/run", response_model=AgentState)
async def run_shadow_workflow(body: ShadowRunRequest):
    return await run_workflow(body.request, mode=body.mode)


@router.get("/report")
async def shadow_report(minutes_per_case: float = Query(default=15.0, ge=0, le=1440)):
    return build_shadow_report(minutes_per_case=minutes_per_case).model_dump(mode="json")
