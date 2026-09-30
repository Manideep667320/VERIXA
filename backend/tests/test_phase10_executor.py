import pytest

from app.agent.executor import execute_plan
from app.audit.logger import get_run_audit
from app.core import database
from app.core.constants import AutonomyDecision
from app.models.schemas import ActionContract, AgentState, EvidenceItem
from app.verification.verifier import VerificationResult
from app.tools.registry import execute_action


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "phase10.sqlite")
    database.init_db()


def action(kind, arguments=None):
    return ActionContract(action_type=kind, arguments=arguments or {}, evidence_ids=["SOP-042"])


def state_for(plan):
    return AgentState(
        run_id="RUN-PHASE10",
        request="Open a service ticket and dispatch support",
        evidence=[EvidenceItem(id="SOP-042", source="SOP-042.md", text="Service steps")],
        evidence_confidence=0.95,
        proposed_actions=plan,
        autonomy_decision=AutonomyDecision.EXECUTE,
    )


async def test_second_step_failure_rolls_back_first_and_audits_verified_compensation(
    isolated_db
):
    async def fail_notifications(step):
        if step.action_type == "send_notification":
            from app.models.schemas import ActionResult
            return ActionResult(success=False, action_id=step.id, error="notification transport failed")
        return await execute_action(step)

    async def replan(**kwargs):
        assert "notification transport failed" in kwargs["failure_reason"]
        return [action("send_notification", {"recipient": "ops@example.com", "message": "retry"})]

    plan = [
        action("create_service_ticket", {"customer_id": "CUST-001", "product_id": "PX-100",
                                           "description": "Overheating"}),
        action("send_notification", {"recipient": "ops@example.com", "message": "dispatch"}),
        action("assign_technician", {"ticket_id": "TKT-unused", "technician_id": "TECH-001"}),
    ]

    outcome = await execute_plan(state_for(plan), replan=replan, tool_runner=fail_notifications)

    assert outcome.state.autonomy_decision == AutonomyDecision.ESCALATE
    assert outcome.compensations[0].verification.status == "VERIFIED"
    with database.get_db() as conn:
        assert conn.execute("SELECT status FROM service_tickets").fetchone()[0] == "CANCELLED"
    audit = get_run_audit("RUN-PHASE10")
    assert audit is not None
    assert any(item.get("phase") == "COMPENSATE" for item in audit.actions)
    assert any(item.get("phase") == "ROLLBACK" and item.get("status") == "VERIFIED"
               for item in audit.verification)


async def test_replanned_expensive_step_is_policy_gated(isolated_db):
    executed = []

    async def fail_notification(step):
        executed.append(step.action_type)
        from app.models.schemas import ActionResult
        return ActionResult(success=False, action_id=step.id, error="temporary failure")

    async def replan(**kwargs):
        return [action("replace_product", {"amount": 6000})]

    outcome = await execute_plan(
        state_for([action("send_notification", {"recipient": "ops@example.com", "message": "x"})]),
        replan=replan, tool_runner=fail_notification,
    )

    assert outcome.state.autonomy_decision == AutonomyDecision.APPROVAL_REQUIRED
    assert executed == ["send_notification"]


async def test_failed_verification_rolls_back_immediately_and_escalates(isolated_db):
    ticket = action("create_service_ticket", {"customer_id": "CUST-001", "product_id": "PX-100",
                                                "description": "Overheating"})

    async def failed_readback(step, _result):
        return VerificationResult(action_id=step.id, status="FAILED", verified=False,
                                  details="ticket state could not be verified")

    async def should_not_replan(**_kwargs):
        raise AssertionError("verification failure must roll back immediately")

    outcome = await execute_plan(
        state_for([ticket]), verifier=failed_readback, replan=should_not_replan,
    )

    assert outcome.state.autonomy_decision == AutonomyDecision.ESCALATE
    assert len(outcome.compensations) == 1
    assert outcome.compensations[0].verification.status == "VERIFIED"
    with database.get_db() as conn:
        assert conn.execute("SELECT status FROM service_tickets").fetchone()[0] == "CANCELLED"
