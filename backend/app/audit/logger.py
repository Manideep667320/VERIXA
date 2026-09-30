"""Append-only, hash-linked run audit records in SQLite."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from app.core.database import get_db

GENESIS_HASH = "0" * 64


class RunAuditRecord(BaseModel):
    run_id: str
    prompt: str
    evidence_ids: list[str]
    policy_rule: str
    decision: str
    actions: list[dict[str, Any]]
    verification: list[dict[str, Any]]
    timestamp: str
    sequence: int
    snapshot: dict[str, Any]
    prev_hash: str
    row_hash: str


def _json_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"Cannot serialize audit value of type {type(value).__name__}")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_json_value)


def _parse_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _ensure_audit_schema() -> None:
    """Create current tables and backfill legacy Phase 4 rows exactly once."""
    with get_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS run_audit (
                run_id TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                evidence_ids TEXT NOT NULL,
                policy_rule TEXT NOT NULL,
                decision TEXT NOT NULL,
                actions TEXT NOT NULL,
                verification TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sequence INTEGER,
                snapshot TEXT,
                prev_hash TEXT,
                row_hash TEXT
            )"""
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(run_audit)")}
        migrations = {
            "sequence": "INTEGER",
            "snapshot": "TEXT",
            "prev_hash": "TEXT",
            "row_hash": "TEXT",
        }
        for name, sql_type in migrations.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE run_audit ADD COLUMN {name} {sql_type}")

        conn.execute(
            """CREATE TABLE IF NOT EXISTS audit_chain_head (
                singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                row_count INTEGER NOT NULL,
                last_sequence INTEGER NOT NULL,
                last_hash TEXT NOT NULL,
                last_run_id TEXT
            )"""
        )
        head = conn.execute("SELECT * FROM audit_chain_head WHERE singleton = 1").fetchone()
        if head is None:
            legacy_rows = conn.execute("SELECT * FROM run_audit ORDER BY rowid").fetchall()
            previous_hash = GENESIS_HASH
            for sequence, row in enumerate(legacy_rows, start=1):
                snapshot = _legacy_snapshot(conn, row)
                payload = _row_payload(
                    sequence=sequence,
                    run_id=row["run_id"],
                    prompt=row["prompt"],
                    evidence_ids=_parse_json(row["evidence_ids"], []),
                    policy_rule=row["policy_rule"],
                    decision=row["decision"],
                    actions=_parse_json(row["actions"], []),
                    verification=_parse_json(row["verification"], []),
                    timestamp=row["timestamp"],
                    snapshot=snapshot,
                    prev_hash=previous_hash,
                )
                row_hash = _hash_payload(payload)
                conn.execute(
                    """UPDATE run_audit SET sequence = ?, snapshot = ?, prev_hash = ?, row_hash = ?
                       WHERE run_id = ?""",
                    (sequence, _canonical_json(snapshot), previous_hash, row_hash, row["run_id"]),
                )
                previous_hash = row_hash
            conn.execute(
                "INSERT INTO audit_chain_head(singleton, row_count, last_sequence, last_hash, last_run_id) "
                "VALUES (1, ?, ?, ?, ?)",
                (len(legacy_rows), len(legacy_rows), previous_hash,
                 legacy_rows[-1]["run_id"] if legacy_rows else None),
            )


def _legacy_snapshot(conn, row) -> dict[str, Any]:
    evidence = _parse_json(row["evidence_ids"], [])
    actions = _parse_json(row["actions"], [])
    verification = _parse_json(row["verification"], [])
    snapshot: dict[str, Any] = {
        "prompt": row["prompt"],
        "evidence_items": evidence,
        "agent_outputs": {
            "policy_rule": row["policy_rule"],
            "decision": row["decision"],
            "actions": actions,
            "verification": verification,
        },
    }
    has_runs_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'runs'"
    ).fetchone()
    if has_runs_table:
        run = conn.execute("SELECT * FROM runs WHERE id = ?", (row["run_id"],)).fetchone()
        if run:
            snapshot["evidence_items"] = _parse_json(run["evidence"], evidence)
            snapshot["agent_outputs"] = {
                **snapshot["agent_outputs"],
                **{key: _parse_json(run[key], run[key]) if key in run.keys() else None for key in (
                    "intent", "entities", "reasoning", "proposed_actions", "policy_result",
                    "autonomy_decision", "execution_results", "verification_results",
                )},
            }
    return snapshot


