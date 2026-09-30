"""Mock ticket service — create and retrieve service tickets."""

import logging
from uuid import uuid4

from app.models.schemas import ActionContract, ActionResult
from app.tools.registry import register_tool

logger = logging.getLogger(__name__)

# In-memory store (mock)
_tickets: dict[str, dict] = {}


@register_tool("create_service_ticket")
async def create_service_ticket(action: ActionContract) -> ActionResult:
    """Create a service ticket in the mock enterprise system."""
    ticket_id = f"TKT-{str(uuid4())[:6].upper()}"
    ticket = {
        "ticket_id": ticket_id,
        "customer_id": action.arguments.get("customer_id", "UNKNOWN"),
        "product_id": action.arguments.get("product_id", "UNKNOWN"),
        "severity": action.arguments.get("severity", "MEDIUM"),
        "description": action.arguments.get("description", action.reason),
        "status": "CREATED",
    }
    _tickets[ticket_id] = ticket
    logger.info("Service ticket created: %s", ticket_id)
    return ActionResult(success=True, action_id=action.id, data=ticket)


def get_ticket(ticket_id: str) -> dict | None:
    """Retrieve a ticket by ID (used by verification)."""
    return _tickets.get(ticket_id)
