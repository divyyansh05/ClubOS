from __future__ import annotations
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from clubos2.investigator.orchestrator import InvestigationRunResult, run_investigation
from clubos2.investigator.agent_schemas import InvestigatorInput
from clubos2.investigator.repo import InvestigationRepository
from clubos2.investigator.schema import InvestigationStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai/investigator", tags=["ai", "investigator"])


class InvestigateRequest(BaseModel):
    triggered_by: str = Field(default="manual")
    max_steps: int = Field(default=8, ge=1, le=20)


class InvestigateResponse(BaseModel):
    investigation_id: str
    alert_id: str
    metric_name: str
    status: str
    finding: dict | None
    latency_seconds: float
    trace_url: str | None
    error: str | None


@router.post("/run/{alert_id}", response_model=InvestigateResponse)
async def trigger_investigation(
    alert_id: str, request: InvestigateRequest
) -> InvestigateResponse:
    """Manually trigger an investigation for a specific Watchdog alert.

    Runs synchronously. Typical investigation: 15-45 seconds.
    Future work: move to background task with status polling.
    """
    from clubos2.watchdog.alerts_repo import AlertsRepository
    alerts_repo = AlertsRepository()
    alert = await alerts_repo.get_by_id(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    try:
        result = await run_investigation(
            InvestigatorInput(
                alert_id=alert_id,
                metric_name=alert.metric_name,
                triggered_by=request.triggered_by,
                max_steps=request.max_steps,
            )
        )
        return InvestigateResponse(
            investigation_id=result.investigation_id,
            alert_id=result.alert_id,
            metric_name=result.metric_name,
            status=result.status,
            finding=result.finding.model_dump(mode="json") if result.finding else None,
            latency_seconds=result.latency_seconds,
            trace_url=result.trace_url,
            error=result.error,
        )
    except Exception:
        logger.exception(f"Investigator endpoint failed for alert {alert_id}")
        raise HTTPException(status_code=500, detail="Internal error running investigation")


class InvestigationListResponse(BaseModel):
    total: int
    investigations: list[dict]
    filters_applied: dict


@router.get("", response_model=InvestigationListResponse)
async def list_investigations(
    limit: int = 50,
    metric_name: str | None = None,
    status: str | None = None,
    alert_id: str | None = None,
) -> InvestigationListResponse:
    """Query past investigations."""
    repo = InvestigationRepository()

    if alert_id:
        invs = await repo.get_by_alert(alert_id)
    else:
        status_enum = None
        if status:
            try:
                status_enum = InvestigationStatus(status)
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Invalid status: {status}")
        invs = await repo.list_recent(
            limit=limit, metric_name=metric_name, status=status_enum
        )

    return InvestigationListResponse(
        total=len(invs),
        investigations=[i.model_dump(mode="json") for i in invs],
        filters_applied={
            "limit": limit,
            "metric_name": metric_name,
            "status": status,
            "alert_id": alert_id,
        },
    )


@router.get("/{investigation_id}", response_model=dict)
async def get_investigation(investigation_id: str) -> dict:
    """Get full details of a single investigation."""
    repo = InvestigationRepository()
    inv = await repo.get_by_id(investigation_id)
    if inv is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation {investigation_id} not found",
        )
    return inv.model_dump(mode="json")
