from fastapi import APIRouter

from app.schemas.briefing import BriefingResponse
from app.services.briefing_service import get_latest_briefing

router = APIRouter()


@router.get("/latest", response_model=BriefingResponse)
def latest_briefing() -> BriefingResponse:
    return BriefingResponse(**get_latest_briefing())
