"""
Content Intelligence service for V1.6.4 - Content-to-Commercial Correlation Engine.

Computes lagged correlations between social media content types and commercial outcomes.
Answers: "Does high Goal Celebration engagement correlate with higher eCommerce sales
in the same or following months?"

Lower correlation threshold (0.45) than internal signals (0.60) because content
correlations are noisier — content strategy influences commercial outcomes through
longer causal chains with more confounding factors.
"""

from typing import Optional
import statistics
from scipy.stats import pearsonr
from app.clients.databricks import DatabricksClient
from app.config.settings import settings
from app.schemas.content_intelligence import (
    ContentSignal,
    ContentCommercialSummary,
    ContentIntelligenceResponse,
    ContentMonthlyPerformance
)


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


# Content types available in gold_social_metrics
CONTENT_TYPES = [
    "goal_celebration",
    "training",
    "score_graphic",
    "player_arrival",
    "lineup_graphic",
    "birthday",
    "game_preview"
]

# Commercial metrics to test (metric_name, asset_name tuples)
COMMERCIAL_METRICS = [
    ("net_sales", "ecommerce"),
    ("conversion_rate", "ecommerce"),
    ("unique_visitors", "ecommerce"),
    ("visits", "main_website"),
    ("subscriptions", "streaming"),
    ("daily_users", "fan_app"),
    ("matchday_visits", "fan_app")
]


def compute_content_commercial_correlations() -> list[ContentSignal]:
    """
    Compute correlations between content type engagement and commercial metrics.

    For each content type × commercial metric pair:
    - Test at lag 0, 1, 2 months
    - Compute Pearson correlation
    - If abs(correlation) >= 0.45, record as signal

    Returns:
        List of ContentSignal objects for all correlations exceeding threshold
    """
    # Read data
    social_rows = _client().read_table("gold_social_metrics")
    kpi_rows = _client().read_table("gold_kpi_health")

    # Sort by month
    social_rows = sorted(social_rows, key=lambda r: r.get("month", ""))
    kpi_rows = sorted(kpi_rows, key=lambda r: r.get("month", ""))

    signals = []

    for content_type in CONTENT_TYPES:
        content_field = f"{content_type}_avg_engagement"

        # Extract content engagement time series
        content_values = []
        content_months = []
        for row in social_rows:
            val = row.get(content_field)
            if val is not None and val > 0:
                content_values.append(float(val))
                content_months.append(row.get("month"))

        if len(content_values) < 6:
            continue  # Not enough data

        avg_content_engagement = statistics.mean(content_values)

        for metric_name, asset_name in COMMERCIAL_METRICS:
            # Extract commercial metric time series
            commercial_values = []
            commercial_months = []
            for row in kpi_rows:
                if row.get("asset_name") == asset_name and row.get("metric_name") == metric_name:
                    val = row.get("metric_value")
                    if val is not None:
                        commercial_values.append(float(val))
                        commercial_months.append(row.get("month"))

            if len(commercial_values) < 6:
                continue

            # Test at lag 0, 1, 2 months
            for lag in [0, 1, 2]:
                # Align time series with lag
                aligned_content = []
                aligned_commercial = []

                for i, c_month in enumerate(content_months):
                    # Find commercial value at content_month + lag
                    try:
                        lag_idx = commercial_months.index(c_month) + lag
                        if lag_idx < len(commercial_months):
                            aligned_content.append(content_values[i])
                            aligned_commercial.append(commercial_values[lag_idx])
                    except (ValueError, IndexError):
                        continue

                if len(aligned_content) < 6:
                    continue  # Not enough overlapping data

                # Compute Pearson correlation
                try:
                    corr, p_value = pearsonr(aligned_content, aligned_commercial)
                except:
                    continue

                # Threshold check
                if abs(corr) < 0.45:
                    continue

                # Determine strength label
                abs_corr = abs(corr)
                if abs_corr > 0.65:
                    strength_label = "Strong"
                elif abs_corr >= 0.55:
                    strength_label = "Moderate"
                else:
                    strength_label = "Weak"

                # Direction
                direction = "positive" if corr > 0 else "negative"

                # Generate interpretation
                interpretation = _generate_interpretation(
                    content_type,
                    metric_name,
                    asset_name,
                    direction,
                    lag,
                    corr,
                    avg_content_engagement
                )

                signals.append(ContentSignal(
                    content_type=content_type,
                    commercial_metric=metric_name,
                    commercial_asset=asset_name,
                    correlation=corr,
                    lag_months=lag,
                    direction=direction,
                    interpretation=interpretation,
                    strength_label=strength_label,
                    confidence_note="Based on 12 months of data — provisional",
                    avg_content_engagement=avg_content_engagement,
                    sample_size_months=len(aligned_content)
                ))

    # Sort by absolute correlation strength
    signals = sorted(signals, key=lambda s: abs(s.correlation), reverse=True)

    return signals


