"""Jira Cloud REST v3 connector with bounded retries and explicit errors."""
from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx

from app.connectors.base import Connector, ConnectorError, TicketCreate, TicketRecord
from app.core.config import settings

_ACTION_ID_RE = re.compile(r"\[E2A_ACTION_ID=([^\]]+)\]")


class JiraConnector(Connector):
    def __init__(
        self,
        *,
        base_url: str,
        email: str,
        api_token: str,
        project_key: str,
        issue_type: str = "Task",
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.project_key = project_key
        self.issue_type = issue_type
        self.timeout_seconds = timeout_seconds
        self.transport = transport
        missing = [name for name, value in {
            "JIRA_BASE_URL": base_url, "JIRA_EMAIL": email,
            "JIRA_API_TOKEN": api_token, "JIRA_PROJECT_KEY": project_key,
        }.items() if not value.strip()]
        if missing:
            raise ConnectorError(f"Jira connector configuration is missing: {', '.join(missing)}")

    @classmethod
    def from_settings(cls) -> "JiraConnector":
        return cls(
            base_url=settings.jira_base_url,
            email=settings.jira_email,
            api_token=settings.jira_api_token,
            project_key=settings.jira_project_key,
            issue_type=settings.jira_issue_type,
            timeout_seconds=settings.connector_timeout_seconds,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        allow_missing: bool = False,
    ) -> Any:
        url = f"{self.base_url}/rest/api/3/{path.lstrip('/')}"
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(
                    auth=(self.email, self.api_token), timeout=self.timeout_seconds,
                    transport=self.transport,
                ) as client:
                    response = await client.request(method, url, json=json_body,
                                                    headers={"Accept": "application/json"})
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                if attempt == 0:
                    continue
                raise ConnectorError(
                    f"Jira request timed out or could not connect after one retry ({method} {path})."
                ) from exc

            if response.status_code == 401:
                raise ConnectorError(
                    "Jira authentication failed (HTTP 401); check JIRA_EMAIL and JIRA_API_TOKEN."
                )
            if allow_missing and response.status_code == 404:
                return None
            if response.status_code == 429:
                if attempt == 0:
                    try:
                        delay = max(0.0, min(float(response.headers.get("Retry-After", "0")), 2.0))
                    except ValueError:
                        delay = 0.0
                    await asyncio.sleep(delay)
                    continue
                raise ConnectorError("Jira rate limit exceeded (HTTP 429) after one retry.")
            if response.is_error:
                detail = response.text.strip().replace("\n", " ")[:400]
                raise ConnectorError(f"Jira request failed (HTTP {response.status_code}): {detail}")
            if response.status_code == 204 or not response.content:
                return None
            try:
                return response.json()
            except ValueError as exc:
                raise ConnectorError(f"Jira returned invalid JSON for {method} {path}.") from exc
        raise ConnectorError(f"Jira request failed after one retry ({method} {path}).")

    async def create_ticket(self, ticket: TicketCreate) -> TicketRecord:
        description = (
            f"[E2A_ACTION_ID={ticket.action_id}]\n"
            f"Customer: {ticket.customer_id}\nProduct: {ticket.product_id}\n"
            f"Severity: {ticket.severity}\n\n{ticket.description}"
        )
        payload = await self._request("POST", "issue", json_body={"fields": {
            "project": {"key": self.project_key},
            "issuetype": {"name": self.issue_type},
            "summary": f"{ticket.product_id} service case: {ticket.description[:140]}",
            "description": _adf(description),
        }})
        key = str(payload.get("key") or "") if isinstance(payload, dict) else ""
        if not key:
            raise ConnectorError("Jira created an issue but returned no issue key.")
        return TicketRecord(
            ticket_id=key, action_id=ticket.action_id, customer_id=ticket.customer_id,
            product_id=ticket.product_id,
            summary=f"{ticket.product_id} service case: {ticket.description[:140]}",
            description=description, severity=ticket.severity, status="CREATED",
            metadata={"provider": "jira"},
        )

    async def get_ticket(self, ticket_id: str) -> TicketRecord | None:
        payload = await self._request(
            "GET", f"issue/{_path_quote(ticket_id)}?fields=summary,description,status,assignee,project,issuetype",
            allow_missing=True,
        )
        if payload is None:
            return None
        fields = payload.get("fields") or {}
        desc = _adf_text(fields.get("description"))
        marker = _ACTION_ID_RE.search(desc)
        status_value = fields.get("status") or {}
        status_name = str(status_value.get("name") or "UNKNOWN")
        category = ((status_value.get("statusCategory") or {}).get("key") or "").lower()
        if "cancel" in status_name.lower():
            normalized_status = "CANCELLED"
        elif category == "new" or status_name.lower() in {"open", "to do", "created"}:
            normalized_status = "CREATED"
        else:
            normalized_status = status_name.upper().replace(" ", "_")
        assignee = fields.get("assignee") or {}
        return TicketRecord(
            ticket_id=str(payload.get("key") or ticket_id),
            action_id=marker.group(1) if marker else "",
            summary=str(fields.get("summary") or ""), description=desc,
            status=normalized_status,
            assignee_id=assignee.get("accountId"),
            metadata={"provider": "jira", "jira_status": status_name,
                      "issue_id": str(payload.get("id") or "")},
        )

    async def cancel_ticket(self, ticket_id: str) -> TicketRecord:
        transitions = await self._request("GET", f"issue/{_path_quote(ticket_id)}/transitions")
        candidates = transitions.get("transitions", []) if isinstance(transitions, dict) else []
        cancel_transition = next((item for item in candidates if
                                  "cancel" in str((item.get("to") or {}).get("name", "")).lower()), None)
        if cancel_transition is None:
            raise ConnectorError(
                f"Jira issue {ticket_id} has no available Cancel transition; configure the sandbox workflow."
            )
        await self._request("POST", f"issue/{_path_quote(ticket_id)}/transitions",
                            json_body={"transition": {"id": str(cancel_transition["id"])}})
        record = await self.get_ticket(ticket_id)
        if record is None or record.status != "CANCELLED":
            raise ConnectorError(f"Jira cancel transition was submitted but {ticket_id} did not read back as cancelled.")
        return record

    async def assign(self, ticket_id: str, technician_id: str, *, action_id: str) -> TicketRecord:
        await self._request("PUT", f"issue/{_path_quote(ticket_id)}/assignee",
                            json_body={"accountId": technician_id})
        record = await self.get_ticket(ticket_id)
        if record is None or record.assignee_id != technician_id:
            raise ConnectorError(f"Jira assignment did not read back for issue {ticket_id}.")
        return record.model_copy(update={"assignment_action_id": action_id})

    async def unassign(self, ticket_id: str, *, action_id: str) -> TicketRecord:
        await self._request("PUT", f"issue/{_path_quote(ticket_id)}/assignee", json_body={"accountId": None})
        record = await self.get_ticket(ticket_id)
        if record is None or record.assignee_id is not None:
            raise ConnectorError(f"Jira unassignment did not read back for issue {ticket_id}.")
        return record.model_copy(update={"assignment_action_id": action_id})


def _adf(text: str) -> dict[str, Any]:
    return {"type": "doc", "version": 1, "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": line}]}
        for line in text.splitlines() if line
    ]}


def _adf_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts = [str(value["text"])] if isinstance(value.get("text"), str) else []
        parts.extend(_adf_text(child) for child in value.get("content", []))
        return "\n".join(part for part in parts if part)
    if isinstance(value, list):
        return "\n".join(part for item in value if (part := _adf_text(item)))
    return ""


def _path_quote(value: str) -> str:
    from urllib.parse import quote

    return quote(value, safe="")
