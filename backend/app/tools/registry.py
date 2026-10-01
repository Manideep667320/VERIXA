"""Validated SQLite-backed execution for the registered enterprise tools."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from app.connectors.base import TicketCreate, get_connector
from app.core.database import get_db
from app.models.schemas import ActionContract, ActionResult

logger = logging.getLogger(__name__)


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateServiceTicketInput(ToolInput):
    customer_id: str
    product_id: str
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"


class AssignTechnicianInput(ToolInput):
    ticket_id: str
    technician_id: str


class LookupCustomerInput(ToolInput):
    customer_id: str


class SendNotificationInput(ToolInput):
    recipient: str
    message: str
    channel: Literal["email", "sms", "phone"] = "email"


class CancelTicketInput(ToolInput):
    ticket_id: str


class UnassignTechnicianInput(ToolInput):
    ticket_id: str
    original_action_id: str


class ReplaceProductInput(ToolInput):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    product_id: str | None = "DEFAULT-UNIT"
    customer_id: str | None = "CUSTOMER"
    amount: float | str | None = 0.0
    replacement_model: str | None = None
    reason: str | None = None


class IssueRefundInput(ToolInput):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    customer_id: str | None = "CUSTOMER"
    amount: float | str | None = 0.0
    reason: str | None = None


_REGISTRY: dict[str, Callable] = {}
_INPUT_SCHEMAS: dict[str, type[ToolInput]] = {
    "create_service_ticket": CreateServiceTicketInput,
    "assign_technician": AssignTechnicianInput,
    "lookup_customer": LookupCustomerInput,
    "send_notification": SendNotificationInput,
    "cancel_ticket": CancelTicketInput,
    "unassign_technician": UnassignTechnicianInput,
    "replace_product": ReplaceProductInput,
    "issue_refund": IssueRefundInput,
}

COMPENSATIONS: dict[str, str] = {
    "create_service_ticket": "cancel_ticket",
    "assign_technician": "unassign_technician",
}


def register_tool(action_type: str):
    """Register an action handler, retaining compatibility with tool modules."""

    def decorator(fn: Callable):
        _REGISTRY[action_type] = fn
        return fn

    return decorator


def _parse_amount(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


@register_tool("replace_product")
async def _replace_product_handler(action: ActionContract) -> ActionResult:
    return await execute_action(action)


@register_tool("issue_refund")
async def _issue_refund_handler(action: ActionContract) -> ActionResult:
    return await execute_action(action)


def _ensure_tool_tables() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS service_tickets (
                ticket_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE,
                customer_id TEXT NOT NULL, product_id TEXT NOT NULL,
                description TEXT NOT NULL, severity TEXT NOT NULL, status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS technician_assignments (
                assignment_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE,
                ticket_id TEXT NOT NULL, technician_id TEXT NOT NULL, status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS customer_lookups (
                lookup_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE,
                customer_id TEXT NOT NULL, found INTEGER NOT NULL, looked_up_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE,
                recipient TEXT NOT NULL, message TEXT NOT NULL, channel TEXT NOT NULL, status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS customer_profiles (
                customer_id TEXT PRIMARY KEY, profile_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS product_replacements (
                replacement_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE,
                product_id TEXT, customer_id TEXT, amount REAL NOT NULL, status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS refunds (
                refund_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE,
                customer_id TEXT, amount REAL NOT NULL, status TEXT NOT NULL
            );
            """
        )
        if conn.execute("SELECT COUNT(*) FROM customer_profiles").fetchone()[0] == 0:
            data_path = Path(__file__).resolve().parents[3] / "data" / "customers.json"
            if data_path.exists():
                for customer in json.loads(data_path.read_text(encoding="utf-8")):
                    customer_id = customer.get("customer_id") or customer.get("id")
                    if customer_id:
                        conn.execute(
                            "INSERT OR IGNORE INTO customer_profiles(customer_id, profile_json) VALUES (?, ?)",
                            (customer_id, json.dumps(customer, ensure_ascii=False)),
                        )


def _ticket_id(action_id: str) -> str:
    return f"TKT-{action_id}"


def _assignment_id(action_id: str) -> str:
    return f"ASN-{action_id}"


