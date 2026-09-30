"""Phase 4 tool execution, verification, approval, and audit flows."""

from __future__ import annotations

import json

import pytest
from fastapi import HTTPException

from app.api.approval import approve_action, reject_action
from app.audit.logger import get_run_audit, log_run
from app.core import database
from app.core.constants import ApprovalStatus
from app.models.schemas import ActionContract, ActionResult, ApprovalDecision
from app.tools.registry import execute_action
from app.verification.verifier import verify_action


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "phase4.sqlite")
    database.init_db()
    return database.DB_PATH


def _create_run(run_id: str, action: ActionContract, *, approval_id: str | None = None):
    with database.get_db() as conn:
        conn.execute(
            "INSERT INTO runs(id, request, evidence, policy_result, autonomy_decision) VALUES (?, ?, ?, ?, ?)",
            (run_id, "Customer reports equipment failure", json.dumps(["SOP-042", "POL-EQP-002"]),
             json.dumps({"matched_policy": "create_service_ticket"}),
             "APPROVAL_REQUIRED" if approval_id else "EXECUTE"),
        )
        conn.execute(
            """INSERT INTO actions(id, run_id, action_type, arguments, reason, evidence_ids,
               risk_level, requires_approval, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (action.id, run_id, action.action_type, json.dumps(action.arguments), action.reason,
             json.dumps(action.evidence_ids), action.risk_level.value, int(bool(approval_id)),
             "PENDING" if approval_id else "EXECUTING"),
        )
        if approval_id:
            conn.execute(
                "INSERT INTO approvals(id, run_id, action_id, reason, status) VALUES (?, ?, ?, ?, 'PENDING')",
                (approval_id, run_id, action.id, "Manager approval required"),
            )


async def test_scenario_a_executes_ticket_and_assignment_and_audits_complete_run(isolated_db):
    ticket_action = ActionContract(
        action_type="create_service_ticket",
        arguments={"customer_id": "CUST-001", "product_id": "PX-100",
                   "description": "Overheating", "severity": "HIGH"},
        evidence_ids=["SOP-042"],
    )
    ticket_result = await execute_action(ticket_action)
    assert ticket_result.success is True
    ticket_verification = await verify_action(ticket_action, ticket_result)
    assert ticket_verification.status == "VERIFIED"

    assignment_action = ActionContract(
        action_type="assign_technician",
        arguments={"ticket_id": ticket_result.data["ticket_id"], "technician_id": "TECH-001"},
        evidence_ids=["SOP-055"],
    )
    assignment_result = await execute_action(assignment_action)
    assignment_verification = await verify_action(assignment_action, assignment_result)
    assert assignment_result.success is True
    assert assignment_verification.status == "VERIFIED"

    log_run(
        run_id="RUN-A",
        prompt="Create a ticket and dispatch a technician for PX-100 overheating.",
        evidence_ids=["SOP-042", "SOP-055"],
        policy_rule="service ticket and dispatch policy",
        decision="EXECUTE",
        actions=[ticket_action, assignment_action],
        verification=[ticket_verification, assignment_verification],
    )
    record = get_run_audit("RUN-A")
    assert record is not None
    assert record.prompt.startswith("Create a ticket")
    assert record.evidence_ids == ["SOP-042", "SOP-055"]
    assert record.policy_rule == "service ticket and dispatch policy"
    assert record.decision == "EXECUTE"
    assert len(record.actions) == 2
    assert [item["status"] for item in record.verification] == ["VERIFIED", "VERIFIED"]
    with database.get_db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM run_audit WHERE run_id = 'RUN-A'").fetchone()[0] == 1


async def test_scenario_b_waits_then_approval_resumes_action_and_blocks_second_approval(isolated_db):
    action = ActionContract(
        action_type="create_service_ticket",
        arguments={"customer_id": "CUST-002", "product_id": "PX-100",
                   "description": "Approved replacement assessment", "severity": "HIGH"},
        evidence_ids=["POL-EQP-002"],
    )
    _create_run("RUN-B", action, approval_id="APR-B")
    with database.get_db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'service_tickets'"
        ).fetchone()[0] == 0

    response = await approve_action("APR-B", ApprovalDecision(
        decision=ApprovalStatus.APPROVED, decided_by="manager-7"))
    assert response["status"] == "APPROVED"
    assert response["verification"]["status"] == "VERIFIED"
    with database.get_db() as conn:
        assert conn.execute("SELECT status FROM approvals WHERE id = 'APR-B'").fetchone()[0] == "APPROVED"
        assert conn.execute("SELECT status FROM service_tickets").fetchone()[0] == "CREATED"
    assert get_run_audit("RUN-B").decision == "APPROVED"

    with pytest.raises(HTTPException) as raised:
        await approve_action("APR-B")
    assert raised.value.status_code == 409


async def test_verifier_fails_when_tool_return_claims_success_but_db_row_is_missing(isolated_db):
    action = ActionContract(
        action_type="create_service_ticket",
        arguments={"customer_id": "CUST-001", "product_id": "PX-100", "description": "Test"},
    )
    tool_result = await execute_action(action)
    assert tool_result.success is True
    with database.get_db() as conn:
        conn.execute("DELETE FROM service_tickets WHERE action_id = ?", (action.id,))
    claimed_success = ActionResult(success=True, action_id=action.id, data=tool_result.data)
    verification = await verify_action(action, claimed_success)
    assert verification.status == "FAILED"
    assert verification.verified is False


async def test_registry_rejects_unknown_tools_and_invalid_arguments(isolated_db):
    unknown = await execute_action(ActionContract(action_type="delete_everything"))
    invalid = await execute_action(ActionContract(
        action_type="create_service_ticket", arguments={"customer_id": "CUST-001"}))
    assert unknown.success is False
    assert "No tool registered" in unknown.error
    assert invalid.success is False
    assert "Invalid arguments" in invalid.error
    with database.get_db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'service_tickets'").fetchone()[0] == 0


async def test_rejection_records_outcome_without_running_action(isolated_db):
    action = ActionContract(
        action_type="create_service_ticket",
        arguments={"customer_id": "CUST-001", "product_id": "PX-100", "description": "Do not execute"},
    )
    _create_run("RUN-REJECT", action, approval_id="APR-REJECT")
    response = await reject_action("APR-REJECT", ApprovalDecision(
        decision=ApprovalStatus.REJECTED, decided_by="manager-2"))
    assert response["status"] == "REJECTED"
    with database.get_db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'service_tickets'").fetchone()[0] == 0
        assert conn.execute("SELECT status FROM actions WHERE id = ?", (action.id,)).fetchone()[0] == "REJECTED"
    record = get_run_audit("RUN-REJECT")
    assert record is not None
    assert record.decision == "REJECTED"
    assert record.verification == []
