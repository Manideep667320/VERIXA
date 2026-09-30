"""Verify write state through connectors and SQLite-backed read models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.connectors.base import get_connector
from app.core.database import get_db
from app.models.schemas import ActionContract


class VerificationResult(BaseModel):
    action_id: str
    status: Literal["VERIFIED", "FAILED"]
    verified: bool
    details: str


def _default_ticket_id(action_id: str) -> str:
    return f"TKT-{action_id}"


async def verify_action(action: ActionContract, tool_result: object | None = None) -> VerificationResult:
    """Read ticket state independently; create/assign response data is used only as an object locator."""
    try:
        if action.action_type in {"create_service_ticket", "assign_technician", "cancel_ticket", "unassign_technician"}:
            ticket_id = _default_ticket_id(action.id)
            result_data = getattr(tool_result, "data", None)
            if isinstance(result_data, dict) and isinstance(result_data.get("ticket_id"), str):
                ticket_id = result_data["ticket_id"]
            elif action.action_type in {"assign_technician", "unassign_technician"}:
                ticket_id = str(action.arguments.get("ticket_id", ticket_id))

            ticket = await get_connector().get_ticket(ticket_id)
            if action.action_type == "create_service_ticket":
                ok = ticket is not None and ticket.status == "CREATED" and ticket.action_id == action.id
                details = "Connector read-back confirms ticket CREATED." if ok else "Connector read-back did not confirm ticket CREATED."
            elif action.action_type == "assign_technician":
                expected_id = str(action.arguments.get("technician_id", ""))
                ok = (ticket is not None and ticket.status == "CREATED" and ticket.assignee_id == expected_id
                      and ticket.assignment_action_id in {None, action.id})
                details = "Connector read-back confirms technician assignment." if ok else "Connector read-back did not confirm technician assignment."
            elif action.action_type == "cancel_ticket":
                ok = ticket is not None and ticket.status == "CANCELLED"
                details = "Connector read-back confirms ticket cancellation." if ok else "Connector read-back did not confirm ticket cancellation."
            else:
                ok = ticket is not None and ticket.assignee_id is None
                details = "Connector read-back confirms technician unassignment." if ok else "Connector read-back did not confirm technician unassignment."
        else:
            with get_db() as conn:
                if action.action_type == "lookup_customer":
                    row = conn.execute(
                        "SELECT found FROM customer_lookups WHERE action_id = ?", (action.id,)
                    ).fetchone()
                    ok = row is not None and row["found"] == 1
                    details = "Customer lookup is persisted." if ok else "Successful customer lookup is missing."
                elif action.action_type == "send_notification":
                    row = conn.execute(
                        "SELECT status FROM notifications WHERE action_id = ?", (action.id,)
                    ).fetchone()
                    ok = row is not None and row["status"] == "SENT"
                    details = "Notification row exists with status SENT." if ok else "Notification row is missing or not SENT."
                else:
                    return VerificationResult(
                        action_id=action.id, status="FAILED", verified=False,
                        details=f"No verifier for action type: {action.action_type}",
                    )
    except Exception as exc:
        return VerificationResult(action_id=action.id, status="FAILED", verified=False,
                                  details=f"Could not verify persisted state: {exc}")
    return VerificationResult(action_id=action.id, status="VERIFIED" if ok else "FAILED",
                              verified=ok, details=details)
