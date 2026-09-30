"""Append-only storage for human approval, rejection, override, and evidence-gap feedback."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core import database
from app.core.database import get_db


class FeedbackEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    event_type: Literal["approval", "rejection", "override"]
    reason_code: str = Field(min_length=2, max_length=80)
    prompt: str = ""
    decision: str = ""
    actor: str = "human"
    evidence_ids: list[str] = Field(default_factory=list)
    policy_version: int | None = Field(default=None, ge=1)

    @field_validator("reason_code", "actor")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be blank")
        return value


class FeedbackRecord(FeedbackEvent):
    id: str
    created_at: datetime


class KnowledgeGap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    run_id: str
    query: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)
    reason: Literal["NO_EVIDENCE", "BELOW_CONFIDENCE_THRESHOLD"]
    detected_at: datetime


def _ensure_schema() -> None:
    database.init_db()
    with sqlite3.connect(str(database.DB_PATH)) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS feedback_events (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            event_type TEXT NOT NULL CHECK(event_type IN ('approval', 'rejection', 'override')),
            reason_code TEXT NOT NULL,
            prompt TEXT NOT NULL,
            decision TEXT NOT NULL,
            actor TEXT NOT NULL,
            evidence_ids TEXT NOT NULL,
            policy_version INTEGER,
            created_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS knowledge_gaps (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            query TEXT NOT NULL,
            confidence REAL NOT NULL,
            evidence_ids TEXT NOT NULL,
            reason TEXT NOT NULL CHECK(reason IN ('NO_EVIDENCE', 'BELOW_CONFIDENCE_THRESHOLD')),
            detected_at TEXT NOT NULL
        )""")


def record_feedback(event: FeedbackEvent) -> FeedbackRecord:
    """Append a human decision with its reason code and evidence provenance."""
    _ensure_schema()
    record_id = f"FDB-{uuid4().hex}"
    created_at = datetime.now(timezone.utc)
    with get_db() as conn:
        conn.execute(
            """INSERT INTO feedback_events
               (id, run_id, event_type, reason_code, prompt, decision, actor, evidence_ids, policy_version, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record_id, event.run_id, event.event_type, event.reason_code, event.prompt,
             event.decision, event.actor, json.dumps(event.evidence_ids), event.policy_version,
             created_at.isoformat()),
        )
    return FeedbackRecord(**event.model_dump(), id=record_id, created_at=created_at)


def list_feedback(*, limit: int = 1000) -> list[FeedbackRecord]:
    """Read newest feedback events without exposing any mutation operation."""
    _ensure_schema()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM feedback_events ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_feedback_from_row(row) for row in rows]


def record_knowledge_gap(
    *, run_id: str, query: str, confidence: float, evidence_ids: list[str],
) -> KnowledgeGap:
    """Append a run where retrieval found no usable evidence for the request."""
    _ensure_schema()
    reason: Literal["NO_EVIDENCE", "BELOW_CONFIDENCE_THRESHOLD"] = (
        "NO_EVIDENCE" if not evidence_ids else "BELOW_CONFIDENCE_THRESHOLD"
    )
    gap_id = f"GAP-{uuid4().hex}"
    detected_at = datetime.now(timezone.utc)
    with get_db() as conn:
        conn.execute(
            """INSERT INTO knowledge_gaps (id, run_id, query, confidence, evidence_ids, reason, detected_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (gap_id, run_id, query, confidence, json.dumps(evidence_ids), reason, detected_at.isoformat()),
        )
    return KnowledgeGap(id=gap_id, run_id=run_id, query=query, confidence=confidence,
                        evidence_ids=evidence_ids, reason=reason, detected_at=detected_at)


def list_knowledge_gaps(*, limit: int = 1000) -> list[KnowledgeGap]:
    _ensure_schema()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM knowledge_gaps ORDER BY detected_at DESC, rowid DESC LIMIT ?", (limit,)
        ).fetchall()
    return [KnowledgeGap(id=row["id"], run_id=row["run_id"], query=row["query"],
                         confidence=row["confidence"], evidence_ids=json.loads(row["evidence_ids"]),
                         reason=row["reason"], detected_at=row["detected_at"]) for row in rows]


def _feedback_from_row(row: sqlite3.Row) -> FeedbackRecord:
    return FeedbackRecord(
        id=row["id"], run_id=row["run_id"], event_type=row["event_type"], reason_code=row["reason_code"],
        prompt=row["prompt"], decision=row["decision"], actor=row["actor"],
        evidence_ids=json.loads(row["evidence_ids"]), policy_version=row["policy_version"],
        created_at=row["created_at"],
    )
