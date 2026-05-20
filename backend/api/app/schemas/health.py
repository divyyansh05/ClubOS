from pydantic import BaseModel
from typing import Optional, Dict


class HealthCheckResponse(BaseModel):
    status: str
    service: str


class HealthSummaryResponse(BaseModel):
    latest_month: str
    metric_count: int
    good_count: int
    review_count: int
    stable_count: int
    avg_abs_deviation: Optional[float] = None


class AssetHealthStats(BaseModel):
    """Health statistics for a single asset."""
    metric_count: int
    good_count: int
    review_count: int
    stable_count: int
    health_percentage: float


class AssetHealthBreakdownResponse(BaseModel):
    """Per-asset health breakdown (V1.6.1)."""
    assets: Dict[str, AssetHealthStats]