async def execute_action(action: ActionContract) -> ActionResult:
    """Validate and execute one registered action; all writes are persisted in SQLite."""
    if (action.action_type not in _INPUT_SCHEMAS
            or (action.action_type not in _REGISTRY and action.action_type not in COMPENSATIONS.values())):
        return ActionResult(success=False, action_id=action.id,
                            error=f"No tool registered for: {action.action_type}")
    schema = _INPUT_SCHEMAS[action.action_type]
    try:
        arguments = schema.model_validate(action.arguments)
    except Exception as exc:
        return ActionResult(success=False, action_id=action.id, error=f"Invalid arguments: {exc}")

    _ensure_tool_tables()
    values = arguments.model_dump()
    try:
        if action.action_type == "create_service_ticket":
            ticket = await get_connector().create_ticket(TicketCreate(
                action_id=action.id, customer_id=values["customer_id"],
                product_id=values["product_id"], description=values["description"],
                severity=values["severity"],
            ))
            data = ticket.model_dump(mode="json")
        elif action.action_type == "assign_technician":
            ticket = await get_connector().assign(
                values["ticket_id"], values["technician_id"], action_id=action.id,
            )
            data = {**ticket.model_dump(mode="json"), "technician_id": values["technician_id"]}
        elif action.action_type == "lookup_customer":
            with get_db() as conn:
                row = conn.execute(
                    "SELECT profile_json FROM customer_profiles WHERE customer_id = ?",
                    (values["customer_id"],),
                ).fetchone()
                conn.execute(
                    "INSERT INTO customer_lookups(lookup_id, action_id, customer_id, found) VALUES (?, ?, ?, ?)",
                    (f"LOOK-{action.id}", action.id, values["customer_id"], int(row is not None)),
                )
            if row is None:
                return ActionResult(success=False, action_id=action.id,
                                    error=f"Customer not found: {values['customer_id']}")
            data = json.loads(row["profile_json"])
        elif action.action_type == "cancel_ticket":
            ticket = await get_connector().cancel_ticket(values["ticket_id"])
            data = ticket.model_dump(mode="json")
        elif action.action_type == "unassign_technician":
            ticket = await get_connector().unassign(
                values["ticket_id"], action_id=values["original_action_id"],
            )
            data = ticket.model_dump(mode="json")
        elif action.action_type == "replace_product":
            replacement_id = f"RPL-{action.id}"
            amt = _parse_amount(values.get("amount", 0))
            with get_db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO product_replacements(replacement_id, action_id, product_id, customer_id, amount, status) "
                    "VALUES (?, ?, ?, ?, ?, 'AUTHORIZED')",
                    (replacement_id, action.id, str(values.get("product_id") or "DEFAULT-UNIT"),
                     str(values.get("customer_id") or "CUSTOMER"), amt),
                )
            data = {"replacement_id": replacement_id, "amount": amt, "status": "AUTHORIZED", **values}
        elif action.action_type == "issue_refund":
            refund_id = f"RFD-{action.id}"
            amt = _parse_amount(values.get("amount", 0))
            with get_db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO refunds(refund_id, action_id, customer_id, amount, status) "
                    "VALUES (?, ?, ?, ?, 'PROCESSED')",
                    (refund_id, action.id, str(values.get("customer_id") or "CUSTOMER"), amt),
                )
            data = {"refund_id": refund_id, "amount": amt, "status": "PROCESSED", **values}
        elif action.action_type == "send_notification":
            notification_id = f"NTF-{action.id}"
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO notifications VALUES (?, ?, ?, ?, ?, 'SENT')",
                    (notification_id, action.id, values.get("recipient", "ops@example.com"),
                     values.get("message", "Notification"), values.get("channel", "email")),
                )
            data = {"notification_id": notification_id, **values, "status": "SENT"}
        else:
            data = {**values, "status": "EXECUTED"}
        logger.info("Tool executed: %s", action.action_type)
        return ActionResult(success=True, action_id=action.id, data=data)
    except Exception as exc:
        logger.exception("Tool execution failed: %s", action.action_type)
        return ActionResult(success=False, action_id=action.id, error=str(exc))


def list_tools() -> list[str]:
    """Return the actions available through the validated execution boundary."""
    return [name for name in _INPUT_SCHEMAS if name not in {"cancel_ticket", "unassign_technician"}]


def compensation_for(action: ActionContract, result: ActionResult | None = None) -> ActionContract | None:
    """Build the declared inverse action for a persisted write tool."""
    compensation_type = COMPENSATIONS.get(action.action_type)
    if compensation_type is None:
        return None
    ticket_id = ((result.data.get("ticket_id") if result else None)
                 or action.arguments.get("ticket_id")
                 or _ticket_id(action.id))
    arguments = {"ticket_id": str(ticket_id)}
    if compensation_type == "unassign_technician":
        arguments["original_action_id"] = action.id
    return ActionContract(
        action_type=compensation_type,
        arguments=arguments,
        reason=f"Compensate {action.action_type} after workflow failure",
        evidence_ids=action.evidence_ids,
    )
