"""
Social Benchmark Schemas - V1.6.3

Pydantic schemas for social media peer benchmarking endpoints.
"""

from typing import Optional
from pydantic import BaseModel


class SocialBenchmarkEntry(BaseModel):
    """Single club's data point for a metric"""
    club: str
    value: float
    rank: int
    is_real_madrid: bool


class SocialBenchmarkResponse(BaseModel):
    """Response for GET /benchmark/social/{metric}"""
    metric: str
    month: Optional[str] = None
    clubs: list[SocialBenchmarkEntry]
    rm_rank: Optional[int] = None
    rm_value: Optional[float] = None
    peer_median: Optional[float] = None
    peer_leader_club: Optional[str] = None
    peer_leader_value: Optional[float] = None
    gap_to_median: Optional[float] = None
    gap_to_leader: Optional[float] = None
    club_count: int


class SocialBenchmarkTrendPoint(BaseModel):
    """Single month's ranking data"""
    month: str
    rm_rank: Optional[int] = None
    rm_value: Optional[float] = None


class SocialBenchmarkTrendResponse(BaseModel):
    """Response for GET /benchmark/social/{metric}/trend"""
    metric: str
    months: list[SocialBenchmarkTrendPoint]


class SocialBenchmarkMetricSummary(BaseModel):
    """Summary for one metric"""
    metric: str
    rm_rank: Optional[int] = None
    rm_value: Optional[float] = None
    peer_median: Optional[float] = None
    gap_to_median: Optional[float] = None
    status: str  # "leader", "above_median", "below_median"


class SocialBenchmarkSummaryResponse(BaseModel):
    """Response for GET /benchmark/social/summary"""
    latest_month: Optional[str] = None
    metrics: list[SocialBenchmarkMetricSummary]
