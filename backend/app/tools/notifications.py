"""Mock notification service."""

import logging

from app.models.schemas import ActionContract, ActionResult
from app.tools.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("send_notification")
async def send_notification(action: ActionContract) -> ActionResult:
    """Send a notification (mock — logs instead of sending)."""
    recipient = action.arguments.get("recipient", "unknown")
    message = action.arguments.get("message", action.reason)
    channel = action.arguments.get("channel", "email")
    logger.info("Notification sent [%s] to %s: %s", channel, recipient, message[:80])
    return ActionResult(
        success=True,
        action_id=action.id,
        data={"recipient": recipient, "channel": channel, "status": "SENT"},
    )
