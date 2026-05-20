from typing import Optional
from fastapi import APIRouter, Query

from app.schemas.benchmark import BenchmarkResponse
from app.schemas.social_benchmark import (
    SocialBenchmarkResponse,
    SocialBenchmarkTrendResponse,
    SocialBenchmarkSummaryResponse,
)
from app.services.benchmark_service import get_benchmark_view
from app.services.social_benchmark_service import (
    get_social_peer_benchmark,
    get_social_benchmark_trend,
    get_social_benchmark_summary,
)

router = APIRouter()


# Social benchmark routes MUST come before /{asset}/{metric} to avoid path conflicts
@router.get("/social/summary", response_model=SocialBenchmarkSummaryResponse)
def social_benchmark_summary_view() -> SocialBenchmarkSummaryResponse:
    """
    Get Real Madrid's position summary across all social benchmark metrics.

    Shows where Real Madrid leads and where it lags vs peer clubs.
    """
    return SocialBenchmarkSummaryResponse(**get_social_benchmark_summary())


@router.get("/social/{metric}/trend", response_model=SocialBenchmarkTrendResponse)
def social_benchmark_trend_view(metric: str) -> SocialBenchmarkTrendResponse:
    """
    Get 12-month ranking trend for Real Madrid on a social metric.

    Shows how Real Madrid's rank has changed over the last 12 months.
    """
    return SocialBenchmarkTrendResponse(**get_social_benchmark_trend(metric))


@router.get("/social/{metric}", response_model=SocialBenchmarkResponse)
def social_benchmark_view(
    metric: str,
    month: Optional[str] = Query(None, description="Month in YYYY-MM-DD format. Defaults to latest month.")
) -> SocialBenchmarkResponse:
    """
    Get peer social benchmark for Real Madrid vs 9 other elite clubs.

    Supported metrics:
    - avg_engagement_per_post (default, most commercially meaningful)
    - total_engagement
    - instagram_engagement_rate
    - posting_frequency
    """
    return SocialBenchmarkResponse(**get_social_peer_benchmark(metric, month_str=month))


# Traditional benchmark route (must come after social routes)
@router.get("/{asset}/{metric}", response_model=BenchmarkResponse)
def benchmark_view(asset: str, metric: str) -> BenchmarkResponse:
    """Get traditional peer benchmark for a commercial metric"""
    return BenchmarkResponse(**get_benchmark_view(asset, metric))
