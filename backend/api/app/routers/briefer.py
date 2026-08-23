from __future__ import annotations

import logging
from calendar import monthrange
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from clubos2.briefer.agent_schemas import BriefingInput, BriefingRunResult, BriefingType
from clubos2.briefer.orchestrator import run_briefing
from clubos2.briefer.repo import BriefingRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai/briefer", tags=["ai", "briefer"])


class BriefingRunRequest(BaseModel):
    briefing_type: str = Field(default="ad_hoc_summary")
    scope_key: str
    period_start: datetime
    period_end: datetime
    triggered_by: str = Field(default="manual")
    freshness_days: int = Field(default=7, ge=0, le=90)
    force_regenerate: bool = False


@router.post("/run", response_model=BriefingRunResult)
async def run_briefing_endpoint(request: BriefingRunRequest) -> BriefingRunResult:
    """Run a briefing manually. Dedup cache applies unless force_regenerate=True.

    Returns a cached briefing (was_cached=True) if a fresh match exists within
    freshness_days. Force a fresh generation with force_regenerate=True.
    """
    try:
        briefing_type = BriefingType(request.briefing_type)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid briefing_type '{request.briefing_type}'. "
                   f"Valid values: {[t.value for t in BriefingType]}",
        )
    try:
        return await run_briefing(BriefingInput(
            briefing_type=briefing_type,
            scope_key=request.scope_key,
            period_start=request.period_start,
            period_end=request.period_end,
            triggered_by=request.triggered_by,
            freshness_days=request.freshness_days,
            force_regenerate=request.force_regenerate,
        ))
    except Exception:
        logger.exception("Briefing run endpoint failed")
        raise HTTPException(status_code=500, detail="Briefing generation failed")


@router.post("/run_monthly", response_model=BriefingRunResult)
async def run_monthly_briefing_endpoint(
    year_month: str | None = Query(
        default=None,
        description="YYYY-MM (e.g. 2026-03). Defaults to the last complete calendar month.",
    ),
) -> BriefingRunResult:
    """Run a monthly briefing. Designed for cron invocation on the 1st of each month.

    Idempotent: repeated calls for the same year_month return the cached briefing
    without re-generating (dedup cache via scope_key).

    Example: POST /api/ai/briefer/run_monthly?year_month=2026-03
    """
    if year_month is None:
        now = datetime.utcnow()
        first_of_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_of_prev = first_of_this - timedelta(seconds=1)
        year_month = last_of_prev.strftime("%Y-%m")

    try:
        year, month = map(int, year_month.split("-"))
        if not (1 <= month <= 12):
            raise ValueError("month out of range")
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=422, detail=f"Invalid year_month format: {year_month!r}. Expected YYYY-MM.")

    period_start = datetime(year, month, 1)
    last_day = monthrange(year, month)[1]
    period_end = datetime(year, month, last_day, 23, 59, 59)

    try:
        return await run_briefing(BriefingInput(
            briefing_type=BriefingType.MONTHLY_SCHEDULED,
            scope_key=f"monthly:{year_month}",
            period_start=period_start,
            period_end=period_end,
            triggered_by="scheduled_cron",
        ))
    except Exception:
        logger.exception(f"Monthly briefing endpoint failed for {year_month}")
        raise HTTPException(status_code=500, detail="Monthly briefing generation failed")


@router.get("", response_model=list[dict])
async def list_briefings(
    limit: int = Query(default=20, ge=1, le=200),
    briefing_type: str | None = None,
) -> list[dict]:
    """List recent briefings, newest first."""
    repo = BriefingRepository()
    briefings = await repo.list_recent(limit=limit, briefing_type=briefing_type)
    return [b.model_dump(mode="json") for b in briefings]


@router.get("/{briefing_id}", response_model=dict)
async def get_briefing(briefing_id: str) -> dict:
    """Get a single briefing by ID."""
    repo = BriefingRepository()
    briefing = await repo.get_by_id(briefing_id)
    if briefing is None:
        raise HTTPException(status_code=404, detail=f"Briefing {briefing_id} not found")
    return briefing.model_dump(mode="json")
