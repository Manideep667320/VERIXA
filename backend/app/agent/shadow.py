"""Persist workflow recommendations and provide a tool-free shadow mode."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.agent.graph import Retriever, run_agent
from app.core.database import DB_PATH, get_db
from app.core.constants import AutonomyDecision
from app.llm.provider import LLMProvider
from app.models.schemas import AgentState


class RunMode(StrEnum):
    SHADOW = "shadow"
    SUPERVISED = "supervised"
    AUTONOMOUS = "autonomous"


class ShadowRunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    request: str
    mode: RunMode
    human_decision: str | None = None
    human_action: str | None = None
    recommended_decision: str
    recommended_actions: list[dict] = Field(default_factory=list)
    state_snapshot: dict
    created_at: str


class ShadowMismatch(BaseModel):
    run_id: str
    request: str
    human_decision: str
    recommended_decision: str
    human_action: str | None = None
    recommended_actions: list[dict] = Field(default_factory=list)


class ShadowReport(BaseModel):
    total_cases: int
    matched_cases: int
    match_rate: float
    mismatches: list[ShadowMismatch]
    escalation_rate: float
    estimated_hours_saved: float


def ensure_shadow_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS shadow_runs (
            run_id TEXT PRIMARY KEY, request TEXT NOT NULL, mode TEXT NOT NULL,
            human_decision TEXT, human_action TEXT, recommended_decision TEXT NOT NULL,
            recommended_actions TEXT NOT NULL, state_snapshot TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")


def normalize_decision(value: str) -> str:
    normalized = "_".join(value.strip().upper().replace("-", " ").split())
    aliases = {"APPROVAL": "APPROVAL_REQUIRED", "APPROVE": "APPROVAL_REQUIRED",
               "APPROVAL_REQUIRED": "APPROVAL_REQUIRED", "AUTOMATIC": "EXECUTE",
               "EXECUTED": "EXECUTE", "HUMAN": "ESCALATE"}
    return aliases.get(normalized, normalized)


def persist_shadow_run(
    state: AgentState,
    mode: RunMode,
    *,
    human_decision: str | None = None,
    human_action: str | None = None,
) -> ShadowRunRecord:
    ensure_shadow_table()
    created_at = datetime.now(timezone.utc).isoformat()
    snapshot = state.model_dump(mode="json")
    actions = [action.model_dump(mode="json") for action in state.proposed_actions]
    record = ShadowRunRecord(
        run_id=state.run_id, request=state.request, mode=mode,
        human_decision=human_decision, human_action=human_action,
        recommended_decision=state.autonomy_decision.value,
        recommended_actions=actions, state_snapshot=snapshot, created_at=created_at,
    )
    with get_db() as conn:
        conn.execute(
            """INSERT INTO shadow_runs
            (run_id, request, mode, human_decision, human_action, recommended_decision,
             recommended_actions, state_snapshot, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.run_id, record.request, record.mode.value, record.human_decision,
             record.human_action, record.recommended_decision,
             json.dumps(record.recommended_actions, ensure_ascii=False),
             json.dumps(record.state_snapshot, ensure_ascii=False), record.created_at),
        )
    return record


async def run_workflow(
    request: str,
    *,
    mode: RunMode = RunMode.SHADOW,
    llm: LLMProvider | None = None,
    retriever: Retriever | None = None,
    human_decision: str | None = None,
    human_action: str | None = None,
) -> AgentState:
    """Run the complete agent graph, persist its recommendation, and gate execution by mode."""
    state = await run_agent(request, llm=llm, retriever=retriever)
    stage_statuses = dict(state.stage_statuses)
    # Shadow mode intentionally stops here: it never imports or calls a tool handler.
    if mode == RunMode.AUTONOMOUS and state.autonomy_decision == AutonomyDecision.EXECUTE:
        from app.tools.registry import execute_action
        import app.tools  # noqa: F401 — registers tool handlers
        results = [await execute_action(action) for action in state.proposed_actions]
        execution_failed = any(not result.success for result in results)
        stage_statuses["executing_actions"] = "failed" if execution_failed else "complete"
        stage_statuses["verifying_outcome"] = "skipped"
        state = state.model_copy(update={
            "execution_results": results,
            "workflow_mode": mode.value,
            "stage_statuses": stage_statuses,
            "failed_stage": "executing_actions" if execution_failed else state.failed_stage,
        })
    else:
        stage_statuses["executing_actions"] = "skipped"
        stage_statuses["verifying_outcome"] = "skipped"
        state = state.model_copy(update={
            "workflow_mode": mode.value,
            "stage_statuses": stage_statuses,
        })
    persist_shadow_run(state, mode, human_decision=human_decision, human_action=human_action)
    return state


def build_shadow_report(*, minutes_per_case: float = 15.0) -> ShadowReport:
    ensure_shadow_table()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM shadow_runs WHERE mode = 'shadow' ORDER BY created_at, rowid"
        ).fetchall()
    evaluated = [row for row in rows if row["human_decision"] is not None]
    mismatches: list[ShadowMismatch] = []
    matched = 0
    for row in evaluated:
        recommended = row["recommended_decision"]
        if normalize_decision(row["human_decision"]) == normalize_decision(recommended):
            matched += 1
        else:
            mismatches.append(ShadowMismatch(
                run_id=row["run_id"], request=row["request"],
                human_decision=row["human_decision"], recommended_decision=recommended,
                human_action=row["human_action"],
                recommended_actions=json.loads(row["recommended_actions"]),
            ))
    total = len(evaluated)
    all_count = len(rows)
    escalations = sum(row["recommended_decision"] == AutonomyDecision.ESCALATE.value for row in rows)
    return ShadowReport(
        total_cases=total,
        matched_cases=matched,
        match_rate=(matched / total if total else 0.0),
        mismatches=mismatches,
        escalation_rate=(escalations / all_count if all_count else 0.0),
        estimated_hours_saved=matched * minutes_per_case / 60.0,
    )


async def import_history_csv(
    csv_path: str | Path,
    *,
    llm: LLMProvider | None = None,
    retriever: Retriever | None = None,
) -> list[AgentState]:
    """Run each CSV request through shadow mode and retain the human comparison fields."""
    import csv

    states: list[AgentState] = []
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"request", "human_decision", "human_action"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("CSV must include request, human_decision, and human_action columns")
        for line, row in enumerate(reader, start=2):
            request = (row.get("request") or "").strip()
            if not request:
                raise ValueError(f"CSV row {line} has an empty request")
            states.append(await run_workflow(
                request, mode=RunMode.SHADOW, llm=llm, retriever=retriever,
                human_decision=(row.get("human_decision") or "").strip() or None,
                human_action=(row.get("human_action") or "").strip() or None,
            ))
    return states
