"""Mock customer lookup service."""

import logging

from app.models.schemas import ActionContract, ActionResult
from app.tools.registry import register_tool

logger = logging.getLogger(__name__)

# Mock customer data — will be replaced by seed data loading
_CUSTOMERS: dict[str, dict] = {
    "CUS-101": {"id": "CUS-101", "name": "Acme Corp", "product_ids": ["PROD-X"], "warranty_status": "ACTIVE"},
    "CUS-102": {"id": "CUS-102", "name": "TechStart Inc", "product_ids": ["PROD-X", "PROD-Y"], "warranty_status": "ACTIVE"},
    "CUS-103": {"id": "CUS-103", "name": "GlobalMfg Ltd", "product_ids": ["PROD-Y"], "warranty_status": "EXPIRED"},
}


@register_tool("lookup_customer")
async def lookup_customer(action: ActionContract) -> ActionResult:
    """Look up customer information."""
    customer_id = action.arguments.get("customer_id", "")
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return ActionResult(success=False, action_id=action.id, error=f"Customer not found: {customer_id}")
    logger.info("Customer lookup: %s → %s", customer_id, customer["name"])
    return ActionResult(success=True, action_id=action.id, data=customer)
