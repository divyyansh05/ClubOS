from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from clubos2.watchdog.alerts_repo import AlertsRepository
from clubos2.watchdog.alerts_schema import AlertSeverity
from clubos2.watchdog.orchestrator import run_watchdog, WatchdogRunResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai/watchdog", tags=["ai", "watchdog"])


# ── Trigger endpoint ─────────────────────────────────────────────────────────

class WatchdogRunRequest(BaseModel):
    dedup_window_days: int = Field(default=7, ge=1, le=30)
    top_n: int = Field(default=10, ge=3, le=20)
    triggered_by: str = Field(default="manual")


class WatchdogRunResponse(BaseModel):
    run_id: str
    duration_seconds: float
    metrics_evaluated: int
    rules_fired: int
    alerts_created: int
    alerts_deduped: int
    alert_ids: list[str]
    errors: list[str]


@router.post("/run", response_model=WatchdogRunResponse)
async def trigger_watchdog_run(request: WatchdogRunRequest) -> WatchdogRunResponse:
    """Manually trigger one Watchdog detection cycle.

    Returns run stats including alert IDs. Query alerts at GET /api/ai/watchdog/alerts.

    Phase 3 note: runs synchronously in the request handler (~5s typical).
    TODO Phase 6: add auth + rate limiting before public exposure.
    """
    try:
        result: WatchdogRunResult = await run_watchdog(
            dedup_window_days=request.dedup_window_days,
            top_n=request.top_n,
        )
        return WatchdogRunResponse(
            run_id=result.run_id,
            duration_seconds=result.duration_seconds,
            metrics_evaluated=result.metrics_evaluated,
            rules_fired=result.rules_fired,
            alerts_created=result.alerts_created,
            alerts_deduped=result.alerts_deduped,
            alert_ids=result.alert_ids,
            errors=result.errors,
        )
    except Exception:
        logger.exception("Watchdog trigger endpoint failed")
        raise HTTPException(status_code=500, detail="Internal error running Watchdog")


# ── Alerts query endpoints ────────────────────────────────────────────────────

class AlertsListResponse(BaseModel):
    total: int
    alerts: list[dict]
    filters_applied: dict


@router.get("/alerts", response_model=AlertsListResponse)
async def list_alerts(
    limit: int = 50,
    since_hours: int | None = None,
    metric_name: str | None = None,
    severity: str | None = None,
    run_id: str | None = None,
    unacknowledged_only: bool = False,
) -> AlertsListResponse:
    """Query recent Watchdog alerts with optional filters."""
    repo = AlertsRepository()

    since: datetime | None = None
    if since_hours is not None:
        since = datetime.utcnow() - timedelta(hours=since_hours)

    severity_enum: AlertSeverity | None = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid severity: {severity}. Must be: info, warning, critical")

    alerts = await repo.list_recent(
        limit=limit,
        since=since,
        metric_name=metric_name,
        severity=severity_enum,
    )

    if run_id:
        alerts = [a for a in alerts if a.run_id == run_id]

    if unacknowledged_only:
        alerts = [a for a in alerts if a.acknowledged_at is None]

    return AlertsListResponse(
        total=len(alerts),
        alerts=[a.model_dump(mode="json") for a in alerts],
        filters_applied={
            "limit": limit,
            "since_hours": since_hours,
            "metric_name": metric_name,
            "severity": severity,
            "run_id": run_id,
            "unacknowledged_only": unacknowledged_only,
        },
    )


class AcknowledgeRequest(BaseModel):
    acknowledged_by: str = Field(..., min_length=1, max_length=100)


@router.post("/alerts/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_alert(alert_id: str, request: AcknowledgeRequest) -> dict:
    """Mark an alert as acknowledged. Phase 6 will wire this to Slack approve buttons."""
    repo = AlertsRepository()
    try:
        updated = await repo.acknowledge(alert_id, by_user=request.acknowledged_by)
        return {
            "alert_id": updated.alert_id,
            "acknowledged_at": updated.acknowledged_at.isoformat() if updated.acknowledged_at else None,
            "acknowledged_by": updated.acknowledged_by,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
