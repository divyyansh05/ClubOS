"""
Social media metrics service for V1.6.1 - Fifth Digital Platform.

Reads from gold_social_metrics table (CSV snapshot or Databricks live mode).

V1.6.5 additions: Social anomaly detection for event confirmation workflow.
V1.6.6 additions: International audience intelligence and commercial correlation.
"""

from typing import Optional
import statistics
from scipy.stats import pearsonr
from app.clients.databricks import DatabricksClient
from app.config.settings import settings
from app.schemas.social import (
    SocialMetricsMonthly,
    SocialSummaryResponse,
    SocialPlatformBreakdown,
    SocialPlatformBreakdownResponse,
    SocialContentPerformance,
    SocialContentPerformanceResponse,
    SocialMonthlyTrendResponse,
    SocialAnomaly
)
from app.services import event_service


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def get_social_metrics(month_str: Optional[str] = None) -> list[dict]:
    """
    Get social media metrics, optionally filtered to a specific month.

    Args:
        month_str: Optional month filter in YYYY-MM format

    Returns:
        List of monthly metric rows as dicts
    """
    rows = _client().read_table("gold_social_metrics")

    if month_str:
        # Convert YYYY-MM to YYYY-MM-01 for comparison
        month_filter = f"{month_str}-01"
        rows = [r for r in rows if r.get("month") == month_filter]

    return rows


def get_social_summary() -> SocialSummaryResponse:
    """
    Get latest month summary with MoM comparison.

    Returns:
        SocialSummaryResponse with key metrics and changes
    """
    rows = get_social_metrics()

    if not rows:
        raise ValueError("No social metrics data available")

    # Sort by month descending
    rows_sorted = sorted(rows, key=lambda r: r.get("month", ""), reverse=True)

    latest = rows_sorted[0]
    prior = rows_sorted[1] if len(rows_sorted) > 1 else None

    def compute_mom_change(current, previous):
        if previous is None or previous == 0:
            return None
        return ((current - previous) / previous) * 100

    # Extract values
    total_engagement = latest.get("total_engagement", 0)
    avg_engagement_per_post = latest.get("avg_engagement_per_post", 0)
    instagram_engagement_rate = latest.get("instagram_engagement_rate", 0)
    international_engagement_ratio = latest.get("international_engagement_ratio", 0)

    # Compute MoM changes
    total_engagement_mom_change = None
    avg_engagement_per_post_mom_change = None
    instagram_engagement_rate_mom_change = None
    international_engagement_ratio_mom_change = None

    if prior:
        total_engagement_mom_change = compute_mom_change(
            total_engagement,
            prior.get("total_engagement", 0)
        )
        avg_engagement_per_post_mom_change = compute_mom_change(
            avg_engagement_per_post,
            prior.get("avg_engagement_per_post", 0)
        )
        instagram_engagement_rate_mom_change = compute_mom_change(
            instagram_engagement_rate,
            prior.get("instagram_engagement_rate", 0)
        )
        international_engagement_ratio_mom_change = compute_mom_change(
            international_engagement_ratio,
            prior.get("international_engagement_ratio", 0)
        )

    return SocialSummaryResponse(
        latest_month=latest.get("month"),
        total_engagement=total_engagement,
        total_engagement_mom_change=total_engagement_mom_change,
        avg_engagement_per_post=avg_engagement_per_post,
        avg_engagement_per_post_mom_change=avg_engagement_per_post_mom_change,
        instagram_engagement_rate=instagram_engagement_rate,
        instagram_engagement_rate_mom_change=instagram_engagement_rate_mom_change,
        international_engagement_ratio=international_engagement_ratio,
        international_engagement_ratio_mom_change=international_engagement_ratio_mom_change,
        total_posts=latest.get("total_posts", 0),
        top_performing_platform=latest.get("top_performing_platform", "unknown"),
        top_performing_content_type=latest.get("top_performing_content_type", "unknown")
    )


