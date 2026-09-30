"""Offline policy replay over persisted runs; this module never calls models or tools."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.schemas import ActionContract
from app.policy.engine import evaluate_actions
from app.policy.loader import PolicyRules, parse_policy_rules


class DecisionChange(BaseModel):
    run_id: str
    old: str
    new: str
    policy_version: int


class PolicySimulationResult(BaseModel):
    policy_version: int
    checked_runs: int
    changed_decisions: list[DecisionChange] = Field(default_factory=list)


def _decode(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _column(row, name: str, default: Any = None) -> Any:
    return row[name] if name in row.keys() else default


def _actions(value: Any) -> list[ActionContract]:
    parsed = _decode(value, [])
    if isinstance(parsed, dict):
        parsed = [parsed]
    if not isinstance(parsed, list):
        return []
    actions = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        try:
            actions.append(ActionContract.model_validate(item))
        except Exception:
            # Malformed historical action contracts fail closed in the engine as no plan.
            return []
    return actions


def _number(value: Any) -> float:
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def simulate_policy(
    candidate_rules: str | dict[str, Any] | PolicyRules,
    last_n: int = 100,
) -> PolicySimulationResult:
    """Replay the most recent runs using only stored inputs and candidate rules."""
    if last_n < 1:
        raise ValueError("last_n must be at least 1")
    rules = parse_policy_rules(candidate_rules)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY created_at DESC, rowid DESC LIMIT ?", (last_n,)
        ).fetchall()

    changes = []
    for row in rows:
        old = str(_column(row, "autonomy_decision", "") or "")
        if not old:
            continue
        reasoning = _decode(_column(row, "reasoning"), {})
        evidence = _decode(_column(row, "evidence"), [])
        entities = _decode(_column(row, "entities"), {})
        actions = _actions(_column(row, "proposed_actions"))
        confidence = _number(
            _column(row, "evidence_confidence", reasoning.get("confidence", 0.0)
                    if isinstance(reasoning, dict) else 0.0)
        )
        conflicting = bool(
            reasoning.get("conflicting_evidence", reasoning.get("conflicting", False))
            if isinstance(reasoning, dict) else False
        )
        amount = max(
            (_number(entities.get(key)) for key in ("amount", "cost", "estimated_cost", "replacement_cost")),
            default=0.0,
        ) if isinstance(entities, dict) else 0.0
        replayed = evaluate_actions(
            actions,
            confidence,
            has_evidence=bool(evidence),
            conflicting_evidence=conflicting,
            amount=amount,
            rules=rules,
        )
        new = replayed.decision.value
        if new != old:
            changes.append(DecisionChange(run_id=row["id"], old=old, new=new,
                                          policy_version=replayed.policy_version))
    return PolicySimulationResult(policy_version=rules.version, checked_runs=len(rows), changed_decisions=changes)
