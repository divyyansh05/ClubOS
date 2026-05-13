from fastapi import APIRouter, HTTPException

from app.schemas.priorities import PriorityDetailResponse, PriorityListResponse
from app.services.priority_service import get_latest_priorities, get_priority_detail

router = APIRouter()


@router.get("/latest", response_model=PriorityListResponse)
def latest_priorities() -> PriorityListResponse:
    return PriorityListResponse(**get_latest_priorities())


@router.get("/{priority_id}", response_model=PriorityDetailResponse)
def priority_detail(priority_id: str) -> PriorityDetailResponse:
    try:
        payload = get_priority_detail(priority_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PriorityDetailResponse(**payload)
