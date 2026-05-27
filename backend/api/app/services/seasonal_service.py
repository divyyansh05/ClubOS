import calendar
from typing import Any, Optional
from datetime import datetime

from app.clients.databricks import DatabricksClient
from app.config.settings import settings


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def _month_str(row: dict[str, Any], key: str = "month") -> str:
    """Extract YYYY-MM-DD format date string from row"""
    val = row.get(key, "")
    return str(val)[:10] if val else ""


def _calendar_month(date_str: str) -> int:
    """Extract calendar month (1-12) from YYYY-MM-DD date string"""
    return int(date_str.split("-")[1])


def compute_seasonal_baseline(asset: str, metric: str) -> dict[int, dict[str, Any]]:
    """
    Compute seasonal baseline statistics for a metric across all calendar months.

    Returns dict keyed by month number (1-12) with stats:
    - seasonal_mean: average value across all years
    - seasonal_std: standard deviation
    - seasonal_min: minimum observed
    - seasonal_max: maximum observed
    - seasonal_p25: 25th percentile
    - seasonal_p75: 75th percentile
    - year_count: number of years of data for this month
    """
    try:
        all_health = _client().read_gold_table("gold_kpi_health")

        # Filter for this metric
        metric_health = [
            r for r in all_health
            if str(r.get("asset_name", "")).lower() == asset.lower()
            and str(r.get("metric_name", "")).lower() == metric.lower()
        ]

        if not metric_health:
            return {}

        # Group by calendar month
        month_groups: dict[int, list[float]] = {}
        for r in metric_health:
            month_str = _month_str(r)
            cal_month = _calendar_month(month_str)
            value = r.get("metric_value")
            if value is not None:
                if cal_month not in month_groups:
                    month_groups[cal_month] = []
                month_groups[cal_month].append(float(value))

        # Compute stats for each month
        baseline = {}
        for cal_month, values in month_groups.items():
            if not values:
                continue

            values_sorted = sorted(values)
            n = len(values)

            # Mean and std
            mean_val = sum(values) / n
            if n > 1:
                variance = sum((x - mean_val) ** 2 for x in values) / (n - 1)
                std_val = variance ** 0.5
            else:
                std_val = 0.0

            # Percentiles
            def percentile(data, p):
                k = (n - 1) * p
                f = int(k)
                c = k - f
                if f + 1 < n:
                    return data[f] + c * (data[f + 1] - data[f])
                return data[f]

            p25 = percentile(values_sorted, 0.25) if n >= 2 else values_sorted[0]
            p75 = percentile(values_sorted, 0.75) if n >= 2 else values_sorted[0]

            baseline[cal_month] = {
                "seasonal_mean": mean_val,
                "seasonal_std": std_val,
                "seasonal_min": min(values),
                "seasonal_max": max(values),
                "seasonal_p25": p25,
                "seasonal_p75": p75,
                "year_count": n,
                "month_name": calendar.month_name[cal_month]
            }

        return baseline

    except Exception as e:
        print(f"Error computing seasonal baseline for {asset}/{metric}: {e}")
        return {}


def get_seasonal_context_for_month(
    asset: str,
    metric: str,
    month_str: str
) -> Optional[dict[str, Any]]:
    """
    Get seasonal context for a specific month.

    Returns dict with:
    - seasonal_mean: expected value for this calendar month
    - seasonal_std: standard deviation
    - is_within_normal_range: True if z-score between -1.5 and +1.5
    - seasonal_expectation: description of typical behavior
    - interpretation: detailed interpretation string
    - year_count: years of historical data
    - z_score: deviation from seasonal mean in standard deviations
    - actual_value: the actual metric value for this month
    """
    try:
        # Get actual value for this month
        all_health = _client().read_gold_table("gold_kpi_health")
        match = next(
            (
                r for r in all_health
                if str(r.get("asset_name", "")).lower() == asset.lower()
                and str(r.get("metric_name", "")).lower() == metric.lower()
                and _month_str(r) == month_str[:10]
            ),
            None
        )

        if not match:
            return None

        actual_value = match.get("metric_value")
        if actual_value is None:
            return None
        actual_value = float(actual_value)

        # Get seasonal baseline for this calendar month
        cal_month = _calendar_month(month_str[:10])
        baseline = compute_seasonal_baseline(asset, metric)

        if cal_month not in baseline:
            return None

        month_baseline = baseline[cal_month]
        mean = month_baseline["seasonal_mean"]
        std = month_baseline["seasonal_std"]
        month_name = month_baseline["month_name"]
        year_count = month_baseline["year_count"]

        # Compute z-score
        if std > 0:
            z_score = (actual_value - mean) / std
        else:
            z_score = 0.0

        # Determine if within normal range
        is_within_normal = -1.5 <= z_score <= 1.5

        # Build seasonal expectation
        if mean > 0:
            pct_from_mean = ((actual_value - mean) / mean) * 100
            direction = "higher" if pct_from_mean > 0 else "lower"
            seasonal_expectation = f"Typically {direction} in {month_name}"
        else:
            seasonal_expectation = f"Typical {month_name} behavior"

        # Build interpretation
        abs_z = abs(z_score)
        if z_score < -2.0:
            interpretation = (
                f"Significantly below seasonal norm. This metric typically reads "
                f"{mean:.4f} in {month_name}. Current value is {abs_z:.2f} standard "
                f"deviations below expectation — genuinely anomalous."
            )
        elif z_score < -1.5:
            interpretation = (
                f"Slightly below seasonal norm. Worth monitoring but within the range "
                f"of historical variation for {month_name}. Historical {month_name} "
                f"average: {mean:.4f}."
            )
        elif z_score > 1.5:
            interpretation = (
                f"Above seasonal norm. {month_name} typically shows lower values — "
                f"this positive deviation ({abs_z:.2f} std devs) is commercially notable."
            )
        else:
            interpretation = (
                f"Within expected seasonal range for {month_name}. Historical {month_name} "
                f"average: {mean:.4f}. This movement is expected."
            )

        return {
            "seasonal_mean": mean,
            "seasonal_std": std,
            "seasonal_min": month_baseline["seasonal_min"],
            "seasonal_max": month_baseline["seasonal_max"],
            "seasonal_p25": month_baseline["seasonal_p25"],
            "seasonal_p75": month_baseline["seasonal_p75"],
            "is_within_normal_range": is_within_normal,
            "seasonal_expectation": seasonal_expectation,
            "interpretation": interpretation,
            "year_count": year_count,
            "z_score": z_score,
            "actual_value": actual_value,
            "month_name": month_name
        }

    except Exception as e:
        print(f"Error getting seasonal context for {asset}/{metric}/{month_str}: {e}")
        return None
