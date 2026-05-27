from typing import Optional, List, Dict
from fastapi import APIRouter, Query
import pandas as pd

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
from app.config.settings import settings

router = APIRouter()


@router.get("/available-metrics", response_model=List[Dict[str, str]])
def available_metrics_view() -> List[Dict[str, str]]:
    """
    Get list of metrics that have peer benchmark data available.

    Returns only metrics that actually exist in gold_peer_benchmark.csv,
    preventing users from selecting metrics with no data.

    Each item includes:
    - asset_name: The asset identifier (ecommerce, main_website, etc)
    - metric_name: The metric identifier (conversion_rate, bounce_rate, etc)
    - label: Human-readable metric label
    - asset_label: Human-readable asset label
    """
    import json
    from pathlib import Path

    # Read benchmark CSV to get available combinations
    benchmark_csv = Path(settings.clubos_gold_snapshot_dir) / "gold_peer_benchmark.csv"

    if not benchmark_csv.exists():
        return []

    df = pd.read_csv(benchmark_csv)

    # Get distinct asset/metric pairs
    distinct_pairs = df[['asset_name', 'metric_name']].drop_duplicates().sort_values(['asset_name', 'metric_name'])

    # Read metric dictionary for labels
    dictionary_path = Path(settings.clubos_gold_snapshot_dir) / "metric_dictionary.json"
    metric_labels = {}

    if dictionary_path.exists():
        with open(dictionary_path, 'r') as f:
            metric_dict = json.load(f)
            metric_labels = {m['metric_name']: m['label'] for m in metric_dict.get('metrics', [])}

    # Asset label mapping
    asset_labels = {
        'ecommerce': 'eCommerce',
        'main_website': 'Main Website',
        'streaming': 'Streaming',
        'fan_app': 'Fan App',
        'social_media': 'Social Media',
    }

    # Build result list
    result = []
    for _, row in distinct_pairs.iterrows():
        asset = row['asset_name']
        metric = row['metric_name']
        result.append({
            'asset_name': asset,
            'metric_name': metric,
            'label': metric_labels.get(metric, metric.replace('_', ' ').title()),
            'asset_label': asset_labels.get(asset, asset.replace('_', ' ').title()),
        })

    return result


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
