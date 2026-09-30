"""Hash-chain integrity, migration, and export tests for run audit records."""

from __future__ import annotations

import csv
import io
import json

import pytest

from app.api.audit import export_audit, verify_audit_chain
from app.audit.logger import get_run_audit, log_run
from app.audit.verify_chain import verify_chain
from app.core import database


@pytest.fixture
def isolated_audit_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "audit-chain.sqlite")
    database.init_db()
    return database.DB_PATH


def _append_three():
    for number in range(1, 4):
        log_run(
            run_id=f"RUN-{number}",
            prompt=f"Prompt {number}",
            evidence_ids=[f"SOP-{number:03}"],
            policy_rule="ticket-policy",
            decision="EXECUTE",
            actions=[{"action_type": "create_service_ticket", "ticket_id": f"TKT-{number}"}],
            verification=[{"status": "VERIFIED"}],
            snapshot={
                "prompt": f"Prompt {number}",
                "evidence_items": [{"id": f"SOP-{number:03}", "text": "evidence"}],
                "agent_outputs": {"intent": "service_request", "actions": [{"id": f"ACT-{number}"}]},
            },
        )


async def test_untouched_chain_and_verify_endpoint_pass(isolated_audit_db):
    _append_three()
    result = verify_chain()
    endpoint = await verify_audit_chain()
    assert result.valid is True
    assert result.first_broken_row_id is None
    assert endpoint["valid"] is True
    assert endpoint["checked_rows"] == 3
    row = get_run_audit("RUN-1")
    assert row.snapshot["evidence_items"][0]["id"] == "SOP-001"
    assert row.snapshot["agent_outputs"]["intent"] == "service_request"
    assert len(row.row_hash) == 64
    assert row.prev_hash == "0" * 64


@pytest.mark.parametrize(
    ("tamper", "expected_broken_id"),
    [("edit", "RUN-2"), ("delete_middle", "RUN-3"),
     ("delete_last", "RUN-3"), ("reorder", "RUN-3")],
)
def test_chain_verifier_reports_first_broken_row(isolated_audit_db, tamper, expected_broken_id):
    _append_three()
    with database.get_db() as conn:
        if tamper == "edit":
            conn.execute("UPDATE run_audit SET decision = 'TAMPERED' WHERE run_id = 'RUN-2'")
        elif tamper == "delete_middle":
            conn.execute("DELETE FROM run_audit WHERE run_id = 'RUN-2'")
        elif tamper == "delete_last":
            conn.execute("DELETE FROM run_audit WHERE run_id = 'RUN-3'")
        else:
            conn.execute("UPDATE run_audit SET sequence = 10 WHERE run_id = 'RUN-1'")
            conn.execute("UPDATE run_audit SET sequence = 1 WHERE run_id = 'RUN-3'")
            conn.execute("UPDATE run_audit SET sequence = 2 WHERE run_id = 'RUN-2'")
    result = verify_chain()
    assert result.valid is False
    assert result.first_broken_row_id == expected_broken_id


def test_legacy_audit_rows_are_migrated_and_chain_verified(isolated_audit_db):
    with database.get_db() as conn:
        conn.execute(
            """CREATE TABLE run_audit (
                run_id TEXT PRIMARY KEY, prompt TEXT NOT NULL, evidence_ids TEXT NOT NULL,
                policy_rule TEXT NOT NULL, decision TEXT NOT NULL, actions TEXT NOT NULL,
                verification TEXT NOT NULL, timestamp TEXT NOT NULL
            )"""
        )
        conn.execute(
            "INSERT INTO run_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("LEGACY-1", "Legacy prompt", json.dumps(["SOP-042"]), "legacy-rule", "EXECUTE",
             json.dumps([{"action_type": "create_service_ticket"}]),
             json.dumps([{"status": "VERIFIED"}]), "2026-01-01T00:00:00+00:00"),
        )
    result = verify_chain()
    migrated = get_run_audit("LEGACY-1")
    assert result.valid is True
    assert migrated.sequence == 1
    assert migrated.snapshot["prompt"] == "Legacy prompt"
    assert migrated.snapshot["evidence_items"] == ["SOP-042"]
    assert migrated.prev_hash == "0" * 64


async def test_export_supports_json_and_csv(isolated_audit_db):
    log_run(run_id="RUN-EXPORT", prompt="Export me", evidence_ids=[], policy_rule="", decision="EXECUTE",
            actions=[], verification=[], snapshot={"prompt": "Export me", "evidence_items": [], "agent_outputs": {}})
    json_response = await export_audit("json")
    csv_response = await export_audit("csv")
    assert json.loads(json_response.body)[0]["run_id"] == "RUN-EXPORT"
    exported = next(csv.DictReader(io.StringIO(csv_response.body.decode())))
    assert exported["run_id"] == "RUN-EXPORT"
    assert exported["row_hash"]
