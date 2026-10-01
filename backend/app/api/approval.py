"""Human approval endpoints with single-use decisions and verified resumption."""

from __future__ import annotations

import json
from html import escape
from datetime import datetime, timezone
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.audit.logger import log_run
from app.approvals.notifiers.email import (
    EmailActionTokenError,
    ExpiredEmailActionToken,
    verify_email_action,
)
from app.approvals.notifiers.slack import verify_slack_signature
from app.approvals.routing import (
    RoutingError,
    advance_expired_approvals,
    get_approval_route,
    route_approval,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.constants import ApprovalStatus
from app.feedback.store import FeedbackEvent, record_feedback
from app.models import ApprovalDecision
from app.models.schemas import ActionContract
from app.tools.registry import execute_action
from app.verification.verifier import verify_action

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/pending")
async def pending_approvals():
    """Return pending approvals so the workspace can drive human review."""
    await advance_expired_approvals()
    with get_db() as conn:
        rows = conn.execute(
            """SELECT p.id AS approval_id, p.run_id, p.reason, p.status,
                      a.action_type, a.arguments, a.risk_level,
                      r.request, r.autonomy_decision
               FROM approvals p
               JOIN actions a ON a.id = p.action_id AND a.run_id = p.run_id
               JOIN runs r ON r.id = p.run_id
               WHERE p.status = 'PENDING'
               ORDER BY p.created_at DESC"""
        ).fetchall()
    return [
        {
            "approval_id": row["approval_id"],
            "run_id": row["run_id"],
            "request": row["request"],
            "reason": row["reason"],
            "action_type": row["action_type"],
            "arguments": _decode(row["arguments"], {}),
            "risk_level": row["risk_level"],
            "decision": row["autonomy_decision"],
        }
        for row in rows
    ]


def _decode(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _audit_policy_rule(policy_result: str | None) -> str:
    value = _decode(policy_result, {})
    if isinstance(value, dict):
        return str(value.get("matched_policy") or value.get("reason") or "")
    return ""


def _evidence_ids(value: str | None) -> list[str]:
    evidence = _decode(value, [])
    if not isinstance(evidence, list):
        return []
    return [item if isinstance(item, str) else item["id"]
            for item in evidence if isinstance(item, str) or (isinstance(item, dict) and item.get("id"))]


def _record_human_feedback(row: dict, *, decision: str, actor: str) -> None:
    policy_result = _decode(row["policy_result"], {})
    evidence_ids = _evidence_ids(row["evidence"])
    record_feedback(FeedbackEvent(
        run_id=row["run_id"], event_type="approval" if decision == "APPROVED" else "rejection",
        reason_code="HUMAN_APPROVED" if decision == "APPROVED" else "HUMAN_REJECTED",
        prompt=row["request"], decision=decision, actor=actor, evidence_ids=evidence_ids,
        policy_version=policy_result.get("policy_version") if isinstance(policy_result, dict) else None,
    ))


def _approval_audit_run_id(run_id: str, approval_id: str, decision: str) -> str:
    """Preserve a run's existing immutable audit row by appending a decision row."""
    with get_db() as conn:
        table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'run_audit'"
        ).fetchone()
        if table is None:
            return run_id
        exists = conn.execute("SELECT 1 FROM run_audit WHERE run_id = ?", (run_id,)).fetchone()
    if exists:
        return f"{run_id}#approval:{approval_id}:{decision.lower()}"
    return run_id


def _pending_approval(approval_id: str):
    with get_db() as conn:
        row = conn.execute(
            """SELECT p.id AS approval_id, p.run_id, p.action_id, p.reason AS approval_reason,
                      p.status AS approval_status, a.action_type, a.arguments, a.reason AS action_reason,
                      a.evidence_ids, a.risk_level, r.request, r.evidence, r.policy_result
               FROM approvals p
               JOIN actions a ON a.id = p.action_id AND a.run_id = p.run_id
               JOIN runs r ON r.id = p.run_id
               WHERE p.id = ?""",
            (approval_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Approval not found.")
    if row["approval_status"] != "PENDING":
        raise HTTPException(status_code=409, detail=f"Approval already decided: {row['approval_status']}.")
    return dict(row)


def _action_from_row(row: dict) -> ActionContract:
    return ActionContract(
        id=row["action_id"],
        action_type=row["action_type"],
        arguments=_decode(row["arguments"], {}),
        reason=row["action_reason"] or "",
        evidence_ids=_decode(row["evidence_ids"], []),
        risk_level=row["risk_level"] or "UNKNOWN",
        requires_approval=True,
    )


def _audit_action(action: ActionContract, result: dict, verification: dict | None, actor: str) -> dict:
    return {
        "action": action.model_dump(mode="json"),
        "execution": result,
        "verification": verification,
        "actor": actor,
    }


def _consume_decision(approval_id: str, status: ApprovalStatus, actor: str,
                      routed_role: str | None = None) -> dict:
    """Atomically consume a pending approval and optional currently assigned role."""
    row = _pending_approval(approval_id)
    get_approval_route(approval_id)  # ensure route table exists for unrouted legacy approvals too
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        if routed_role is not None:
            route = conn.execute(
                "SELECT current_role, status FROM approval_routes WHERE approval_id = ?",
                (approval_id,),
            ).fetchone()
            if route is None or route["current_role"] != routed_role or route["status"] not in {"PENDING", "HUMAN_QUEUE"}:
                raise HTTPException(status_code=409, detail="This approver role is no longer assigned.")
        updated = conn.execute(
            "UPDATE approvals SET status = ?, decided_by = ?, decided_at = ? "
            "WHERE id = ? AND status = 'PENDING'",
            (status.value, actor, now, approval_id),
        ).rowcount
        if updated != 1:
            raise HTTPException(status_code=409, detail="Approval has already been decided.")
        if status == ApprovalStatus.APPROVED:
            conn.execute("UPDATE actions SET status = 'EXECUTING' WHERE id = ?", (row["action_id"],))
        else:
            conn.execute("UPDATE actions SET status = 'REJECTED' WHERE id = ?", (row["action_id"],))
        conn.execute(
            "UPDATE approval_routes SET status = 'DECIDED', expires_at = NULL, decided_by = ?, "
            "updated_at = ? WHERE approval_id = ? AND status IN ('PENDING', 'HUMAN_QUEUE')",
            (actor, now, approval_id),
        )
    return row


async def _approve_action(approval_id: str, decision: ApprovalDecision | None = None,
                          *, routed_role: str | None = None):
    if decision and decision.decision != ApprovalStatus.APPROVED:
        raise HTTPException(status_code=422, detail="Approve endpoint requires decision=APPROVED.")
    await advance_expired_approvals()
    approver = decision.decided_by if decision else "manager"
    row = _consume_decision(approval_id, ApprovalStatus.APPROVED, approver, routed_role)
    _record_human_feedback(row, decision="APPROVED", actor=approver)
    action = _action_from_row(row)
    execution = await execute_action(action)
    verification = await verify_action(action, execution)
    result_json = execution.model_dump(mode="json")
    verification_json = verification.model_dump(mode="json")
    action_status = "VERIFIED" if verification.verified else "FAILED"
    with get_db() as conn:
        conn.execute(
            "UPDATE actions SET status = ?, execution_result = ?, verification_result = ? WHERE id = ?",
            (action_status, json.dumps(result_json), json.dumps(verification_json), row["action_id"]),
        )
        conn.execute(
            "UPDATE runs SET autonomy_decision = 'APPROVED', execution_results = ?, "
            "verification_results = ?, status = ?, updated_at = datetime('now') WHERE id = ?",
            (json.dumps([result_json]), json.dumps([verification_json]), action_status, row["run_id"]),
        )

    log_run(
        run_id=_approval_audit_run_id(row["run_id"], approval_id, "APPROVED"),
        prompt=row["request"],
        evidence_ids=_evidence_ids(row["evidence"]),
        policy_rule=_audit_policy_rule(row["policy_result"]),
        decision="APPROVED",
        actions=[_audit_action(action, result_json, verification_json, approver)],
        verification=[verification_json],
    )
    return {
        "approval_id": approval_id,
        "status": "APPROVED",
        "execution": result_json,
        "verification": verification_json,
    }


async def _reject_action(approval_id: str, decision: ApprovalDecision | None = None,
                         *, routed_role: str | None = None):
    if decision and decision.decision != ApprovalStatus.REJECTED:
        raise HTTPException(status_code=422, detail="Reject endpoint requires decision=REJECTED.")
    await advance_expired_approvals()
    approver = decision.decided_by if decision else "manager"
    row = _consume_decision(approval_id, ApprovalStatus.REJECTED, approver, routed_role)
    _record_human_feedback(row, decision="REJECTED", actor=approver)
    action = _action_from_row(row)
    log_run(
        run_id=_approval_audit_run_id(row["run_id"], approval_id, "REJECTED"),
        prompt=row["request"],
        evidence_ids=_evidence_ids(row["evidence"]),
        policy_rule=_audit_policy_rule(row["policy_result"]),
        decision="REJECTED",
        actions=[{"action": action.model_dump(mode="json"), "status": "REJECTED", "actor": approver}],
        verification=[],
    )
    return {"approval_id": approval_id, "status": "REJECTED"}


@router.post("/{approval_id}/approve")
async def approve_action(approval_id: str, decision: ApprovalDecision | None = None):
    """Consume a pending approval, execute its action, verify it, and audit the actor."""
    return await _approve_action(approval_id, decision)


@router.post("/{approval_id}/reject")
async def reject_action(approval_id: str, decision: ApprovalDecision | None = None):
    """Consume a pending approval without executing its action."""
    return await _reject_action(approval_id, decision)


@router.post("/{approval_id}/route")
async def start_approval_routing(approval_id: str):
    """Assign a pending approval to the policy-selected role and send its notification."""
    row = _pending_approval(approval_id)
    arguments = _decode(row["arguments"], {})
    amount = _amount(arguments)
    try:
        route = await route_approval(approval_id, amount=amount,
                                     risk_level=row["risk_level"] or "UNKNOWN")
    except RoutingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return route.model_dump(mode="json")


@router.post("/escalate-due")
async def escalate_due_approvals():
    """Scheduler hook for timeout catch-up after process restarts."""
    routes = await advance_expired_approvals()
    return {"escalated": [route.model_dump(mode="json") for route in routes]}


@router.get("/{approval_id}/routing")
async def get_approval_routing(approval_id: str):
    await advance_expired_approvals()
    route = get_approval_route(approval_id)
    if route is None:
        raise HTTPException(status_code=404, detail="Approval has not been routed.")
    return route.model_dump(mode="json")


@router.post("/slack/callback")
async def slack_callback(request: Request):
    raw_body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    if not verify_slack_signature(raw_body, timestamp, signature, settings.slack_signing_secret):
        raise HTTPException(status_code=401, detail="Slack request signature is invalid or expired.")
    try:
        form = parse_qs(raw_body.decode("utf-8"), strict_parsing=True)
        payload = json.loads(form["payload"][0])
        action = payload["actions"][0]
        decision_name = action["action_id"]
        value = json.loads(action["value"])
        approval_id, role = value["approval_id"], value["role"]
        user_id = payload["user"]["id"]
    except (KeyError, IndexError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Malformed Slack approval callback.") from exc
    if decision_name not in {"e2a_approve", "e2a_reject"}:
        raise HTTPException(status_code=400, detail="Unsupported Slack approval action.")
    if user_id not in settings.approval_role_slack_users.get(role, []):
        raise HTTPException(status_code=403, detail="Slack user is not assigned to this approval role.")
    actor = f"slack:{user_id}"
    decision = ApprovalDecision(
        decision=ApprovalStatus.APPROVED if decision_name == "e2a_approve" else ApprovalStatus.REJECTED,
        decided_by=actor,
    )
    try:
        if decision.decision == ApprovalStatus.APPROVED:
            return await _approve_action(approval_id, decision, routed_role=role)
        return await _reject_action(approval_id, decision, routed_role=role)
    except RoutingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/email/{token}", response_class=HTMLResponse)
async def email_confirmation(token: str):
    """Render a confirmation page; link scanners cannot decide the approval with GET."""
    try:
        action = verify_email_action(token)
    except ExpiredEmailActionToken as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except EmailActionTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    word = "approve" if action.decision == "approve" else "reject"
    form_action = f"/api/approvals/email/{escape(token, quote=True)}"
    html = (
        "<!doctype html><html><body><h1>Confirm approval decision</h1>"
        f"<p>Confirm that you want to {word} approval {escape(action.approval_id)} as {escape(action.role)}.</p>"
        f'<form method="post" action="{form_action}"><button type="submit">Confirm {word.title()}</button></form>'
        "</body></html>"
    )
    return HTMLResponse(html)


@router.post("/email/{token}")
async def email_decision(token: str):
    try:
        action = verify_email_action(token)
    except ExpiredEmailActionToken as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except EmailActionTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    actor = f"email:{action.recipient}"
    decision = ApprovalDecision(
        decision=ApprovalStatus.APPROVED if action.decision == "approve" else ApprovalStatus.REJECTED,
        decided_by=actor,
    )
    try:
        if action.decision == "approve":
            return await _approve_action(action.approval_id, decision, routed_role=action.role)
        return await _reject_action(action.approval_id, decision, routed_role=action.role)
    except RoutingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _amount(arguments: dict) -> float:
    for key in ("amount", "cost", "estimated_cost", "replacement_cost"):
        try:
            return float(str(arguments.get(key, 0)).replace("$", "").replace(",", ""))
        except (TypeError, ValueError):
            continue
    return 0.0
