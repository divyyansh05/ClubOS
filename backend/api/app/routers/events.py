from fastapi import APIRouter, HTTPException

from app.schemas.events import EventCreateSchema, EventListResponse, EventSchema
from app.services.event_service import (
    create_event,
    delete_event,
    get_all_events,
    get_events_for_month,
    get_events_near_metric_movement,
)

router = APIRouter()


@router.get("", response_model=EventListResponse)
def list_events(category: str | None = None, year: str | None = None) -> EventListResponse:
    """List all events with optional category and year filters"""
    result = get_all_events()

    # Apply filters
    items = result["items"]

    if category:
        items = [e for e in items if e["event_category"] == category]

    if year:
        items = [e for e in items if e["event_date"].startswith(year)]

    return EventListResponse(
        total_count=len(items),
        items=[EventSchema(**e) for e in items]
    )


@router.get("/{month}", response_model=EventListResponse)
def events_for_month(month: str) -> EventListResponse:
    """Get events for a specific month (format: YYYY-MM)"""
    result = get_events_for_month(month)

    return EventListResponse(
        total_count=result["total_count"],
        items=[EventSchema(**e) for e in result["items"]]
    )


@router.post("", response_model=EventSchema)
def add_event(event: EventCreateSchema) -> EventSchema:
    """Create a new event"""
    new_event = create_event(event.model_dump())
    return EventSchema(**new_event)


@router.delete("/{event_id}")
def remove_event(event_id: str) -> dict:
    """Delete an event"""
    success = delete_event(event_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    return {"message": f"Event {event_id} deleted successfully"}


@router.get("/near/{asset}/{metric}/{month}", response_model=EventListResponse)
def events_near_metric(asset: str, metric: str, month: str) -> EventListResponse:
    """Get events near a metric movement (within 30 days)"""
    result = get_events_near_metric_movement(asset, metric, month)

    return EventListResponse(
        total_count=result["total_count"],
        items=[EventSchema(**e) for e in result["items"]]
    )
