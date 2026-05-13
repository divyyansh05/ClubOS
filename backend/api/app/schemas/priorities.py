from typing import Any, Optional

from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    severity: float
    persistence: float
    peer_gap: float
    commercial: float
    evidence: float


class HistoricalValue(BaseModel):
    month: str
    value: float


class PeerValue(BaseModel):
    club: str
    value: float


class PriorityCard(BaseModel):
    priority_id: str
    month: str
    title: str
    category: str
    score: float
    rank: int
    asset_name: str
    primary_metric: str
    summary_text: str
    why_it_matters: str
    suggested_next_investigation: str
    # New enriched fields
    consecutive_declining_months: Optional[int] = None
    trend_direction: Optional[str] = None
    trend_slope: Optional[float] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    historical_values: Optional[list[HistoricalValue]] = None
    peer_values: Optional[list[PeerValue]] = None
    peer_median: Optional[float] = None
    peer_leader_value: Optional[float] = None


class PriorityListResponse(BaseModel):
    latest_month: str
    items: list[PriorityCard]


class PriorityDetailResponse(BaseModel):
    priority_id: str
    month: str
    title: str
    category: str
    score: float
    rank: int
    asset_name: str
    primary_metric: str
    summary_text: str
    why_it_matters: str
    suggested_next_investigation: str
    supporting_metrics: dict[str, Any]
    # New enriched fields
    consecutive_declining_months: Optional[int] = None
    trend_direction: Optional[str] = None
    trend_slope: Optional[float] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    historical_values: Optional[list[HistoricalValue]] = None
    peer_values: Optional[list[PeerValue]] = None
    peer_median: Optional[float] = None
    peer_leader_value: Optional[float] = None