def get_social_platform_breakdown(month_str: str) -> SocialPlatformBreakdownResponse:
    """
    Get per-platform breakdown for a specific month.

    Args:
        month_str: Month in YYYY-MM format

    Returns:
        SocialPlatformBreakdownResponse with platform details
    """
    rows = get_social_metrics(month_str)

    if not rows:
        raise ValueError(f"No data for month {month_str}")

    row = rows[0]
    month_iso = row.get("month")

    platforms = []

    # Instagram
    platforms.append(SocialPlatformBreakdown(
        platform="instagram",
        posts=row.get("instagram_posts", 0),
        engagement=row.get("instagram_engagement", 0),
        avg_engagement=row.get("instagram_avg_engagement", 0),
        engagement_rate=row.get("instagram_engagement_rate", 0)
    ))

    # TikTok
    platforms.append(SocialPlatformBreakdown(
        platform="tiktok",
        posts=row.get("tiktok_posts", 0),
        engagement=row.get("tiktok_engagement", 0),
        avg_engagement=row.get("tiktok_avg_engagement", 0),
        engagement_rate=row.get("tiktok_engagement_rate", 0)
    ))

    # X (Twitter)
    platforms.append(SocialPlatformBreakdown(
        platform="x",
        posts=row.get("x_posts", 0),
        engagement=row.get("x_engagement", 0),
        avg_engagement=row.get("x_avg_engagement", 0),
        engagement_rate=row.get("x_engagement_rate", 0)
    ))

    # Facebook
    platforms.append(SocialPlatformBreakdown(
        platform="facebook",
        posts=row.get("facebook_posts", 0),
        engagement=row.get("facebook_engagement", 0),
        avg_engagement=row.get("facebook_avg_engagement", 0),
        engagement_rate=row.get("facebook_engagement_rate", 0)
    ))

    # YouTube
    platforms.append(SocialPlatformBreakdown(
        platform="youtube",
        posts=row.get("youtube_posts", 0),
        engagement=row.get("youtube_engagement", 0),
        avg_engagement=row.get("youtube_avg_engagement", 0),
        engagement_rate=None  # YouTube engagement rate not computed
    ))

    return SocialPlatformBreakdownResponse(
        month=month_iso,
        platforms=platforms
    )


def get_social_content_performance(month_str: str) -> SocialContentPerformanceResponse:
    """
    Get content type performance for a specific month.

    Args:
        month_str: Month in YYYY-MM format

    Returns:
        SocialContentPerformanceResponse with content type stats
    """
    rows = get_social_metrics(month_str)

    if not rows:
        raise ValueError(f"No data for month {month_str}")

    row = rows[0]
    month_iso = row.get("month")

    content_types = [
        SocialContentPerformance(
            content_type="Goal Celebration",
            avg_engagement=row.get("goal_celebration_avg_engagement", 0)
        ),
        SocialContentPerformance(
            content_type="Training",
            avg_engagement=row.get("training_avg_engagement", 0)
        ),
        SocialContentPerformance(
            content_type="Score Graphic",
            avg_engagement=row.get("score_graphic_avg_engagement", 0)
        ),
        SocialContentPerformance(
            content_type="Player Arrival",
            avg_engagement=row.get("player_arrival_avg_engagement", 0)
        ),
        SocialContentPerformance(
            content_type="Lineup Graphic",
            avg_engagement=row.get("lineup_graphic_avg_engagement", 0)
        ),
        SocialContentPerformance(
            content_type="Birthday",
            avg_engagement=row.get("birthday_avg_engagement", 0)
        ),
        SocialContentPerformance(
            content_type="Game Preview",
            avg_engagement=row.get("game_preview_avg_engagement", 0)
        )
    ]

    # Sort by avg_engagement descending
    content_types_sorted = sorted(
        content_types,
        key=lambda ct: ct.avg_engagement,
        reverse=True
    )

    return SocialContentPerformanceResponse(
        month=month_iso,
        content_types=content_types_sorted
    )


def get_social_monthly_trend() -> SocialMonthlyTrendResponse:
    """
    Get all 12 months trend data for charts.

    Returns:
        SocialMonthlyTrendResponse with time series arrays
    """
    rows = get_social_metrics()

    if not rows:
        raise ValueError("No social metrics data available")

    # Sort chronologically
    rows_sorted = sorted(rows, key=lambda r: r.get("month", ""))

    months = [r.get("month") for r in rows_sorted]
    total_engagement = [r.get("total_engagement", 0) for r in rows_sorted]
    avg_engagement_per_post = [r.get("avg_engagement_per_post", 0) for r in rows_sorted]
    total_posts = [r.get("total_posts", 0) for r in rows_sorted]

    return SocialMonthlyTrendResponse(
        months=months,
        total_engagement=total_engagement,
        avg_engagement_per_post=avg_engagement_per_post,
        total_posts=total_posts
    )


# V1.6.5 — Social Anomaly Detection for Event Confirmation

