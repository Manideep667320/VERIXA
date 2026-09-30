"""Approval API routes — approve or reject pending actions."""

from fastapi import APIRouter, HTTPException

from app.models import ApprovalDecision

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("/{approval_id}/approve")
async def approve_action(approval_id: str, decision: ApprovalDecision | None = None):
    """Approve a pending action."""
    # TODO: Update approval record, resume agent execution
    return {"approval_id": approval_id, "status": "APPROVED", "message": "Not yet implemented."}


@router.post("/{approval_id}/reject")
async def reject_action(approval_id: str, decision: ApprovalDecision | None = None):
    """Reject a pending action."""
    # TODO: Update approval record, stop execution
    return {"approval_id": approval_id, "status": "REJECTED", "message": "Not yet implemented."}