def _row_payload(
    *, sequence: int, run_id: str, prompt: str, evidence_ids: list,
    policy_rule: str, decision: str, actions: list, verification: list,
    timestamp: str, snapshot: dict, prev_hash: str,
) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "run_id": run_id,
        "prompt": prompt,
        "evidence_ids": evidence_ids,
        "policy_rule": policy_rule,
        "decision": decision,
        "actions": actions,
        "verification": verification,
        "timestamp": timestamp,
        "snapshot": snapshot,
        "prev_hash": prev_hash,
    }


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _record_from_row(row) -> RunAuditRecord:
    return RunAuditRecord(
        run_id=row["run_id"],
        prompt=row["prompt"],
        evidence_ids=_parse_json(row["evidence_ids"], []),
        policy_rule=row["policy_rule"],
        decision=row["decision"],
        actions=_parse_json(row["actions"], []),
        verification=_parse_json(row["verification"], []),
        timestamp=row["timestamp"],
        sequence=row["sequence"],
        snapshot=_parse_json(row["snapshot"], {}),
        prev_hash=row["prev_hash"],
        row_hash=row["row_hash"],
    )


def _payload_from_row(row) -> dict[str, Any]:
    return _row_payload(
        sequence=row["sequence"],
        run_id=row["run_id"],
        prompt=row["prompt"],
        evidence_ids=_parse_json(row["evidence_ids"], []),
        policy_rule=row["policy_rule"],
        decision=row["decision"],
        actions=_parse_json(row["actions"], []),
        verification=_parse_json(row["verification"], []),
        timestamp=row["timestamp"],
        snapshot=_parse_json(row["snapshot"], {}),
        prev_hash=row["prev_hash"],
    )


def log_run(
    *, run_id: str, prompt: str, evidence_ids: list[str], policy_rule: str,
    decision: str, actions: list[Any], verification: list[Any],
    timestamp: datetime | None = None, snapshot: dict[str, Any] | None = None,
) -> RunAuditRecord:
    """Append one hashed audit row. Existing audit rows have no update/delete API."""
    _ensure_audit_schema()
    action_values = [item.model_dump(mode="json") if isinstance(item, BaseModel) else item for item in actions]
    verification_values = [item.model_dump(mode="json") if isinstance(item, BaseModel) else item for item in verification]
    recorded_at = (timestamp or datetime.now(timezone.utc)).isoformat()
    with get_db() as conn:
        head = conn.execute("SELECT * FROM audit_chain_head WHERE singleton = 1").fetchone()
        sequence = head["last_sequence"] + 1
        previous_hash = head["last_hash"]
        if snapshot is None:
            snapshot = _legacy_snapshot(
                conn,
                {
                    "run_id": run_id,
                    "prompt": prompt,
                    "evidence_ids": _canonical_json(evidence_ids),
                    "policy_rule": policy_rule,
                    "decision": decision,
                    "actions": _canonical_json(action_values),
                    "verification": _canonical_json(verification_values),
                    "timestamp": recorded_at,
                },
            )
        payload = _row_payload(
            sequence=sequence, run_id=run_id, prompt=prompt, evidence_ids=evidence_ids,
            policy_rule=policy_rule, decision=decision, actions=action_values,
            verification=verification_values, timestamp=recorded_at,
            snapshot=snapshot, prev_hash=previous_hash,
        )
        row_hash = _hash_payload(payload)
        conn.execute(
            """INSERT INTO run_audit
               (run_id, prompt, evidence_ids, policy_rule, decision, actions, verification,
                timestamp, sequence, snapshot, prev_hash, row_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, prompt, _canonical_json(evidence_ids), policy_rule, decision,
             _canonical_json(action_values), _canonical_json(verification_values),
             recorded_at, sequence, _canonical_json(snapshot), previous_hash, row_hash),
        )
        conn.execute(
            "UPDATE audit_chain_head SET row_count = ?, last_sequence = ?, last_hash = ?, last_run_id = ? "
            "WHERE singleton = 1",
            (head["row_count"] + 1, sequence, row_hash, run_id),
        )
    return RunAuditRecord(**payload, row_hash=row_hash)


def get_run_audits() -> list[RunAuditRecord]:
    """Read the immutable audit chain in append order."""
    _ensure_audit_schema()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM run_audit ORDER BY sequence").fetchall()
    return [_record_from_row(row) for row in rows]


def get_run_audit(run_id: str) -> RunAuditRecord | None:
    """Read one immutable run record."""
    _ensure_audit_schema()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM run_audit WHERE run_id = ?", (run_id,)).fetchone()
    return _record_from_row(row) if row else None