# Metrics to monitor for anomalies
ANOMALY_METRICS = [
    "total_engagement",
    "avg_engagement_per_post",
    "instagram_engagement",
    "tiktok_engagement",
    "x_engagement",
    "goal_celebration_avg_engagement",
    "birthday_avg_engagement",
    "score_graphic_avg_engagement"
]


def detect_social_anomalies() -> list[SocialAnomaly]:
    """
    Detect social media anomalies (spikes/drops >2 std from mean).

    Returns list of SocialAnomaly objects with month, metric, z-score,
    likely cause classification, and candidate event details.
    """
    rows = get_social_metrics()

    if len(rows) < 3:
        return []  # Need at least 3 months for meaningful stats

    anomalies = []

    for metric in ANOMALY_METRICS:
        # Extract metric values
        values = [row.get(metric, 0) for row in rows if row.get(metric) is not None]

        if len(values) < 3:
            continue

        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0

        if std_val == 0:
            continue  # No variation

        # Check each month for anomalies
        for row in rows:
            actual_val = row.get(metric, 0)
            if actual_val is None:
                continue

            z_score = (actual_val - mean_val) / std_val if std_val > 0 else 0

            if abs(z_score) > 2.0:
                month = row.get("month", "")

                # Classify direction
                direction = "spike" if z_score > 0 else "drop"

                # Classify likely cause based on metric combination
                likely_cause, candidate_category = _classify_anomaly_cause(row, metric, direction)

                # Generate candidate event name
                month_label = month[:7] if len(month) >= 7 else month  # YYYY-MM
                candidate_event_name = f"{month_label} Social {direction.title()} — {likely_cause.replace('_', ' ').title()}"

                # Determine confidence level
                confidence_level = "high" if abs(z_score) > 3.0 else "medium" if abs(z_score) > 2.5 else "low"

                anomalies.append(SocialAnomaly(
                    month=month,
                    metric=metric,
                    actual_value=actual_val,
                    mean_value=mean_val,
                    std_value=std_val,
                    z_score=z_score,
                    direction=direction,
                    likely_cause=likely_cause,
                    candidate_event_name=candidate_event_name,
                    candidate_category=candidate_category,
                    is_confirmed=False,
                    confidence_level=confidence_level
                ))

    # Sort by abs z_score descending (most anomalous first)
    anomalies.sort(key=lambda a: abs(a.z_score), reverse=True)

    return anomalies


def _classify_anomaly_cause(row: dict, anomaly_metric: str, direction: str) -> tuple[str, str]:
    """
    Classify likely cause of social anomaly based on metric patterns.

    Returns (likely_cause, candidate_category) tuple.
    """
    # Extract key metrics for classification
    goal_celebration = row.get("goal_celebration_avg_engagement", 0)
    birthday = row.get("birthday_avg_engagement", 0)
    score_graphic = row.get("score_graphic_avg_engagement", 0)
    x_engagement = row.get("x_engagement", 0)
    instagram_engagement = row.get("instagram_engagement", 0)
    total_engagement = row.get("total_engagement", 0)

    # Compute baseline averages for comparison (rough heuristic)
    # These are typical values from the data
    goal_celebration_baseline = 100000
    birthday_baseline = 150000

    if direction == "spike":
        # Match result win / Trophy win
        if "goal_celebration" in anomaly_metric or (
            goal_celebration > goal_celebration_baseline * 1.5 and total_engagement > 350000000
        ):
            return ("match_result_win", "match_result_win")

        # Birthday posts spike
        if "birthday" in anomaly_metric or birthday > birthday_baseline * 2:
            return ("media_event", "media_event")

        # Score graphic spike (post-match content)
        if "score_graphic" in anomaly_metric or score_graphic > 120000:
            return ("match_result_win", "match_result_win")

        # X/Twitter spike without goal celebration (likely injury/news)
        if "x_engagement" in anomaly_metric and goal_celebration < goal_celebration_baseline:
            return ("injury_news", "injury_news")

        # Instagram spike without goal celebration (player signing/media event)
        if "instagram" in anomaly_metric and goal_celebration < goal_celebration_baseline:
            return ("player_signing", "player_signing")

        # General engagement spike
        return ("media_event", "media_event")

    else:  # drop
        # Drop in goal celebration (poor match result)
        if "goal_celebration" in anomaly_metric:
            return ("match_result_loss", "match_result_loss")

        # X/Twitter drop (injury news depresses engagement)
        if "x_engagement" in anomaly_metric:
            return ("injury_news", "injury_news")

        # General drop
        return ("poor_match_result", "match_result_loss")


