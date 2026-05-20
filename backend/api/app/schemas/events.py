from typing import Optional
from pydantic import BaseModel


class EventSchema(BaseModel):
    event_id: str
    event_date: str  # ISO 8601 date string
    event_name: str
    event_category: str
    event_description: str
    expected_impact: str  # Comma-separated list of affected assets
    affected_assets: list[str]  # Parsed from expected_impact
    impact_magnitude: str  # 'high', 'medium', 'low'


class EventCreateSchema(BaseModel):
    event_date: str
    event_name: str
    event_category: str
    event_description: str
    expected_impact: str  # Comma-separated asset names
    impact_magnitude: str


class EventListResponse(BaseModel):
    total_count: int
    items: list[EventSchema]
