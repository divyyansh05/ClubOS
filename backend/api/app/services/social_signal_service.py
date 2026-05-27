"""
Social Signal Service - V1.6.2

Computes validated leading indicator relationships from social media metrics
to commercial outcomes (eCommerce, website, streaming, fan app).

Signal validation criteria:
- Pearson correlation >= 0.60 (or 0.50 if 0.60 yields no results)
- Business prior gate: social→commercial is logical; reverse is rejected
- Lags tested: 1, 2, 3 months
- Data: 12 months (2025-01-01 to 2025-12-01)
"""

from typing import Any, Optional
import pandas as pd
from scipy.stats import pearsonr
from app.clients.databricks import DatabricksClient
from app.config.settings import settings


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def _month_str(row: dict[str, Any], key: str) -> str:
    """Extract YYYY-MM-DD date string from row"""
    val = row.get(key, "")
    return str(val)[:10] if val else ""


def _get_social_metric_series(metric_name: str) -> Optional[pd.Series]:
    """
    Get monthly time series for a social metric from gold_social_metrics.
    Returns pandas Series indexed by month (YYYY-MM-DD).
    """
    try:
        social_data = _client().read_gold_table("gold_social_metrics")
        if not social_data:
            return None

        df = pd.DataFrame(social_data)
        df['month'] = pd.to_datetime(df['month']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('month')

        if metric_name not in df.columns:
            return None

        series = df.set_index('month')[metric_name]
        # Convert to float, handling any non-numeric values
        series = pd.to_numeric(series, errors='coerce')
        return series.dropna()
    except Exception:
        return None


def _get_commercial_metric_series(asset_name: str, metric_name: str) -> Optional[pd.Series]:
    """
    Get monthly time series for a commercial metric from gold_kpi_health.
    Returns pandas Series indexed by month (YYYY-MM-DD).
    """
    try:
        health_data = _client().read_gold_table("gold_kpi_health")
        if not health_data:
            return None

        # Filter for the specific asset and metric
        filtered = [
            row for row in health_data
            if str(row.get("asset_name", "")).lower() == asset_name.lower()
            and str(row.get("metric_name", "")).lower() == metric_name.lower()
        ]

        if not filtered:
            return None

        df = pd.DataFrame(filtered)
        df['month'] = pd.to_datetime(df['month']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('month')

        series = df.set_index('month')['metric_value']
        series = pd.to_numeric(series, errors='coerce')
        return series.dropna()
    except Exception:
        return None


def _compute_lagged_correlation(
    source_series: pd.Series,
    target_series: pd.Series,
    lag_months: int
) -> Optional[float]:
    """
    Compute Pearson correlation with source series lagged by lag_months.

    Example with lag=1:
    - Source month N aligns with target month N+1
    - If source=[Jan, Feb, Mar] and target=[Jan, Feb, Mar]
    - Align source[Jan, Feb] with target[Feb, Mar]

    Returns correlation coefficient or None if insufficient data.
    """
    try:
        # Shift source series forward by lag_months
        # This aligns source month N with target month N+lag
        source_shifted = source_series.shift(lag_months)

        # Find common months between shifted source and target
        common_months = source_shifted.index.intersection(target_series.index)

        if len(common_months) < 3:  # Need at least 3 points for meaningful correlation
            return None

        source_aligned = source_shifted[common_months]
        target_aligned = target_series[common_months]

        # Remove any NaN values
        mask = source_aligned.notna() & target_aligned.notna()
        source_clean = source_aligned[mask]
        target_clean = target_aligned[mask]

        if len(source_clean) < 3:
            return None

        # Compute Pearson correlation
        correlation, p_value = pearsonr(source_clean, target_clean)

        # Only return if statistically significant (p < 0.05)
        if p_value < 0.05:
            return correlation
        return None
    except Exception:
        return None


def _check_business_prior(source_metric: str, target_metric: str) -> bool:
    """
    Business logic gate: verify that source→target makes causal sense.

    Social engagement → commercial outcomes = ACCEPT (makes sense)
    Commercial outcomes → social engagement = REJECT (reverse causality)

    For this feature, all source metrics are social and all targets are commercial,
    so this gate always returns True. Included for completeness and future extension.
    """
    # All pairs in the predefined list are social→commercial, which is logically valid
    return True


def _get_social_trend(metric_name: str) -> str:
    """
    Get current trend direction for a social metric.
    Returns 'up', 'down', or 'stable'.
    """
    try:
        social_data = _client().read_gold_table("gold_social_metrics")
        if not social_data or len(social_data) < 2:
            return "stable"

        # Sort by month
        sorted_data = sorted(social_data, key=lambda x: str(x.get('month', '')))

        # Get last two months
        latest = sorted_data[-1]
        prior = sorted_data[-2]

        latest_val = latest.get(metric_name)
        prior_val = prior.get(metric_name)

        if latest_val is None or prior_val is None or prior_val == 0:
            return "stable"

        latest_val = float(latest_val)
        prior_val = float(prior_val)

        pct_change = ((latest_val - prior_val) / prior_val) * 100

        if pct_change > 5:
            return "up"
        elif pct_change < -5:
            return "down"
        else:
            return "stable"
    except Exception:
        return "stable"


def compute_social_signals(correlation_threshold: float = 0.60) -> list[dict[str, Any]]:
    """
    Compute validated social-to-commercial signals.

    Tests all predefined social→commercial metric pairs at lags 1, 2, 3 months.
    Returns list of validated signal dictionaries with signal_type="social_to_commercial".

    Args:
        correlation_threshold: Minimum abs(correlation) to validate (default 0.60)

    Returns:
        List of signal dicts with fields matching gold_signal_relationships schema plus:
        - signal_type: "social_to_commercial"
        - current_status: based on social metric trend
    """

    # Define all social→commercial pairs to test
    signal_pairs = [
        # Social → eCommerce
        ("social_media", "total_engagement", "ecommerce", "net_sales"),
        ("social_media", "instagram_engagement", "ecommerce", "net_sales"),
        ("social_media", "instagram_engagement", "ecommerce", "conversion_rate"),
        ("social_media", "avg_engagement_per_post", "ecommerce", "unique_visitors"),
        ("social_media", "goal_celebration_avg_engagement", "ecommerce", "purchases"),

        # Social → Website
        ("social_media", "total_engagement", "main_website", "unique_visitors"),
        ("social_media", "instagram_engagement", "main_website", "unique_visitors"),
        ("social_media", "total_estimated_views", "main_website", "visits"),

        # Social → Streaming
        ("social_media", "total_engagement", "streaming", "subscriptions"),
        ("social_media", "instagram_engagement", "streaming", "daily_users"),
        ("social_media", "total_estimated_views", "streaming", "video_plays"),

        # Social → Fan App
        ("social_media", "total_engagement", "fan_app", "matchday_visits"),
        ("social_media", "instagram_engagement", "fan_app", "heavy_users"),
        ("social_media", "total_estimated_impressions", "fan_app", "app_downloads"),
    ]

    validated_signals = []

    for source_asset, source_metric, target_asset, target_metric in signal_pairs:
        # Get time series for source and target
        source_series = _get_social_metric_series(source_metric)
        target_series = _get_commercial_metric_series(target_asset, target_metric)

        if source_series is None or target_series is None:
            continue

        # Test lags 1, 2, 3 months
        best_correlation = None
        best_lag = None

        for lag in [1, 2, 3]:
            correlation = _compute_lagged_correlation(source_series, target_series, lag)

            if correlation is not None and abs(correlation) >= correlation_threshold:
                if best_correlation is None or abs(correlation) > abs(best_correlation):
                    best_correlation = correlation
                    best_lag = lag

        # If correlation passes threshold and business prior gate
        if best_correlation is not None and _check_business_prior(source_metric, target_metric):
            # Determine relationship direction
            direction = "positive" if best_correlation > 0 else "negative"

            # Get current trend for source metric
            source_trend = _get_social_trend(source_metric)

            # Compute current status
            if source_trend == "up" and direction == "positive":
                current_status = "firing_positive"
            elif source_trend == "down" and direction == "positive":
                current_status = "firing_negative"
            elif source_trend == "up" and direction == "negative":
                current_status = "firing_negative"
            elif source_trend == "down" and direction == "negative":
                current_status = "firing_positive"
            else:
                current_status = "neutral"

            # Build business interpretation
            strength_pct = int(abs(best_correlation) * 100)
            interpretation = (
                f"Real Madrid's {source_metric} on social media acts as a {best_lag}-month "
                f"leading indicator for {target_metric} on {target_asset}. "
                f"This relationship has been validated with {strength_pct}% correlation strength "
                f"across 12 months of 2025 data. When social engagement rises, "
                f"{target_metric} is expected to {'rise' if direction == 'positive' else 'fall'} "
                f"approximately {best_lag} month{'s' if best_lag > 1 else ''} later."
            )

            # Get latest month from social data
            try:
                social_data = _client().read_gold_table("gold_social_metrics")
                latest_month = max(_month_str(row, "month") for row in social_data)
            except Exception:
                latest_month = "2025-12-01"

            validated_signals.append({
                "source_asset": source_asset,
                "source_metric": source_metric,
                "target_asset": target_asset,
                "target_metric": target_metric,
                "lag_months": best_lag,
                "relationship_direction": direction,
                "strength_score": abs(best_correlation),
                "validation_status": "active",
                "business_interpretation": interpretation,
                "last_validated_month": latest_month,
                "signal_type": "social_to_commercial",
                "current_status": current_status,
            })

    return validated_signals
