from pydantic import BaseModel
from typing import Optional


class PriorityConnection(BaseModel):
    has_connection: bool
    metric: Optional[str] = None
    rank: Optional[int] = None
    score: Optional[float] = None
    interpretation: str
    border_color: str


class SignalItem(BaseModel):
    signal_id: str
    source_asset: str
    source_metric: str
    target_asset: str
    target_metric: str
    lag_months: int
    relationship_direction: str
    strength_score: float
    validation_status: str
    business_interpretation: str
    last_validated_month: str
    # New enriched fields
    current_status: Optional[str] = None
    status_meaning: Optional[str] = None
    source_trend_direction: Optional[str] = None
    source_current_trend: Optional[float] = None
    source_trend_pct_change: Optional[float] = None
    source_current_value: Optional[float] = None
    target_current_value: Optional[float] = None
    target_health_status: Optional[str] = None
    priority_connection: Optional[PriorityConnection] = None
    # V1.5.5: Driver/Outcome Variable Labelling
    driver_label: str = "Independent Variable (Driver)"
    outcome_label: str = "Dependent Variable (Outcome)"
    causal_direction_statement: Optional[str] = None
    action_statement: Optional[str] = None
    relationship_type: Optional[str] = None
    # V1.6.2: Signal Type Classification
    signal_type: Optional[str] = "internal"
    # V1.8.2: Signal Provisional Flag (Audit Fix 3)
    provisional: bool = False


class SignalResponse(BaseModel):
    latest_validated_month: Optional[str] = None
    items: list[SignalItem]
