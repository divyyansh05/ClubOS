from fastapi import APIRouter

from app.schemas.signals import SignalResponse
from app.services.signal_service import get_signal_view

router = APIRouter()


@router.get("", response_model=SignalResponse)
def signals_view() -> SignalResponse:
    return SignalResponse(**get_signal_view())
