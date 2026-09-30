from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.agent.graph import run_agent
from app.api.approval import approve_action, reject_action
from app.core import database
from app.core.constants import ApprovalStatus, AutonomyDecision
from app.feedback.insights import build_insights
from app.feedback.store import FeedbackEvent, list_feedback, record_feedback
from app.knowledge.conflicts import scan_knowledge_conflicts
from app.llm.provider import LLMProvider
from app.models.schemas import ActionResult, ApprovalDecision
from app.policy.loader import load_active_rules
from app.verification.verifier import VerificationResult


@pytest.fixture
def isolated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "phase13.sqlite")
    database.init_db()


class InsightLLM(LLMProvider):
    async def generate(self, prompt: str, system: str = "") -> str:
        raise AssertionError("structured output should be used")

    async def structured_output(self, prompt: str, schema: dict, system: str = "") -> dict:
        fields = schema["properties"]
        if "request_type" in fields:
            return {"request_type": "information", "entities": {},
                    "desired_outcome": "resolve the query", "urgency": "normal"}
        if "conflicting_evidence" in fields:
            return {"summary": "No usable guidance was found.", "confidence": 0.9,
                    "cited_evidence_ids": [], "conflicting_evidence": False, "severity": "MEDIUM"}
        return {"actions": [{"action_type": "create_service_ticket", "arguments": {},
                              "reason": "Request service follow-up", "evidence_ids": []}]}


async def test_seeded_conflict_is_attached_to_evidence_and_forces_escalation(
    isolated_database: None, tmp_path: Path
) -> None:
    from app.knowledge.ingestion import ingest_all
    from app.knowledge.retrieval import retrieve

    project_data = Path(__file__).resolve().parents[2] / "data"
    report = scan_knowledge_conflicts(project_data, as_of=date(2026, 9, 30))
    seeded = [item for item in report.conflicts
              if {item.document_a, item.document_b} == {"SOP-042", "POL-WTY-001"}]
    assert seeded, "the v1 overheating SOP and v3 warranty policy must disagree on PX-100 warranty duration"
    assert {seeded[0].version_a, seeded[0].version_b} == {"1", "3"}
    assert seeded[0].value_a != seeded[0].value_b
    assert any(item.document_id == "SOP-042" for item in report.stale_documents)

    vector_dir = tmp_path / "chroma"
    ingest_all(data_dir=project_data, persist_dir=vector_dir)
    evidence = retrieve("PX-100 warranty duration warranty months", top_k=8, persist_dir=vector_dir)
    conflicting_items = [item for item in evidence if item.metadata.get("conflict_warning")]
    assert conflicting_items
    assert all(item.metadata.get("version") and item.metadata.get("effective_date")
               for item in conflicting_items)

    state = await run_agent(
        "Check the PX-100 warranty duration and advise support.", llm=InsightLLM(),
        retriever=lambda _: evidence,
    )
    assert state.autonomy_decision == AutonomyDecision.ESCALATE


async def test_no_evidence_query_is_reported_as_knowledge_gap(isolated_database: None) -> None:
    state = await run_agent(
        "Product Y intermittent shutdown with no matching guidance", llm=InsightLLM(),
        retriever=lambda _: [],
    )
    report = build_insights()

    assert state.autonomy_decision == AutonomyDecision.ESCALATE
    assert any("Product Y intermittent shutdown" in item.query for item in report.knowledge_gaps)


def test_feedback_suggests_human_review_without_changing_active_policy(
    isolated_database: None,
) -> None:
    active_before = load_active_rules()
    record_feedback(FeedbackEvent(
        run_id="RUN-OVERRIDE-1", event_type="override", reason_code="APPROVAL_THRESHOLD_TOO_HIGH",
        prompt="Replace the PX-100 unit", decision="APPROVED", actor="manager:7",
        evidence_ids=["SOP-042"], policy_version=active_before.version,
    ))

    report = build_insights()
    active_after = load_active_rules()

    assert any(item.sop_id == "SOP-042" for item in report.sop_override_rates)
    assert report.suggested_policy_changes
    assert all(item.status == "PENDING_HUMAN_REVIEW" for item in report.suggested_policy_changes)
    assert active_after.version == active_before.version


async def test_rejection_is_saved_with_actor_and_reason_code(isolated_database: None) -> None:
    import json

    with database.get_db() as conn:
        conn.execute(
            "INSERT INTO runs(id, request, evidence, policy_result) VALUES (?, ?, ?, ?)",
            ("RUN-REJECT", "Do not replace the unit", json.dumps(["SOP-042"]),
             json.dumps({"policy_version": 1})),
        )
        conn.execute(
            """INSERT INTO actions(id, run_id, action_type, arguments, reason, evidence_ids, risk_level)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("ACT-REJECT", "RUN-REJECT", "create_service_ticket", "{}", "review", '["SOP-042"]', "LOW"),
        )
        conn.execute(
            "INSERT INTO approvals(id, run_id, action_id, reason, status) VALUES (?, ?, ?, ?, 'PENDING')",
            ("APR-REJECT", "RUN-REJECT", "ACT-REJECT", "review"),
        )

    result = await reject_action(
        "APR-REJECT", ApprovalDecision(decision=ApprovalStatus.REJECTED, decided_by="manager:7")
    )
    feedback = list_feedback()

    assert result["status"] == "REJECTED"
    assert feedback[0].event_type == "rejection"
    assert feedback[0].reason_code == "HUMAN_REJECTED"
    assert feedback[0].actor == "manager:7"


async def test_approval_is_saved_with_actor_and_reason_code(
    isolated_database: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json

    import app.api.approval as approval_api

    with database.get_db() as conn:
        conn.execute(
            "INSERT INTO runs(id, request, evidence, policy_result) VALUES (?, ?, ?, ?)",
            ("RUN-APPROVE", "Create an approved service ticket", json.dumps(["SOP-042"]),
             json.dumps({"policy_version": 1})),
        )
        conn.execute(
            """INSERT INTO actions(id, run_id, action_type, arguments, reason, evidence_ids, risk_level)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("ACT-APPROVE", "RUN-APPROVE", "create_service_ticket", "{}", "approved",
             '["SOP-042"]', "LOW"),
        )
        conn.execute(
            "INSERT INTO approvals(id, run_id, action_id, reason, status) VALUES (?, ?, ?, ?, 'PENDING')",
            ("APR-APPROVE", "RUN-APPROVE", "ACT-APPROVE", "approved"),
        )

    async def execute(action):
        return ActionResult(success=True, action_id=action.id, data={"ticket_id": "TKT-APPROVE"})

    async def verify(action, result):
        return VerificationResult(action_id=action.id, status="VERIFIED", verified=True,
                                  details="Ticket read back successfully.")

    monkeypatch.setattr(approval_api, "execute_action", execute)
    monkeypatch.setattr(approval_api, "verify_action", verify)
    result = await approve_action(
        "APR-APPROVE", ApprovalDecision(decision=ApprovalStatus.APPROVED, decided_by="manager:8")
    )
    feedback = list_feedback()

    assert result["status"] == "APPROVED"
    assert feedback[0].event_type == "approval"
    assert feedback[0].reason_code == "HUMAN_APPROVED"
    assert feedback[0].actor == "manager:8"
