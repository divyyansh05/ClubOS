from typing import Any, Optional

from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    # Raw component scores (0-1 range)
    severity: float
    persistence: float
    peer_gap: float
    commercial: float
    evidence: float
    # Weighted contributions (what goes into final score)
    severity_contribution: float
    persistence_contribution: float
    peer_gap_contribution: float
    commercial_contribution: float
    evidence_contribution: float


class HistoricalValue(BaseModel):
    month: str
    value: float


class PeerValue(BaseModel):
    club: str
    value: float
    is_estimated: bool = False


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
    # Event-adjusted anomaly detection (V1.5.2)
    anomaly_context: Optional[dict[str, Any]] = None
    event_suppressed: Optional[bool] = None
    # Seasonal baseline intelligence (V1.5.3)
    seasonal_context: Optional[dict[str, Any]] = None
    # Conversion rate volume pairing (V1.5.4)
    conversion_context: Optional[dict[str, Any]] = None


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
    # Event-adjusted anomaly detection (V1.5.2)
    anomaly_context: Optional[dict[str, Any]] = None
    event_suppressed: Optional[bool] = None
    # Seasonal baseline intelligence (V1.5.3)
    seasonal_context: Optional[dict[str, Any]] = None
    # Conversion rate volume pairing (V1.5.4)
    conversion_context: Optional[dict[str, Any]] = None