def check_if_event_exists_for_anomaly(month_str: str, likely_cause: str) -> bool:
    """
    Check if an event matching the anomaly already exists in gold_events.csv.

    Args:
        month_str: Month in YYYY-MM-DD or YYYY-MM format
        likely_cause: Anomaly classification (e.g., "match_result_win")

    Returns:
        True if matching event exists, False otherwise
    """
    # Normalize month to YYYY-MM for comparison
    if len(month_str) > 7:
        month_prefix = month_str[:7]
    else:
        month_prefix = month_str

    # Get events for this month
    result = event_service.get_events_for_month(month_prefix)
    events = result.get("items", [])

    # Check if any event matches the likely cause category
    for event in events:
        if event.get("event_category") == likely_cause:
            return True

    return False


def get_unconfirmed_social_anomalies() -> list[SocialAnomaly]:
    """
    Get social anomalies that don't have matching events in the calendar yet.

    Returns:
        List of unconfirmed anomalies (no event registered for that month/type)
    """
    all_anomalies = detect_social_anomalies()

    unconfirmed = []
    for anomaly in all_anomalies:
        if not check_if_event_exists_for_anomaly(anomaly.month, anomaly.likely_cause):
            unconfirmed.append(anomaly)

    return unconfirmed


# V1.6.6 — International Audience Intelligence

def get_international_breakdown(month_str: Optional[str] = None) -> dict:
    """
    Get international audience breakdown by language market.

    Args:
        month_str: Optional month filter in YYYY-MM format (defaults to latest)

    Returns:
        Dict with month, language_markets list, totals
    """
    rows = get_social_metrics(month_str)

    if not rows:
        raise ValueError("No social metrics data available")

    # Sort by month descending to get latest
    rows_sorted = sorted(rows, key=lambda r: r.get("month", ""), reverse=True)
    latest = rows_sorted[0]
    prior = rows_sorted[1] if len(rows_sorted) > 1 else None

    month = latest.get("month", "")

    # Extract language engagement values
    spanish = latest.get("spanish_account_engagement", 0)
    english = latest.get("english_account_engagement", 0)
    arabic = latest.get("arabic_account_engagement", 0)
    french = latest.get("french_account_engagement", 0)
    other = latest.get("other_account_engagement", 0)

    total_engagement = latest.get("total_engagement", 0)

    # Compute prior month values for MoM change
    prior_spanish = prior.get("spanish_account_engagement", 0) if prior else None
    prior_english = prior.get("english_account_engagement", 0) if prior else None
    prior_arabic = prior.get("arabic_account_engagement", 0) if prior else None
    prior_french = prior.get("french_account_engagement", 0) if prior else None
    prior_other = prior.get("other_account_engagement", 0) if prior else None

    def compute_mom(current, previous):
        if previous is None or previous == 0:
            return None
        return ((current - previous) / previous) * 100

    # Build language breakdown list
    language_markets = [
        {
            "language": "Spanish",
            "account_username": "realmadrid",
            "monthly_engagement": spanish,
            "follower_count": 48_800_000,  # From X
            "engagement_per_follower": spanish / 48_800_000 if spanish > 0 else 0,
            "pct_of_total_engagement": (spanish / total_engagement * 100) if total_engagement > 0 else 0,
            "mom_change": compute_mom(spanish, prior_spanish)
        },
        {
            "language": "English",
            "account_username": "realmadriden",
            "monthly_engagement": english,
            "follower_count": 17_000_000,
            "engagement_per_follower": english / 17_000_000 if english > 0 else 0,
            "pct_of_total_engagement": (english / total_engagement * 100) if total_engagement > 0 else 0,
            "mom_change": compute_mom(english, prior_english)
        },
        {
            "language": "Arabic",
            "account_username": "realmadridarab",
            "monthly_engagement": arabic,
            "follower_count": 11_900_000,
            "engagement_per_follower": arabic / 11_900_000 if arabic > 0 else 0,
            "pct_of_total_engagement": (arabic / total_engagement * 100) if total_engagement > 0 else 0,
            "mom_change": compute_mom(arabic, prior_arabic)
        },
        {
            "language": "French",
            "account_username": "realmadridfra",
            "monthly_engagement": french,
            "follower_count": 5_000_000,
            "engagement_per_follower": french / 5_000_000 if french > 0 else 0,
            "pct_of_total_engagement": (french / total_engagement * 100) if total_engagement > 0 else 0,
            "mom_change": compute_mom(french, prior_french)
        },
        {
            "language": "Other",
            "account_username": None,
            "monthly_engagement": other,
            "follower_count": None,
            "engagement_per_follower": None,
            "pct_of_total_engagement": (other / total_engagement * 100) if total_engagement > 0 else 0,
            "mom_change": compute_mom(other, prior_other)
        }
    ]

    total_international = english + arabic + french + other
    international_ratio = latest.get("international_engagement_ratio", 0)

    return {
        "month": month,
        "language_markets": language_markets,
        "total_international_engagement": total_international,
        "international_engagement_ratio": international_ratio
    }


