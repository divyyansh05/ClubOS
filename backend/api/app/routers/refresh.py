from fastapi import APIRouter

from app.schemas.refresh import RefreshStatusResponse
from app.services.refresh_service import get_refresh_status

router = APIRouter()


@router.get("/status", response_model=RefreshStatusResponse)
def refresh_status() -> RefreshStatusResponse:
    return RefreshStatusResponse(**get_refresh_status())
