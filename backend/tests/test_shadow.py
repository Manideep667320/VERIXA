import csv
import pytest

from app.agent.shadow import import_history_csv
from app.core.constants import AutonomyDecision
from app.core import database
from app.llm.provider import LLMProvider
from app.models.schemas import EvidenceItem


class ShadowLLM(LLMProvider):
    async def generate(self, prompt, system=""):
        raise AssertionError("structured output expected")

    async def structured_output(self, prompt, schema, system=""):
        title = schema["title"]
        if title == "IntentOutput":
            return {"request_type": "service", "entities": {},
                    "desired_outcome": "resolve", "urgency": "normal"}
        if title == "ReasoningOutput":
            return {"summary": "Evidence supports service handling", "confidence": 0.95,
                    "cited_evidence_ids": ["EVID-1"], "conflicting_evidence": False,
                    "severity": "MEDIUM"}
        if title == "ActionPlanOutput":
            return {"actions": [{"action_type": "create_service_ticket",
                                  "arguments": {}, "reason": "Open a service case",
                                  "evidence_ids": ["EVID-1"]}]}
        raise AssertionError(f"Unexpected output schema: {title}")


async def test_shadow_mode_blocks_ticket_and_technician_writes(tmp_path, monkeypatch):
    db_path = tmp_path / "shadow.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    import app.agent.shadow as shadow
    monkeypatch.setattr(shadow, "DB_PATH", db_path)
    with database.get_db() as conn:
        conn.execute("CREATE TABLE service_tickets(ticket_id TEXT)")
        conn.execute("CREATE TABLE technician_assignments(assignment_id TEXT)")

    state = await shadow.run_workflow(
        "PX-100 is overheating", llm=ShadowLLM(),
        retriever=lambda _: [EvidenceItem(id="EVID-1", source="sop.md", text="Create a ticket")],
    )

    assert state.autonomy_decision == AutonomyDecision.EXECUTE
    with database.get_db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM service_tickets").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM technician_assignments").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM shadow_runs").fetchone()[0] == 1


async def test_import_ten_row_history_computes_match_rate(tmp_path, monkeypatch):
    db_path = tmp_path / "history.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    import app.agent.shadow as shadow
    monkeypatch.setattr(shadow, "DB_PATH", db_path)
    csv_path = tmp_path / "cases.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=["request", "human_decision", "human_action"])
        writer.writeheader()
        for index in range(10):
            writer.writerow({
                "request": f"Historical service case {index}",
                "human_decision": "EXECUTE" if index < 8 else "APPROVAL_REQUIRED",
                "human_action": "create ticket",
            })

    states = await import_history_csv(
        csv_path, llm=ShadowLLM(),
        retriever=lambda _: [EvidenceItem(id="EVID-1", source="sop.md", text="Create a ticket")],
    )
    report = shadow.build_shadow_report(minutes_per_case=10)

    assert len(states) == 10
    assert report.total_cases == 10
    assert report.matched_cases == 8
    assert report.match_rate == 0.8
    assert len(report.mismatches) == 2
    assert report.escalation_rate == 0
    assert report.estimated_hours_saved == pytest.approx(8 * 10 / 60)