def get_international_trend() -> dict:
    """
    Get 12-month trend of international audience breakdown.

    Returns:
        Dict with trend list (monthly data points)
    """
    rows = get_social_metrics()

    if not rows:
        raise ValueError("No social metrics data available")

    # Sort chronologically
    rows_sorted = sorted(rows, key=lambda r: r.get("month", ""))

    trend = []
    for row in rows_sorted:
        trend.append({
            "month": row.get("month", ""),
            "spanish_engagement": row.get("spanish_account_engagement", 0),
            "english_engagement": row.get("english_account_engagement", 0),
            "arabic_engagement": row.get("arabic_account_engagement", 0),
            "french_engagement": row.get("french_account_engagement", 0),
            "other_engagement": row.get("other_account_engagement", 0),
            "international_ratio": row.get("international_engagement_ratio", 0)
        })

    return {"trend": trend}


def compute_international_commercial_correlation() -> dict:
    """
    Test correlation between international_engagement_ratio and commercial metrics.

    Uses Pearson correlation (same as content intelligence).
    Tests: streaming active_subscriptions, ecommerce unique_visitors.

    Returns:
        Dict with correlations list, strongest_correlation
    """
    # Get social metrics
    social_rows = get_social_metrics()
    if len(social_rows) < 6:
        return {"correlations": [], "strongest_correlation": None}

    # Sort chronologically
    social_sorted = sorted(social_rows, key=lambda r: r.get("month", ""))

    # Extract international_engagement_ratio time series
    international_ratio_values = []
    social_months = []
    for row in social_sorted:
        val = row.get("international_engagement_ratio")
        if val is not None:
            international_ratio_values.append(float(val))
            social_months.append(row.get("month"))

    if len(international_ratio_values) < 6:
        return {"correlations": [], "strongest_correlation": None}

    # Load commercial metrics
    kpi_rows = _client().read_table("gold_kpi_health")
    kpi_rows = sorted(kpi_rows, key=lambda r: r.get("month", ""))

    correlations = []

    # Test streaming active_subscriptions
    streaming_values = []
    streaming_months = []
    for row in kpi_rows:
        if row.get("asset_name") == "streaming" and row.get("metric_name") == "active_subscriptions":
            val = row.get("metric_value")
            if val is not None:
                streaming_values.append(float(val))
                streaming_months.append(row.get("month"))

    if len(streaming_values) >= 6:
        # Test at lag 0, 1, 2, 3 months
        for lag in [0, 1, 2, 3]:
            # Align time series with lag
            aligned_international = []
            aligned_streaming = []

            for i, s_month in enumerate(social_months):
                # Find streaming value at social_month + lag
                try:
                    lag_idx = streaming_months.index(s_month) + lag
                    if lag_idx < len(streaming_months):
                        aligned_international.append(international_ratio_values[i])
                        aligned_streaming.append(streaming_values[lag_idx])
                except (ValueError, IndexError):
                    continue

            if len(aligned_international) >= 6:
                try:
                    corr, p_value = pearsonr(aligned_international, aligned_streaming)

                    if abs(corr) >= 0.45:
                        direction = "positive" if corr > 0 else "negative"
                        abs_corr = abs(corr)
                        if abs_corr >= 0.60:
                            strength_label = "Strong"
                        elif abs_corr >= 0.55:
                            strength_label = "Moderate"
                        else:
                            strength_label = "Weak"

                        interpretation = (
                            f"International audience growth correlates with active_subscriptions performance "
                            f"at {lag} month lag ({strength_label.lower()} strength). "
                            f"This suggests international fan engagement has measurable commercial value beyond brand awareness."
                        )

                        correlations.append({
                            "commercial_metric": "active_subscriptions",
                            "commercial_asset": "streaming",
                            "correlation": corr,
                            "lag_months": lag,
                            "direction": direction,
                            "strength_label": strength_label,
                            "interpretation": interpretation,
                            "passes_threshold": True
                        })
                except:
                    pass

    # Test ecommerce unique_visitors
    ecommerce_values = []
    ecommerce_months = []
    for row in kpi_rows:
        if row.get("asset_name") == "ecommerce" and row.get("metric_name") == "unique_visitors":
            val = row.get("metric_value")
            if val is not None:
                ecommerce_values.append(float(val))
                ecommerce_months.append(row.get("month"))

    if len(ecommerce_values) >= 6:
        # Test at lag 0, 1, 2, 3 months
        for lag in [0, 1, 2, 3]:
            # Align time series with lag
            aligned_international = []
            aligned_ecommerce = []

            for i, s_month in enumerate(social_months):
                # Find ecommerce value at social_month + lag
                try:
                    lag_idx = ecommerce_months.index(s_month) + lag
                    if lag_idx < len(ecommerce_months):
                        aligned_international.append(international_ratio_values[i])
                        aligned_ecommerce.append(ecommerce_values[lag_idx])
                except (ValueError, IndexError):
                    continue

            if len(aligned_international) >= 6:
                try:
                    corr, p_value = pearsonr(aligned_international, aligned_ecommerce)

                    if abs(corr) >= 0.45:
                        direction = "positive" if corr > 0 else "negative"
                        abs_corr = abs(corr)
                        if abs_corr >= 0.60:
                            strength_label = "Strong"
                        elif abs_corr >= 0.55:
                            strength_label = "Moderate"
                        else:
                            strength_label = "Weak"

                        interpretation = (
                            f"International audience growth correlates with unique_visitors on ecommerce "
                            f"at {lag} month lag ({strength_label.lower()} strength). "
                            f"International traffic drives global store visits."
                        )

                        correlations.append({
                            "commercial_metric": "unique_visitors",
                            "commercial_asset": "ecommerce",
                            "correlation": corr,
                            "lag_months": lag,
                            "direction": direction,
                            "strength_label": strength_label,
                            "interpretation": interpretation,
                            "passes_threshold": True
                        })
                except:
                    pass

    # Sort by abs correlation descending
    correlations.sort(key=lambda c: abs(c["correlation"]), reverse=True)

    strongest = correlations[0] if correlations else None

    return {
        "correlations": correlations,
        "strongest_correlation": strongest
    }


