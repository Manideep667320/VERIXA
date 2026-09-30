"""Tools package — importing this module registers all tools."""

# Import all tool modules to trigger @register_tool decorators
from app.tools import customers, notifications, technicians, tickets  # noqa: F401
from app.tools.registry import execute_action, list_tools

__all__ = ["execute_action", "list_tools"]
