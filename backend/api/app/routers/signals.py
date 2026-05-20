from typing import Optional
from fastapi import APIRouter, Query

from app.schemas.signals import SignalResponse
from app.services.signal_service import get_signal_view

router = APIRouter()


@router.get("", response_model=SignalResponse)
def signals_view(
    signal_type: Optional[str] = Query(
        None,
        description=(
            "Filter signals by type. Options: 'internal' (traditional cross-platform signals), "
            "'social_to_commercial' (social media as leading indicator for commercial outcomes), "
            "or omit for all signals."
        )
    )
) -> SignalResponse:
    """
    Get all validated leading indicator signals.

    V1.6.2: Now includes social-to-commercial signals alongside internal signals.
    Use the signal_type query parameter to filter results.
    """
    return SignalResponse(**get_signal_view(signal_type_filter=signal_type))