def get_market_growth_ranking() -> dict:
    """
    Get market growth ranking (which language markets are growing fastest).

    Returns:
        Dict with month, rankings list (sorted by mom_change_pct descending)
    """
    rows = get_social_metrics()

    if len(rows) < 2:
        raise ValueError("Need at least 2 months of data for growth ranking")

    # Sort by month descending
    rows_sorted = sorted(rows, key=lambda r: r.get("month", ""), reverse=True)

    latest = rows_sorted[0]
    prior = rows_sorted[1]

    month = latest.get("month", "")

    # Extract language engagement values
    markets = [
        {
            "market": "Spanish",
            "this_month": latest.get("spanish_account_engagement", 0),
            "prior_month": prior.get("spanish_account_engagement", 0)
        },
        {
            "market": "English",
            "this_month": latest.get("english_account_engagement", 0),
            "prior_month": prior.get("english_account_engagement", 0)
        },
        {
            "market": "Arabic",
            "this_month": latest.get("arabic_account_engagement", 0),
            "prior_month": prior.get("arabic_account_engagement", 0)
        },
        {
            "market": "French",
            "this_month": latest.get("french_account_engagement", 0),
            "prior_month": prior.get("french_account_engagement", 0)
        },
        {
            "market": "Other",
            "this_month": latest.get("other_account_engagement", 0),
            "prior_month": prior.get("other_account_engagement", 0)
        }
    ]

    # Compute MoM change %
    for market in markets:
        if market["prior_month"] > 0:
            market["mom_change_pct"] = ((market["this_month"] - market["prior_month"]) / market["prior_month"]) * 100
        else:
            market["mom_change_pct"] = 0.0

    # Sort by mom_change_pct descending
    markets_sorted = sorted(markets, key=lambda m: m["mom_change_pct"], reverse=True)

    return {
        "month": month,
        "rankings": markets_sorted
    }