def _generate_interpretation(
    content_type: str,
    metric: str,
    asset: str,
    direction: str,
    lag: int,
    correlation: float,
    avg_engagement: float
) -> str:
    """
    Generate business-readable interpretation of a content-to-commercial correlation.

    For positive correlations: "tends to be HIGHER than usual"
    For negative correlations: "tends to be LOWER than usual" (NOT "tends to be negative")
    """
    content_label = content_type.replace("_", " ").title()

    # Clear directional language — avoids "tends to be negative" mistake
    if direction == "positive":
        direction_phrase = "tends to be HIGHER than usual"
    else:
        direction_phrase = "tends to be LOWER than usual"

    lag_text = "in the same month" if lag == 0 else f"{lag} month{'s' if lag > 1 else ''} later"

    # Context-specific interpretations
    if content_type == "goal_celebration":
        context = f"When Goal Celebration posts generate high engagement in a given month, {metric} on {asset} {direction_phrase} {lag_text}. (Correlation: {correlation:.2f}, {abs(correlation):.0%} strength)"
    elif content_type == "birthday":
        context = f"When Birthday posts generate high engagement, {metric} on {asset} {direction_phrase} {lag_text}. (Correlation: {correlation:.2f})"
    elif content_type == "score_graphic":
        context = f"When Score Graphic posts generate high engagement, {metric} on {asset} {direction_phrase} {lag_text}. These posts spike on matchdays. (Correlation: {correlation:.2f})"
    elif content_type == "lineup_graphic":
        context = f"When Lineup Graphic posts generate high engagement, {metric} on {asset} {direction_phrase} {lag_text}. (Correlation: {correlation:.2f})"
    elif content_type == "game_preview":
        context = f"When Game Preview content generates high engagement, {metric} on {asset} {direction_phrase} {lag_text}. (Correlation: {correlation:.2f})"
    elif content_type == "training":
        context = f"When Training content generates high engagement, {metric} on {asset} {direction_phrase} {lag_text}. (Correlation: {correlation:.2f})"
    else:
        context = f"When {content_label} posts generate high engagement, {metric} on {asset} {direction_phrase} {lag_text}. (Correlation: {correlation:.2f})"

    return context


def get_content_commercial_summary() -> ContentCommercialSummary:
    """
    Get summary of strongest content-to-commercial relationships.

    Returns:
        ContentCommercialSummary with top signal and aggregate stats
    """
    signals = compute_content_commercial_correlations()

    if not signals:
        return ContentCommercialSummary(
            strongest_signal=None,
            total_correlations_found=0,
            avg_correlation_strength=0.0,
            most_predictive_content_type="none",
            most_influenced_commercial_metric="none"
        )

    # Strongest signal
    strongest = signals[0]

    # Avg correlation strength
    avg_corr = statistics.mean([abs(s.correlation) for s in signals])

    # Most predictive content type (appears in most correlations)
    content_counts = {}
    for s in signals:
        content_counts[s.content_type] = content_counts.get(s.content_type, 0) + 1
    most_predictive_content = max(content_counts, key=content_counts.get)

    # Most influenced commercial metric
    metric_counts = {}
    for s in signals:
        key = f"{s.commercial_metric}"
        metric_counts[key] = metric_counts.get(key, 0) + 1
    most_influenced_metric = max(metric_counts, key=metric_counts.get)

    return ContentCommercialSummary(
        strongest_signal=strongest,
        total_correlations_found=len(signals),
        avg_correlation_strength=avg_corr,
        most_predictive_content_type=most_predictive_content,
        most_influenced_commercial_metric=most_influenced_metric
    )


def get_content_performance_by_month(month_str: str) -> ContentMonthlyPerformance:
    """
    Get content performance breakdown for a specific month with commercial context.

    Args:
        month_str: Month in YYYY-MM format

    Returns:
        ContentMonthlyPerformance with content/commercial breakdown
    """
    month_iso = f"{month_str}-01"

    # Read data
    social_rows = _client().read_table("gold_social_metrics")
    kpi_rows = _client().read_table("gold_kpi_health")

    # Find month
    social_row = next((r for r in social_rows if r.get("month") == month_iso), None)
    if not social_row:
        raise ValueError(f"No social data for month {month_str}")

    # Extract content performances
    content_performances = []
    for content_type in CONTENT_TYPES:
        field = f"{content_type}_avg_engagement"
        avg_engagement = social_row.get(field, 0)
        content_performances.append({
            "content_type": content_type.replace("_", " ").title(),
            "avg_engagement": avg_engagement
        })

    # Sort by engagement
    content_performances = sorted(
        content_performances,
        key=lambda x: x["avg_engagement"],
        reverse=True
    )

    # Extract commercial outcomes for this month
    commercial_outcomes = []
    for metric_name, asset_name in COMMERCIAL_METRICS:
        kpi_row = next((
            r for r in kpi_rows
            if r.get("month") == month_iso
            and r.get("asset_name") == asset_name
            and r.get("metric_name") == metric_name
        ), None)

        if kpi_row:
            value = kpi_row.get("metric_value", 0)
            baseline = kpi_row.get("seasonal_baseline")
            vs_baseline_pct = None
            if baseline and baseline > 0:
                vs_baseline_pct = ((value - baseline) / baseline) * 100

            commercial_outcomes.append({
                "metric": metric_name,
                "asset": asset_name,
                "value": value,
                "vs_baseline_pct": vs_baseline_pct
            })

    # Find matching correlations
    signals = compute_content_commercial_correlations()
    matching_correlations = []
    for signal in signals[:5]:  # Top 5
        matching_correlations.append(signal.interpretation)

    return ContentMonthlyPerformance(
        month=month_iso,
        content_performances=content_performances,
        commercial_outcomes=commercial_outcomes,
        matching_correlations=matching_correlations
    )


def get_content_intelligence_full() -> ContentIntelligenceResponse:
    """
    Get full content intelligence report with all signals and summary.

    Returns:
        ContentIntelligenceResponse with complete analysis
    """
    signals = compute_content_commercial_correlations()
    summary = get_content_commercial_summary()

    # Get latest month from social data
    social_rows = _client().read_table("gold_social_metrics")
    social_rows_sorted = sorted(social_rows, key=lambda r: r.get("month", ""), reverse=True)
    latest_month = social_rows_sorted[0].get("month") if social_rows_sorted else "unknown"

    return ContentIntelligenceResponse(
        latest_month=latest_month,
        signals=signals,
        summary=summary
    )
