"""Analytics summaries computed exclusively from immutable audit rows."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.audit.logger import RunAuditRecord, get_run_audits
from app.core.config import settings


class AnalyticsSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_date: date | None = None
    to_date: date | None = None
    total_runs: int = Field(ge=0)
    automation_rate: float = Field(ge=0.0, le=1.0)
    approval_rate: float = Field(ge=0.0, le=1.0)
    escalation_rate: float = Field(ge=0.0, le=1.0)
    verification_failure_rate: float = Field(ge=0.0, le=1.0)
    rollback_count: int = Field(ge=0)
    avg_decision_latency_seconds: float = Field(ge=0.0)
    hours_saved: float = Field(ge=0.0)
    cost_saved: float = Field(ge=0.0)
    minutes_per_case: float = Field(ge=0.0)
    cost_per_hour: float = Field(ge=0.0)


def build_summary(*, from_date: date | None = None, to_date: date | None = None) -> AnalyticsSummary:
    """Aggregate rates and savings over logical runs represented in the audit chain.

    Audit rows appended by approval callbacks share a logical run ID with the
    original row (`RUN-ID#approval:...`) and are grouped to avoid double-counting.
    Date filtering uses the first audit event timestamp for each logical run.
    """
    if from_date is not None and to_date is not None and from_date > to_date:
        raise ValueError("from date must be on or before to date")

    events = get_run_audits()
    grouped: dict[str, list[RunAuditRecord]] = defaultdict(list)
    for event in events:
        grouped[_logical_run_id(event.run_id)].append(event)

    cases: list[list[RunAuditRecord]] = []
    start_bound = _date_start(from_date) if from_date is not None else None
    end_bound = _date_end(to_date) if to_date is not None else None
    for records in grouped.values():
        records.sort(key=lambda row: row.sequence)
        event_times = [_parse_datetime(row.timestamp) for row in records]
        first_event = min((value for value in event_times if value is not None), default=None)
        if first_event is None:
            continue
        if start_bound is not None and first_event < start_bound:
            continue
        if end_bound is not None and first_event >= end_bound:
            continue
        cases.append(records)

    total_runs = len(cases)
    automated_runs = 0
    approval_runs = 0
    escalated_runs = 0
    verification_count = 0
    verification_failures = 0
    rollback_count = 0
    latencies: list[float] = []

    for records in cases:
        decisions = [record.decision.strip().upper() for record in records]
        final_decision = decisions[-1] if decisions else ""
        needs_approval = any(decision in {"APPROVAL_REQUIRED", "APPROVED", "REJECTED"}
                             for decision in decisions)
        if needs_approval:
            approval_runs += 1
        if final_decision == "EXECUTE" and not needs_approval:
            automated_runs += 1
        if final_decision == "ESCALATE":
            escalated_runs += 1

        for record in records:
            for item in record.verification:
                verification_count += 1
                if _verification_failed(item):
                    verification_failures += 1
            rollback_count += sum(_is_rollback(action) for action in record.actions)

        for record in records:
            latency = _decision_latency(record)
            if latency is not None:
                latencies.append(latency)
                break

    minutes_per_case = float(settings.analytics_minutes_per_case)
    cost_per_hour = float(settings.analytics_cost_per_hour)
    hours_saved = automated_runs * minutes_per_case / 60.0
    return AnalyticsSummary(
        from_date=from_date,
        to_date=to_date,
        total_runs=total_runs,
        automation_rate=_rate(automated_runs, total_runs),
        approval_rate=_rate(approval_runs, total_runs),
        escalation_rate=_rate(escalated_runs, total_runs),
        verification_failure_rate=_rate(verification_failures, verification_count),
        rollback_count=rollback_count,
        avg_decision_latency_seconds=(sum(latencies) / len(latencies) if latencies else 0.0),
        hours_saved=hours_saved,
        cost_saved=hours_saved * cost_per_hour,
        minutes_per_case=minutes_per_case,
        cost_per_hour=cost_per_hour,
    )


def _logical_run_id(run_id: str) -> str:
    return run_id.split("#approval:", maxsplit=1)[0]


def _date_start(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _date_end(value: date) -> datetime:
    return datetime.combine(value + timedelta(days=1), time.min, tzinfo=timezone.utc)


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _decision_latency(record: RunAuditRecord) -> float | None:
    snapshot = record.snapshot if isinstance(record.snapshot, dict) else {}
    state = snapshot.get("agent_state", {})
    if not isinstance(state, dict):
        state = {}
    agent_outputs = snapshot.get("agent_outputs", {})
    if not isinstance(agent_outputs, dict):
        agent_outputs = {}
    for source in (snapshot, state, agent_outputs):
        for key in ("decision_latency_seconds", "latency_seconds"):
            try:
                value = float(source[key])
                if value >= 0:
                    return value
            except (KeyError, TypeError, ValueError):
                pass
        for key in ("decision_latency_ms", "latency_ms"):
            try:
                value = float(source[key]) / 1000.0
                if value >= 0:
                    return value
            except (KeyError, TypeError, ValueError):
                pass

    start_value = next((snapshot[key] for key in ("request_started_at", "started_at", "start_time")
                        if snapshot.get(key)), None)
    if start_value is None:
        start_value = next((state[key] for key in ("request_started_at", "started_at", "start_time")
                            if state.get(key)), None)
    if start_value is None:
        start_value = next((agent_outputs[key] for key in ("request_started_at", "started_at", "start_time")
                            if agent_outputs.get(key)), None)
    started_at = _parse_datetime(start_value)
    ended_at = _parse_datetime(record.timestamp)
    if started_at is None or ended_at is None:
        return None
    seconds = (ended_at - started_at).total_seconds()
    return seconds if seconds >= 0 else None


def _verification_failed(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    status = str(item.get("status", "")).upper()
    return status in {"FAILED", "VERIFICATION_FAILED"} or item.get("verified") is False


def _is_rollback(action: Any) -> bool:
    if not isinstance(action, dict):
        return False
    phase = str(action.get("phase", "")).upper()
    kind = str(action.get("type", action.get("kind", ""))).upper()
    return phase in {"COMPENSATE", "ROLLBACK"} or kind in {"COMPENSATION", "ROLLBACK"}


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0
