"""Policy version management and offline decision simulation endpoints."""

from __future__ import annotations

from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.policy.loader import list_policy_versions, load_active_rules, save_new_policy_version
from app.policy.simulator import simulate_policy

router = APIRouter(prefix="/policy", tags=["policy"])


class PolicyWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_rules: str | dict[str, Any] | None = None
    rules: str | dict[str, Any] | None = None

    @model_validator(mode="after")
    def require_one_candidate(self):
        if (self.candidate_rules is None) == (self.rules is None):
            raise ValueError("Provide exactly one of candidate_rules or rules")
        return self

    @property
    def value(self) -> str | dict[str, Any]:
        return self.candidate_rules if self.candidate_rules is not None else self.rules


class PolicySimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_rules: str | dict[str, Any]
    last_n: int = Field(default=100, ge=1, le=1000)


def _invalid_policy_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=422, detail=f"Invalid policy rules: {exc}")


@router.post("")
async def create_policy_version(request: PolicyWriteRequest):
    """Validate policy input and save it as a new immutable version."""
    try:
        saved = save_new_policy_version(request.value)
    except (ValidationError, ValueError, yaml.YAMLError) as exc:
        raise _invalid_policy_error(exc) from exc
    return {
        "version": saved.version,
        "active": True,
        "confidence_threshold": saved.confidence_threshold,
        "approval_amount_threshold": saved.approval_amount_threshold,
    }


@router.get("/versions")
async def get_policy_versions():
    return {
        "active_version": load_active_rules().version,
        "versions": [item.model_dump(mode="json") for item in list_policy_versions()],
    }


@router.post("/simulate")
async def run_policy_simulation(request: PolicySimulationRequest):
    try:
        return simulate_policy(request.candidate_rules, request.last_n).model_dump(mode="json")
    except (ValidationError, ValueError, yaml.YAMLError) as exc:
        raise _invalid_policy_error(exc) from exc
