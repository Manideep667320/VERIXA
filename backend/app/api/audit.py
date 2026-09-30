"""Audit API routes — retrieve audit trails."""

from fastapi import APIRouter

from app.models import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{run_id}")
async def get_audit_trail(run_id: str) -> list[AuditEvent]:
    """Retrieve the full audit trail for a given run."""
    # TODO: Fetch from database
    return []
