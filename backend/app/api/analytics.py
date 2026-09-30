"""Audit-derived workflow analytics endpoints."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.analytics.metrics import AnalyticsSummary, build_summary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> AnalyticsSummary:
    """Summarize audit outcomes over an inclusive UTC date range."""
    try:
        return build_summary(from_date=from_date, to_date=to_date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
