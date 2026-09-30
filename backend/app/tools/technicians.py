"""Mock technician assignment service."""

import logging
from uuid import uuid4

from app.models.schemas import ActionContract, ActionResult
from app.tools.registry import register_tool

logger = logging.getLogger(__name__)

# In-memory store (mock)
_assignments: dict[str, dict] = {}


@register_tool("assign_technician")
async def assign_technician(action: ActionContract) -> ActionResult:
    """Assign an available technician to a service ticket."""
    assignment_id = f"ASN-{str(uuid4())[:6].upper()}"
    assignment = {
        "assignment_id": assignment_id,
        "ticket_id": action.arguments.get("ticket_id", "UNKNOWN"),
        "technician_id": action.arguments.get("technician_id", "TECH-001"),
        "status": "ASSIGNED",
    }
    _assignments[assignment_id] = assignment
    logger.info("Technician assigned: %s → %s", assignment["technician_id"], assignment["ticket_id"])
    return ActionResult(success=True, action_id=action.id, data=assignment)
