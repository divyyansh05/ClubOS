from pydantic import BaseModel
from typing import Optional


class BenchmarkPoint(BaseModel):
    month: str
    rm_value: float
    peer_median: float
    peer_leader_value: float
    rm_rank: int
    club_count: int
    gap_to_peer_median: float
    gap_to_leader: float
    rank_change_12m: Optional[int] = None
    gap_change_12m: Optional[float] = None


class BenchmarkResponse(BaseModel):
    asset: str
    metric: str
    latest_month: Optional[str] = None
    points: list[BenchmarkPoint]
