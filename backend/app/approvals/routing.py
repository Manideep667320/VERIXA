"""Policy-driven approval routing with timed escalation and no automatic approval."""
from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field

from app.approvals.notifiers.base import ApprovalNotice, ApprovalNotifier, get_notifier
from app.core.config import settings
from app.core import database
from app.core.database import get_db
from app.core.constants import RiskLevel
from app.policy.loader import ApprovalRoutingRules, load_active_rules


class RoutingError(RuntimeError):
    """An approval cannot be routed or its routed role is no longer active."""


class ApprovalRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    roles: list[str]
    role_index: int = Field(ge=0)
    current_role: str
    human_queue: str
    timeout_seconds: int
    expires_at: datetime | None
    status: str
    decided_by: str | None = None


_scheduled: dict[str, asyncio.Task] = {}


def _ensure_route_table() -> None:
    database.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(database.DB_PATH)) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS approval_routes (
            approval_id TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            risk_level TEXT NOT NULL,
            roles TEXT NOT NULL,
            role_index INTEGER NOT NULL,
            current_role TEXT NOT NULL,
            human_queue TEXT NOT NULL,
            timeout_seconds INTEGER NOT NULL,
            expires_at TEXT,
            status TEXT NOT NULL,
            decided_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _routing_rules() -> ApprovalRoutingRules:
    return load_active_rules().approval_routing


def _timeout(rules: ApprovalRoutingRules) -> int:
    return settings.approval_timeout_seconds or rules.timeout_seconds


def get_approval_route(approval_id: str) -> ApprovalRoute | None:
    _ensure_route_table()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM approval_routes WHERE approval_id = ?", (approval_id,)).fetchone()
    return _from_row(row) if row else None


async def route_approval(
    approval_id: str,
    *,
    amount: float,
    risk_level: RiskLevel | str,
    notifier: ApprovalNotifier | None = None,
    now: datetime | None = None,
    schedule_timeout: bool = True,
) -> ApprovalRoute:
    """Assign a pending approval to the policy-selected first role and notify it."""
    _ensure_route_table()
    current_time = now or _utcnow()
    rules = _routing_rules()
    timeout_seconds = _timeout(rules)
    normalized_risk = RiskLevel(str(risk_level).upper())
    roles = rules.roles_for(amount, normalized_risk)
    deadline = current_time + timedelta(seconds=timeout_seconds)
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM approval_routes WHERE approval_id = ?", (approval_id,)).fetchone()
        if existing:
            return _from_row(existing)
        approval = conn.execute(
            "SELECT status FROM approvals WHERE id = ?", (approval_id,)
        ).fetchone()
        if approval is None:
            raise RoutingError(f"Approval not found: {approval_id}")
        if approval["status"] != "PENDING":
            raise RoutingError(f"Approval is already decided: {approval['status']}")
        conn.execute(
            """INSERT INTO approval_routes
            (approval_id, amount, risk_level, roles, role_index, current_role, human_queue,
             timeout_seconds, expires_at, status, decided_by, created_at, updated_at)
             VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, 'PENDING', NULL, ?, ?)""",
            (approval_id, amount, normalized_risk.value, json.dumps(roles), roles[0],
             rules.human_queue, timeout_seconds, deadline.isoformat(),
             current_time.isoformat(), current_time.isoformat()),
        )
    route = get_approval_route(approval_id)
    await _notify(route, notifier)
    if schedule_timeout:
        _schedule_timeout(route)
    return route


async def advance_expired_approvals(
    *,
    notifier: ApprovalNotifier | None = None,
    now: datetime | None = None,
    schedule_timeout: bool = True,
) -> list[ApprovalRoute]:
    """Escalate every timed-out approval by one role, then place it in the human queue."""
    _ensure_route_table()
    current_time = now or _utcnow()
    with get_db() as conn:
        rows = conn.execute(
            """SELECT ar.* FROM approval_routes ar JOIN approvals a ON a.id = ar.approval_id
               WHERE ar.status = 'PENDING' AND a.status = 'PENDING' AND ar.expires_at <= ?
               ORDER BY ar.expires_at""",
            (current_time.isoformat(),),
        ).fetchall()
    advanced: list[ApprovalRoute] = []
    for row in rows:
        route = _from_row(row)
        if route.role_index + 1 < len(route.roles):
            new_index = route.role_index + 1
            new_role = route.roles[new_index]
            deadline = current_time + timedelta(seconds=route.timeout_seconds)
            status = "PENDING"
            expiry = deadline.isoformat()
        else:
            new_index = route.role_index
            new_role = route.human_queue
            deadline = None
            status = "HUMAN_QUEUE"
            expiry = None
        with get_db() as conn:
            updated = conn.execute(
                """UPDATE approval_routes SET role_index = ?, current_role = ?, expires_at = ?,
                   status = ?, updated_at = ? WHERE approval_id = ? AND status = 'PENDING'
                   AND role_index = ?""",
                (new_index, new_role, expiry, status, current_time.isoformat(),
                 route.approval_id, route.role_index),
            ).rowcount
        if updated != 1:
            continue
        latest = get_approval_route(route.approval_id)
        await _notify(latest, notifier)
        advanced.append(latest)
        if schedule_timeout and latest.expires_at is not None:
            _schedule_timeout(latest)
    return advanced


def mark_approval_decided(approval_id: str, decided_by: str) -> None:
    """Stop pending timeout escalation after an existing approval decision succeeds."""
    _ensure_route_table()
    with get_db() as conn:
        conn.execute(
            "UPDATE approval_routes SET status = 'DECIDED', expires_at = NULL, decided_by = ?, "
            "updated_at = ? WHERE approval_id = ? AND status IN ('PENDING', 'HUMAN_QUEUE')",
            (decided_by, _utcnow().isoformat(), approval_id),
        )


def validate_current_role(approval_id: str, role: str) -> ApprovalRoute:
    route = get_approval_route(approval_id)
    if route is None:
        raise RoutingError("Approval has not been routed.")
    if route.status not in {"PENDING", "HUMAN_QUEUE"} or route.current_role != role:
        raise RoutingError("This approver role is no longer assigned to the approval.")
    return route


def _from_row(row) -> ApprovalRoute:
    expiry = datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
    return ApprovalRoute(
        approval_id=row["approval_id"], roles=json.loads(row["roles"]), role_index=row["role_index"],
        current_role=row["current_role"], human_queue=row["human_queue"],
        timeout_seconds=row["timeout_seconds"], expires_at=expiry,
        status=row["status"], decided_by=row["decided_by"],
    )


async def _notify(route: ApprovalRoute, notifier: ApprovalNotifier | None) -> None:
    with get_db() as conn:
        row = conn.execute(
            """SELECT a.action_type, a.reason, a.arguments, a.risk_level, r.id AS run_id, r.request
               FROM approvals p JOIN actions a ON a.id = p.action_id AND a.run_id = p.run_id
               JOIN runs r ON r.id = p.run_id WHERE p.id = ?""",
            (route.approval_id,),
        ).fetchone()
    if row is None:
        raise RoutingError(f"Approval details are missing: {route.approval_id}")
    arguments = json.loads(row["arguments"] or "{}")
    amount = _amount(arguments)
    notice = ApprovalNotice(
        approval_id=route.approval_id, run_id=row["run_id"], role=route.current_role,
        request=row["request"], action_type=row["action_type"], action_reason=row["reason"] or "",
        amount=amount, risk_level=row["risk_level"] or "UNKNOWN", expires_at=route.expires_at,
    )
    await (notifier or get_notifier()).send_approval(notice)


def _schedule_timeout(route: ApprovalRoute) -> None:
    if route.expires_at is None:
        return
    previous = _scheduled.get(route.approval_id)
    if previous is not None and not previous.done():
        previous.cancel()

    async def wait_and_escalate():
        delay = max(0, (route.expires_at - _utcnow()).total_seconds())
        await asyncio.sleep(delay)
        _scheduled.pop(route.approval_id, None)
        await advance_expired_approvals()

    _scheduled[route.approval_id] = asyncio.create_task(wait_and_escalate())


def _amount(arguments: dict) -> float:
    for name in ("amount", "cost", "estimated_cost", "replacement_cost"):
        try:
            return float(str(arguments.get(name, 0)).replace("$", "").replace(",", ""))
        except (TypeError, ValueError):
            continue
    return 0.0
