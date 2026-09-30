"""Tool registry — dispatch pattern for action execution."""

from __future__ import annotations

import logging
from typing import Callable

from app.models.schemas import ActionContract, ActionResult

logger = logging.getLogger(__name__)

# Registry: action_type → handler function
_REGISTRY: dict[str, Callable] = {}


def register_tool(action_type: str):
    """Decorator to register a tool handler."""
    def decorator(fn: Callable):
        _REGISTRY[action_type] = fn
        return fn
    return decorator


async def execute_action(action: ActionContract) -> ActionResult:
    """Execute an action through the registered tool handler."""
    handler = _REGISTRY.get(action.action_type)
    if handler is None:
        logger.error("No tool registered for action type: %s", action.action_type)
        return ActionResult(
            success=False,
            action_id=action.id,
            error=f"No tool registered for: {action.action_type}",
        )
    try:
        result = await handler(action)
        logger.info("Tool executed: %s → %s", action.action_type, "SUCCESS" if result.success else "FAILED")
        return result
    except Exception as e:
        logger.exception("Tool execution failed: %s", action.action_type)
        return ActionResult(success=False, action_id=action.id, error=str(e))


def list_tools() -> list[str]:
    """Return all registered tool names."""
    return list(_REGISTRY.keys())
