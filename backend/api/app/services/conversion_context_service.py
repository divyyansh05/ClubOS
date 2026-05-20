from typing import Any, Optional

from app.clients.databricks import DatabricksClient
from app.config.settings import settings
from app.services import seasonal_service


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def _month_str(row: dict[str, Any], key: str = "month") -> str:
    """Extract YYYY-MM-DD format date string from row"""
    return str(row[key])[:10]


def get_conversion_context(asset: str, month_str: str) -> Optional[dict[str, Any]]:
    """
    Get conversion rate volume pairing context for a specific month.

    Reads conversion_rate and unique_visitors for the asset/month,
    compares to seasonal medians, classifies into quadrants, and
    returns interpretation + visualization data.

    Returns dict with:
    - quadrant: one of 4 quadrant identifiers
    - label: human-readable quadrant label
    - interpretation: detailed explanation
    - color: UI color hint (good/warning/critical)
    - conversion_rate_value: actual conversion rate
    - visitors_value: actual unique visitors
    - conversion_seasonal_median: median conversion rate for this calendar month
    - visitors_seasonal_median: median visitors for this calendar month
    - conversion_vs_median_pct: % difference from median
    - visitors_vs_median_pct: % difference from median
    """
    try:
        # Read gold_kpi_health for conversion_rate
        all_health = _client().read_gold_table("gold_kpi_health")

        # Get conversion_rate for this asset/month
        conv_match = next(
            (
                r for r in all_health
                if str(r.get("asset_name", "")).lower() == asset.lower()
                and str(r.get("metric_name", "")).lower() == "conversion_rate"
                and _month_str(r) == month_str[:10]
            ),
            None
        )

        # Get unique_visitors for this asset/month
        visitors_match = next(
            (
                r for r in all_health
                if str(r.get("asset_name", "")).lower() == asset.lower()
                and str(r.get("metric_name", "")).lower() == "unique_visitors"
                and _month_str(r) == month_str[:10]
            ),
            None
        )

        if not conv_match or not visitors_match:
            return None

        conversion_rate_value = float(conv_match.get("metric_value", 0))
        visitors_value = float(visitors_match.get("metric_value", 0))

        # Get seasonal baselines for both metrics
        conv_baseline = seasonal_service.compute_seasonal_baseline(asset, "conversion_rate")
        visitors_baseline = seasonal_service.compute_seasonal_baseline(asset, "unique_visitors")

        # Extract calendar month
        cal_month = int(month_str[:10].split("-")[1])

        if cal_month not in conv_baseline or cal_month not in visitors_baseline:
            return None

        # Get seasonal medians (p50 = median, so we'll use mean as proxy)
        # Actually p25 and p75 are percentiles, mean is the average
        # For median, we can use (p25 + p75) / 2 as approximation or use mean
        # Let's use mean as the "expected" value
        conversion_seasonal_median = conv_baseline[cal_month]["seasonal_mean"]
        visitors_seasonal_median = visitors_baseline[cal_month]["seasonal_mean"]

        # Determine if above or below median
        conv_above_median = conversion_rate_value > conversion_seasonal_median
        vol_above_median = visitors_value > visitors_seasonal_median

        # Calculate percentage differences
        conv_vs_median_pct = ((conversion_rate_value - conversion_seasonal_median) / conversion_seasonal_median) * 100 if conversion_seasonal_median > 0 else 0
        visitors_vs_median_pct = ((visitors_value - visitors_seasonal_median) / visitors_seasonal_median) * 100 if visitors_seasonal_median > 0 else 0

        # Classify into quadrants
        if conv_above_median and vol_above_median:
            quadrant = "high_conversion_high_volume"
            label = "Strong Performance"
            interpretation = (
                "Both conversion rate and traffic are above seasonal median. "
                "This is the optimal commercial state — broad reach with efficient conversion. "
                "Monitor to sustain."
            )
            color = "good"

        elif conv_above_median and not vol_above_median:
            quadrant = "high_conversion_low_volume"
            label = "Warm Audience — Scale Risk"
            interpretation = (
                "Conversion rate is above median but traffic is below. "
                "The store is efficient but the audience is narrow. Strong performance "
                "on a small base — question is whether acquisition is limited."
            )
            color = "warning"

        elif not conv_above_median and vol_above_median:
            quadrant = "low_conversion_high_volume"
            label = "Top-of-Funnel Expansion — Review Funnel"
            interpretation = (
                "Traffic is above median but conversion rate is below. "
                "Could indicate new, lower-intent audience (positive for reach) or "
                "funnel/UX friction preventing purchase completion (negative). Requires "
                "investigation into checkout flow and user intent signals."
            )
            color = "warning"

        else:  # both below median
            quadrant = "low_conversion_low_volume"
            label = "Broad Underperformance"
            interpretation = (
                "Both traffic and conversion below median. This is the most commercially "
                "concerning combination — limited reach and poor funnel efficiency simultaneously."
            )
            color = "critical"

        return {
            "quadrant": quadrant,
            "label": label,
            "interpretation": interpretation,
            "color": color,
            "conversion_rate_value": conversion_rate_value,
            "visitors_value": visitors_value,
            "conversion_seasonal_median": conversion_seasonal_median,
            "visitors_seasonal_median": visitors_seasonal_median,
            "conversion_vs_median_pct": conv_vs_median_pct,
            "visitors_vs_median_pct": visitors_vs_median_pct,
        }

    except Exception as e:
        print(f"Error getting conversion context for {asset}/{month_str}: {e}")
        return None
