from fastapi import APIRouter

from app.schemas.health import HealthCheckResponse, HealthSummaryResponse
from app.services.health_service import get_latest_health_summary

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
def healthcheck() -> HealthCheckResponse:
    return HealthCheckResponse(status="ok", service="clubos-api")


@router.get("/health/summary", response_model=HealthSummaryResponse)
def health_summary() -> HealthSummaryResponse:
    return HealthSummaryResponse(**get_latest_health_summary())
