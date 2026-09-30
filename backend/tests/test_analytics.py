from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.audit.logger import log_run
from app.api.analytics import analytics_summary
from app.core import database
from app.core.config import settings
from app.analytics.metrics import build_summary


@pytest.fixture
def twenty_audited_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "analytics.sqlite")
    database.init_db()
    monkeypatch.setattr(settings, "analytics_minutes_per_case", 30.0, raising=False)
    monkeypatch.setattr(settings, "analytics_cost_per_hour", 120.0, raising=False)

    first_timestamp = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    decisions = (
        ["EXECUTE"] * 10
        + ["APPROVAL_REQUIRED"] * 4
        + ["ESCALATE"] * 4
        + ["APPROVED"] * 2
    )
    for index, decision in enumerate(decisions):
        timestamp = first_timestamp + timedelta(days=index)
        latency = index + 1
        failed = index < 3
        actions = ([{"phase": "COMPENSATE", "action": {"action_type": "cancel_ticket"}}]
                   if index < 5 else [])
        log_run(
            run_id=f"RUN-{index + 1:02}", prompt=f"Known request {index + 1}",
            evidence_ids=["SOP-042"], policy_rule="known-rule", decision=decision,
            actions=actions,
            verification=[{"status": "FAILED", "verified": False} if failed
                          else {"status": "VERIFIED", "verified": True}],
            timestamp=timestamp,
            snapshot={"request_started_at": (timestamp - timedelta(seconds=latency)).isoformat()},
        )

    # A routed approval appends a decision row for the same logical run.
    log_run(
        run_id="RUN-11#approval:APR-11:approved", prompt="Known request 11",
        evidence_ids=["SOP-042"], policy_rule="known-rule", decision="APPROVED",
        actions=[], verification=[], timestamp=first_timestamp + timedelta(days=20),
        snapshot={"request_started_at": (first_timestamp + timedelta(days=20)).isoformat()},
    )


async def test_summary_metrics_match_hand_calculated_twenty_run_fixture(twenty_audited_runs):
    result = build_summary(from_date=date(2026, 1, 1), to_date=date(2026, 1, 20))
    api_result = await analytics_summary(from_date=date(2026, 1, 1), to_date=date(2026, 1, 20))

    assert api_result == result
    assert result.total_runs == 20
    assert result.automation_rate == pytest.approx(0.50)
    assert result.approval_rate == pytest.approx(0.30)
    assert result.escalation_rate == pytest.approx(0.20)
    assert result.verification_failure_rate == pytest.approx(0.15)
    assert result.rollback_count == 5
    assert result.avg_decision_latency_seconds == pytest.approx(10.5)
    assert result.hours_saved == pytest.approx(5.0)
    assert result.cost_saved == pytest.approx(600.0)
