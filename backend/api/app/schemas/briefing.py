from pydantic import BaseModel
from typing import Optional


class BriefingPriority(BaseModel):
    priority_id: str
    priority_rank: int
    priority_title: str
    priority_category: str
    priority_score: float


class BriefingAnomaly(BaseModel):
    anomaly_rank: int
    asset_name: str
    metric_name: str
    metric_value: float
    deviation_from_seasonal_baseline: float


class BriefingSignal(BaseModel):
    signal_rank: int
    signal_id: str
    source_asset: str
    source_metric: str
    target_asset: str
    target_metric: str
    lag_months: int
    relationship_direction: str
    strength_score: float


class BriefingBenchmarkSummary(BaseModel):
    benchmarked_metric_count: int
    benchmark_underperformance_count: int
    avg_gap_to_peer_median: float
    worst_gap_to_peer_median: float


class BriefingHealthSummary(BaseModel):
    metric_count: int
    good_count: int
    review_count: int
    stable_count: int
    avg_abs_deviation: float


class BriefingResponse(BaseModel):
    month: str
    top_priorities: list[BriefingPriority]
    top_anomalies: list[BriefingAnomaly]
    strongest_signals: list[BriefingSignal]
    benchmark_summary: Optional[BriefingBenchmarkSummary] = None
    health_summary: Optional[BriefingHealthSummary] = None
