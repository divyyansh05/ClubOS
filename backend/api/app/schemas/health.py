from pydantic import BaseModel
from typing import Optional


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
