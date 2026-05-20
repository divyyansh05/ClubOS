from fastapi import APIRouter

from app.schemas.health import HealthCheckResponse, HealthSummaryResponse, AssetHealthBreakdownResponse
from app.services.health_service import get_latest_health_summary, get_asset_health_breakdown

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
def healthcheck() -> HealthCheckResponse:
    return HealthCheckResponse(status="ok", service="clubos-api")


@router.get("/health/summary", response_model=HealthSummaryResponse)
def health_summary() -> HealthSummaryResponse:
    return HealthSummaryResponse(**get_latest_health_summary())


@router.get("/health/assets", response_model=AssetHealthBreakdownResponse)
def asset_health_breakdown() -> AssetHealthBreakdownResponse:
    """Get health status breakdown by asset (V1.6.1)."""
    return AssetHealthBreakdownResponse(assets=get_asset_health_breakdown())
