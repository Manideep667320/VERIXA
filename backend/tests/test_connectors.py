from __future__ import annotations

import os
import json

import httpx
import pytest

from app.core import database
from app.core.config import settings
from app.models.schemas import ActionContract


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "connectors.sqlite")
    database.init_db()


async def test_mock_connector_creates_verifies_and_cancels_ticket(isolated_db, monkeypatch):
    monkeypatch.setattr(settings, "connector_provider", "mock")
    from app.connectors.base import get_connector
    from app.tools.registry import compensation_for, execute_action
    from app.verification.verifier import verify_action

    action = ActionContract(
        id="ACT-MOCK-1", action_type="create_service_ticket",
        arguments={"customer_id": "CUST-1", "product_id": "PX-100",
                   "description": "overheating", "severity": "HIGH"},
    )
    created = await execute_action(action)
    verified = await verify_action(action, created)
    rollback = compensation_for(action, created)
    cancelled = await execute_action(rollback)
    current = await get_connector().get_ticket(created.data["ticket_id"])

    assert created.success
    assert verified.status == "VERIFIED"
    assert rollback.action_type == "cancel_ticket"
    assert cancelled.success
    assert current.status == "CANCELLED"


async def test_jira_retries_rate_limit_once_then_succeeds():
    from app.connectors.base import TicketCreate
    from app.connectors.jira import JiraConnector

    requests = []

    async def respond(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(201, json={"id": "10001", "key": "OPS-42"})

    connector = JiraConnector(
        base_url="https://jira.example.test", email="user@example.test", api_token="token",
        project_key="OPS", transport=httpx.MockTransport(respond),
    )
    record = await connector.create_ticket(TicketCreate(
        action_id="ACT-1", customer_id="C1", product_id="PX-100",
        description="Overheating", severity="HIGH",
    ))

    assert record.ticket_id == "OPS-42"
    assert len(requests) == 2


async def test_jira_reports_auth_error_without_retry():
    from app.connectors.base import ConnectorError, TicketCreate
    from app.connectors.jira import JiraConnector

    requests = []

    async def unauthorized(request):
        requests.append(request)
        return httpx.Response(401, json={"message": "unauthorized"})

    connector = JiraConnector(
        base_url="https://jira.example.test", email="user@example.test", api_token="bad",
        project_key="OPS", transport=httpx.MockTransport(unauthorized),
    )
    with pytest.raises(ConnectorError, match="authentication failed.*401"):
        await connector.create_ticket(TicketCreate(
            action_id="ACT-1", customer_id="C1", product_id="PX-100",
            description="Overheating", severity="HIGH",
        ))
    assert len(requests) == 1


async def test_jira_retries_one_timeout_then_succeeds():
    from app.connectors.base import TicketCreate
    from app.connectors.jira import JiraConnector

    requests = []

    async def timeout_once(request):
        requests.append(request)
        if len(requests) == 1:
            raise httpx.ReadTimeout("simulated timeout", request=request)
        return httpx.Response(201, json={"id": "10002", "key": "OPS-43"})

    connector = JiraConnector(
        base_url="https://jira.example.test", email="user@example.test", api_token="token",
        project_key="OPS", transport=httpx.MockTransport(timeout_once),
    )
    record = await connector.create_ticket(TicketCreate(
        action_id="ACT-2", customer_id="C1", product_id="PX-100",
        description="Sensor drift", severity="MEDIUM",
    ))

    assert record.ticket_id == "OPS-43"
    assert len(requests) == 2


async def test_jira_reads_assignment_and_cancel_state_back_from_issue():
    from app.connectors.jira import JiraConnector

    state = {"status": "To Do", "assignee": None}

    async def respond(request):
        if request.method == "PUT" and request.url.path.endswith("/assignee"):
            state["assignee"] = json.loads(request.content).get("accountId")
            return httpx.Response(204)
        if request.method == "GET" and request.url.path.endswith("/transitions"):
            return httpx.Response(200, json={"transitions": [
                {"id": "42", "name": "Cancel Issue", "to": {"name": "Canceled"}},
            ]})
        if request.method == "POST" and request.url.path.endswith("/transitions"):
            state["status"] = "Canceled"
            return httpx.Response(204)
        if request.method == "GET" and "/issue/OPS-44" in request.url.path:
            return httpx.Response(200, json={
                "id": "10044", "key": "OPS-44",
                "fields": {
                    "summary": "PX-100 service case",
                    "description": {"type": "doc", "version": 1, "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": "[E2A_ACTION_ID=ACT-44]"}]},
                    ]},
                    "status": {"name": state["status"], "statusCategory": {"key": "done" if state["status"] == "Canceled" else "new"}},
                    "assignee": {"accountId": state["assignee"]} if state["assignee"] else None,
                },
            })
        return httpx.Response(404)

    connector = JiraConnector(
        base_url="https://jira.example.test", email="user@example.test", api_token="token",
        project_key="OPS", transport=httpx.MockTransport(respond),
    )
    assigned = await connector.assign("OPS-44", "jira-account-7", action_id="ACT-ASSIGN-44")
    cancelled = await connector.cancel_ticket("OPS-44")

    assert assigned.assignee_id == "jira-account-7"
    assert assigned.action_id == "ACT-44"
    assert cancelled.status == "CANCELLED"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jira_sandbox_create_verify_cancel():
    required = ("JIRA_INTEGRATION", "JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY")
    if os.getenv("JIRA_INTEGRATION") != "1" or any(not os.getenv(name) for name in required[1:]):
        pytest.skip("Set JIRA_INTEGRATION=1 and Jira sandbox credentials to enable integration test")

    from app.connectors.base import TicketCreate
    from app.connectors.jira import JiraConnector

    connector = JiraConnector.from_settings()
    created = await connector.create_ticket(TicketCreate(
        action_id="ACT-TEST-SANDBOX", customer_id="TEST", product_id="PX-100",
        description="Automated integration test; safe to cancel.", severity="LOW",
    ))
    try:
        read_back = await connector.get_ticket(created.ticket_id)
        assert read_back is not None
        assert read_back.status == "CREATED"
    finally:
        cancelled = await connector.cancel_ticket(created.ticket_id)
        assert cancelled.status == "CANCELLED"
