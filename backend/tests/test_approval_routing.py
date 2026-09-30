from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException

from app.audit.logger import get_run_audits, log_run
from app.core import database
from app.core.config import settings


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "approval-routing.sqlite")
    database.init_db()
    return database.DB_PATH


def seed_pending_approval(approval_id="APR-ROUTE", *, action_type="create_service_ticket", arguments=None):
    with database.get_db() as conn:
        conn.execute(
            "INSERT INTO runs(id, request, evidence, policy_result, autonomy_decision) VALUES (?, ?, ?, ?, ?)",
            ("RUN-ROUTE", "Customer asks for a service visit", json.dumps(["SOP-042"]),
             json.dumps({"matched_policy": "service"}), "APPROVAL_REQUIRED"),
        )
        conn.execute(
            """INSERT INTO actions(id, run_id, action_type, arguments, reason, evidence_ids,
               risk_level, requires_approval, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("ACT-ROUTE", "RUN-ROUTE", action_type,
             json.dumps(arguments or {"customer_id": "CUST-1", "product_id": "PX-100",
                                      "description": "service visit"}),
             "Manager review", json.dumps(["SOP-042"]), "HIGH", 1, "PENDING"),
        )
        conn.execute(
            "INSERT INTO approvals(id, run_id, action_id, reason, status) VALUES (?, ?, ?, ?, 'PENDING')",
            (approval_id, "RUN-ROUTE", "ACT-ROUTE", "Manager review"),
        )


async def test_timeout_escalates_to_next_role_and_never_auto_approves(isolated_db):
    from datetime import datetime, timedelta, timezone

    from app.approvals.notifiers.mock import MockNotifier
    from app.approvals.routing import advance_expired_approvals, route_approval

    seed_pending_approval()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    notifier = MockNotifier()
    first = await route_approval("APR-ROUTE", amount=7500, risk_level="HIGH",
                                 notifier=notifier, now=now, schedule_timeout=False)
    assert first.current_role == "risk_director"

    advanced = await advance_expired_approvals(
        notifier=notifier, now=now + timedelta(seconds=first.timeout_seconds + 1),
        schedule_timeout=False,
    )
    current = await route_approval("APR-ROUTE", amount=7500, risk_level="HIGH",
                                   notifier=notifier, now=now, schedule_timeout=False)
    queued = await advance_expired_approvals(
        notifier=notifier, now=now + timedelta(seconds=first.timeout_seconds * 2 + 2),
        schedule_timeout=False,
    )
    with database.get_db() as conn:
        approval_status = conn.execute("SELECT status FROM approvals WHERE id = 'APR-ROUTE'").fetchone()[0]

    assert advanced[0].current_role == "executive_approver"
    assert current.current_role == "executive_approver"
    assert queued[0].current_role == "human_queue"
    assert queued[0].status == "HUMAN_QUEUE"
    assert [notice.role for notice in notifier.sent] == ["risk_director", "executive_approver", "human_queue"]
    assert approval_status == "PENDING"


async def test_forged_slack_callback_signature_is_rejected(isolated_db, monkeypatch):
    from app.api.approval import slack_callback

    monkeypatch.setattr(settings, "slack_signing_secret", "test-signing-secret", raising=False)

    class FakeRequest:
        headers = {"X-Slack-Request-Timestamp": str(int(time.time())),
                   "X-Slack-Signature": "v0=forged"}

        async def body(self):
            return b"payload=%7B%7D"

    with pytest.raises(HTTPException) as raised:
        await slack_callback(FakeRequest())
    assert raised.value.status_code == 401


async def test_expired_email_link_is_rejected(isolated_db, monkeypatch):
    from app.api.approval import email_decision
    from app.approvals.notifiers.email import sign_email_action

    monkeypatch.setattr(settings, "approval_link_secret", "test-link-secret", raising=False)
    token = sign_email_action("APR-ROUTE", "approve", "service_manager", "person@example.test",
                              expires_at=int(time.time()) - 5, secret="test-link-secret")
    with pytest.raises(HTTPException) as raised:
        await email_decision(token)
    assert raised.value.status_code == 410


@pytest.mark.parametrize(("action_id", "expected"), [("e2a_approve", "APPROVED"), ("e2a_reject", "REJECTED")])
async def test_slack_decision_callback_audits_approver_identity(
    isolated_db, monkeypatch, action_id, expected
):
    from app.approvals.notifiers.mock import MockNotifier
    from app.approvals.routing import route_approval
    from app.api.approval import slack_callback

    seed_pending_approval()
    log_run(run_id="RUN-ROUTE", prompt="Customer asks for a service visit",
            evidence_ids=["SOP-042"], policy_rule="service", decision="APPROVAL_REQUIRED",
            actions=[], verification=[])
    monkeypatch.setattr(settings, "slack_signing_secret", "test-signing-secret", raising=False)
    monkeypatch.setattr(settings, "approval_role_slack_users", {"risk_director": ["U-MANAGER-9"]}, raising=False)
    await route_approval("APR-ROUTE", amount=100, risk_level="HIGH", notifier=MockNotifier(), schedule_timeout=False)
    payload = {
        "type": "block_actions",
        "user": {"id": "U-MANAGER-9"},
        "actions": [{"action_id": action_id,
                      "value": json.dumps({"approval_id": "APR-ROUTE", "role": "risk_director"})}],
    }
    body = urlencode({"payload": json.dumps(payload)}).encode()
    timestamp = str(int(time.time()))
    base = b"v0:" + timestamp.encode() + b":" + body
    signature = "v0=" + hmac.new(b"test-signing-secret", base, hashlib.sha256).hexdigest()

    class FakeRequest:
        headers = {"X-Slack-Request-Timestamp": timestamp, "X-Slack-Signature": signature}

        async def body(self):
            return body

    result = await slack_callback(FakeRequest())
    record = get_run_audits()[-1]

    assert result["status"] == expected
    assert record.decision == expected
    assert record.run_id.startswith("RUN-ROUTE#approval:APR-ROUTE:")
    assert record.actions[0]["actor"] == "slack:U-MANAGER-9"
