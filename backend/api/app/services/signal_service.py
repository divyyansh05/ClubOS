import logging
from typing import Any, Optional

from app.clients.databricks import DatabricksClient
from app.config.settings import settings
from app.services.social_signal_service import compute_social_signals

logger = logging.getLogger(__name__)


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def _month_str(row: dict[str, Any], key: str) -> str:
    return str(row[key])[:10]


def _get_source_metric_health(asset_name: str, metric_name: str, month: str) -> Optional[dict[str, Any]]:
    """Get current health data for a source metric"""
    try:
        all_health = _client().read_gold_table("gold_kpi_health")
        match = next(
            (
                r for r in all_health
                if str(r.get("asset_name", "")).lower() == asset_name.lower()
                and str(r.get("metric_name", "")).lower() == metric_name.lower()
                and _month_str(r, "month") == month
            ),
            None
        )
        return match
    except Exception as exc:
        logger.warning("Failed loading source metric health for signal enrichment: %s", exc)
        return None


def _compute_signal_status(
    source_health: Optional[dict[str, Any]],
    relationship_direction: str,
    lag_months: int
) -> tuple[str, str]:
    """Compute current_status and interpretation meaning"""
    if not source_health:
        return "unknown", "Source metric data unavailable"

    trend_direction = str(source_health.get("trend_direction", "stable")).lower()

    if trend_direction == "up" and relationship_direction == "positive":
        status = "firing_positive"
        meaning = f"Source rising — target metric expected to rise in {lag_months} month{'s' if lag_months > 1 else ''}"
    elif trend_direction == "down" and relationship_direction == "positive":
        status = "firing_negative"
        meaning = f"Source declining — target metric expected to decline in {lag_months} month{'s' if lag_months > 1 else ''}"
    elif trend_direction == "up" and relationship_direction == "negative":
        status = "firing_negative"
        meaning = f"Source rising — target metric expected to decline in {lag_months} month{'s' if lag_months > 1 else ''}"
    elif trend_direction == "down" and relationship_direction == "negative":
        status = "firing_positive"
        meaning = f"Source declining — target metric expected to rise in {lag_months} month{'s' if lag_months > 1 else ''}"
    else:  # stable
        status = "neutral"
        meaning = "Source stable — no strong directional signal currently"

    return status, meaning


def _get_priority_board_connection(
    source_metric: str,
    target_metric: str,
    current_status: str,
    month: str
) -> Optional[dict[str, Any]]:
    """Check if source or target metric is on Priority Board"""
    try:
        all_priorities = _client().read_gold_table("gold_priority_board")
        # Filter for latest month
        priorities = [
            p for p in all_priorities
            if _month_str(p, "month") == month
        ]

        # Check if target metric is on priority board (more relevant)
        target_match = next(
            (
                p for p in priorities
                if str(p.get("primary_metric", "")).lower() == target_metric.lower()
            ),
            None
        )

        if target_match:
            rank = int(target_match.get("priority_rank", 0))
            score = float(target_match.get("priority_score", 0))

            if current_status == "firing_negative":
                interpretation = (
                    f"The target metric {target_metric} currently ranks #{rank} on the "
                    f"Priority Board with a score of {score:.2f}. This signal's current "
                    f"negative trajectory may amplify that priority."
                )
                border_color = "critical"
            elif current_status == "firing_positive":
                interpretation = (
                    f"The target metric {target_metric} currently ranks #{rank} on the "
                    f"Priority Board with a score of {score:.2f}. This signal's current "
                    f"positive trajectory may help resolve that priority."
                )
                border_color = "good"
            else:
                interpretation = (
                    f"The target metric {target_metric} currently ranks #{rank} on the "
                    f"Priority Board with a score of {score:.2f}."
                )
                border_color = "neutral"

            return {
                "has_connection": True,
                "metric": target_metric,
                "rank": rank,
                "score": score,
                "interpretation": interpretation,
                "border_color": border_color
            }

        # Check source metric
        source_match = next(
            (
                p for p in priorities
                if str(p.get("primary_metric", "")).lower() == source_metric.lower()
            ),
            None
        )

        if source_match:
            rank = int(source_match.get("priority_rank", 0))
            score = float(source_match.get("priority_score", 0))
            interpretation = (
                f"The source metric {source_metric} currently ranks #{rank} on the "
                f"Priority Board with a score of {score:.2f}."
            )
            return {
                "has_connection": True,
                "metric": source_metric,
                "rank": rank,
                "score": score,
                "interpretation": interpretation,
                "border_color": "neutral"
            }

        # No connection
        return {
            "has_connection": False,
            "interpretation": (
                f"Neither {source_metric} nor {target_metric} currently appear on "
                f"the Priority Board. This signal is monitoring pre-priority movement."
            ),
            "border_color": "neutral"
        }
    except Exception as exc:
        logger.warning("Failed computing priority-board connection for signal: %s", exc)
        return None


def _build_signal_labels(
    source_metric: str,
    source_asset: str,
    target_metric: str,
    target_asset: str,
    lag_months: int,
    current_status: str
) -> dict[str, Any]:
    """Build driver/outcome labels and causal direction statement for a signal (V1.5.5)"""

    # Determine relationship type based on lag
    if lag_months > 0:
        relationship_type = "leading_indicator"
    elif lag_months == 0:
        relationship_type = "concurrent"
    else:
        relationship_type = "leading_indicator"  # default

    # Build causal direction statement
    causal_direction_statement = (
        f"Changes in {source_metric} on {source_asset} precede changes in "
        f"{target_metric} on {target_asset} by {lag_months} month{'s' if lag_months != 1 else ''}. "
        f"Source metric is the driver. Target metric is the predicted outcome."
    )

    # Build action statement based on current_status
    if current_status == "firing_positive":
        action_statement = (
            f"SIGNAL ACTIVE — {source_metric} is rising. "
            f"Based on historical patterns, {target_metric} is expected to "
            f"follow upward in {lag_months} month{'s' if lag_months != 1 else ''}. Recommended: anticipate "
            f"increased {target_metric} and align commercial plans accordingly."
        )
    elif current_status == "firing_negative":
        action_statement = (
            f"SIGNAL ACTIVE — {source_metric} is declining. "
            f"Based on historical patterns, {target_metric} is expected to "
            f"follow downward in {lag_months} month{'s' if lag_months != 1 else ''}. Recommended: flag "
            f"{target_metric} for early intervention before the lag window closes."
        )
    else:  # neutral or unknown
        action_statement = (
            f"SIGNAL MONITORING — {source_metric} is stable. "
            f"No directional signal this month. Continue monitoring for "
            f"sustained movement in either direction."
        )

    return {
        "driver_label": "Independent Variable (Driver)",
        "outcome_label": "Dependent Variable (Outcome)",
        "causal_direction_statement": causal_direction_statement,
        "action_statement": action_statement,
        "relationship_type": relationship_type
    }


def _build_dynamic_interpretation(
    signal: dict[str, Any],
    current_status: str,
    source_health: Optional[dict[str, Any]]
) -> str:
    """Build data-driven business interpretation based on current status"""
    if not source_health:
        return signal.get("business_interpretation", "Signal validated but current source data unavailable.")

    source_metric = signal["source_metric"]
    source_asset = signal["source_asset"]
    target_metric = signal["target_metric"]
    target_asset = signal["target_asset"]
    strength = int(signal["strength_score"] * 100)
    lag_months = signal["lag_months"]
    data_months = 103  # Total months in dataset

    # Calculate month-over-month % change
    metric_value = source_health.get("metric_value", 0)
    prior_month_value = source_health.get("prior_month_value")
    pct_change = 0.0
    if prior_month_value and prior_month_value != 0:
        pct_change = ((metric_value - prior_month_value) / prior_month_value) * 100

    if current_status == "firing_positive":
        return (
            f"{source_metric} on {source_asset} is currently trending UP "
            f"({pct_change:+.1f}% vs prior month). Based on {strength}% validated "
            f"correlation across {data_months} months of history, {target_metric} "
            f"on {target_asset} is expected to follow upward in approximately "
            f"{lag_months} month{'s' if lag_months > 1 else ''}. Recommended action: anticipate increased "
            f"{target_metric} and plan accordingly."
        )
    elif current_status == "firing_negative":
        return (
            f"{source_metric} on {source_asset} is currently trending DOWN "
            f"({pct_change:+.1f}% vs prior month). Based on {strength}% validated "
            f"correlation across {data_months} months of history, {target_metric} "
            f"on {target_asset} is expected to follow downward in approximately "
            f"{lag_months} month{'s' if lag_months > 1 else ''}. Recommended action: flag {target_metric} for "
            f"early review before the lag window closes."
        )
    else:  # neutral
        return (
            f"{source_metric} on {source_asset} is currently stable this month. "
            f"This signal remains validated at {strength}% correlation strength "
            f"across {data_months} months. Monitor {source_metric} for directional "
            f"movement — a sustained shift would activate this signal."
        )


def get_signal_view(signal_type_filter: Optional[str] = None) -> dict[str, Any]:
    """
    Get all validated signals (internal + social-to-commercial).

    Args:
        signal_type_filter: Optional filter - "internal", "social_to_commercial", or None for all

    Returns:
        Dict with latest_validated_month and items list
    """
    # Read internal signals from gold_signal_relationships
    rows = _client().read_gold_table("gold_signal_relationships")
    internal_signals_exist = bool(rows)

    if not rows:
        rows = []

    latest_validated_month = max((_month_str(row, "last_validated_month") for row in rows), default=None)

    # Build internal signals
    normalized = []
    for row in rows:
        signal_id = "__".join(
            [
                str(row["source_asset"]),
                str(row["source_metric"]),
                str(row["target_asset"]),
                str(row["target_metric"]),
                str(int(row["lag_months"])),
            ]
        )

        source_asset = str(row["source_asset"])
        source_metric = str(row["source_metric"])
        relationship_direction = str(row["relationship_direction"])
        lag_months = int(row["lag_months"])

        # Get source metric health data
        source_health = _get_source_metric_health(source_asset, source_metric, latest_validated_month)

        # Compute current status
        current_status, status_meaning = _compute_signal_status(
            source_health, relationship_direction, lag_months
        )

        # Extract source trend data
        source_trend_direction = None
        source_current_trend = None
        source_trend_pct_change = None
        source_current_value = None

        if source_health:
            source_trend_direction = str(source_health.get("trend_direction", "stable"))
            source_current_trend = source_health.get("deviation_from_rolling_avg")
            if source_current_trend is not None:
                source_current_trend = float(source_current_trend)

            metric_value = source_health.get("metric_value")
            if metric_value is not None:
                source_current_value = float(metric_value)

            prior_month_value = source_health.get("prior_month_value")
            if metric_value and prior_month_value and prior_month_value != 0:
                source_trend_pct_change = ((metric_value - prior_month_value) / prior_month_value) * 100

        # Get target metric health data
        target_asset = str(row["target_asset"])
        target_metric = str(row["target_metric"])
        target_health = _get_source_metric_health(target_asset, target_metric, latest_validated_month)

        target_current_value = None
        target_health_status = None
        if target_health:
            target_val = target_health.get("metric_value")
            if target_val is not None:
                target_current_value = float(target_val)
            target_health_status = str(target_health.get("health_status", "stable"))

        # Build dynamic interpretation
        signal_dict = {
            "source_metric": source_metric,
            "source_asset": source_asset,
            "target_metric": target_metric,
            "target_asset": target_asset,
            "strength_score": float(row["strength_score"]),
            "lag_months": lag_months,
        }
        dynamic_interpretation = _build_dynamic_interpretation(signal_dict, current_status, source_health)

        # Get priority board connection
        priority_connection = _get_priority_board_connection(
            source_metric, target_metric, current_status, latest_validated_month
        )

        # Build driver/outcome labels (V1.5.5)
        signal_labels = _build_signal_labels(
            source_metric, source_asset, target_metric, target_asset, lag_months, current_status
        )

        normalized.append(
            {
                "signal_id": signal_id,
                "source_asset": source_asset,
                "source_metric": source_metric,
                "target_asset": target_asset,
                "target_metric": target_metric,
                "lag_months": lag_months,
                "relationship_direction": relationship_direction,
                "strength_score": float(row["strength_score"]),
                "validation_status": str(row["validation_status"]),
                "business_interpretation": dynamic_interpretation,
                "last_validated_month": _month_str(row, "last_validated_month"),
                # New enriched fields
                "current_status": current_status,
                "status_meaning": status_meaning,
                "source_trend_direction": source_trend_direction,
                "source_current_trend": source_current_trend,
                "source_trend_pct_change": source_trend_pct_change,
                "source_current_value": source_current_value,
                "target_current_value": target_current_value,
                "target_health_status": target_health_status,
                "priority_connection": priority_connection,
                # V1.5.5: Driver/Outcome labels
                **signal_labels,
                # V1.6.2: Signal type
                "signal_type": "internal",
            }
        )

    # Compute social-to-commercial signals (V1.6.2)
    try:
        # Try 0.60 threshold first
        social_signals = compute_social_signals(correlation_threshold=0.60)

        # If no signals found, try lowering threshold to 0.50
        if not social_signals:
            social_signals = compute_social_signals(correlation_threshold=0.50)

        # Enrich each social signal with driver/outcome labels
        for signal in social_signals:
            signal_id = "__".join([
                str(signal["source_asset"]),
                str(signal["source_metric"]),
                str(signal["target_asset"]),
                str(signal["target_metric"]),
                str(signal["lag_months"]),
            ])
            signal["signal_id"] = signal_id

            # Add driver/outcome labels
            signal_labels = _build_signal_labels(
                signal["source_metric"],
                signal["source_asset"],
                signal["target_metric"],
                signal["target_asset"],
                signal["lag_months"],
                signal.get("current_status", "neutral")
            )
            signal.update(signal_labels)

            # Add status_meaning
            if signal.get("current_status") == "firing_positive":
                signal["status_meaning"] = (
                    f"Source rising — target metric expected to rise in "
                    f"{signal['lag_months']} month{'s' if signal['lag_months'] > 1 else ''}"
                )
            elif signal.get("current_status") == "firing_negative":
                signal["status_meaning"] = (
                    f"Source declining — target metric expected to decline in "
                    f"{signal['lag_months']} month{'s' if signal['lag_months'] > 1 else ''}"
                )
            else:
                signal["status_meaning"] = "Source stable — no strong directional signal currently"

            # Get priority connection for social signals
            priority_conn = _get_priority_board_connection(
                signal["source_metric"],
                signal["target_metric"],
                signal.get("current_status", "neutral"),
                signal["last_validated_month"]
            )
            signal["priority_connection"] = priority_conn

        # Merge social signals with internal signals
        normalized.extend(social_signals)

        # Update latest validated month if social signals are newer
        if social_signals:
            social_latest = max(s["last_validated_month"] for s in social_signals)
            if latest_validated_month is None or social_latest > latest_validated_month:
                latest_validated_month = social_latest

    except Exception as exc:
        # If social signal computation fails, just continue with internal signals
        logger.warning("Social-to-commercial signal computation failed: %s", exc)

    # Apply signal_type filter if specified
    if signal_type_filter:
        if signal_type_filter == "internal":
            normalized = [s for s in normalized if s.get("signal_type") == "internal"]
        elif signal_type_filter == "social_to_commercial":
            normalized = [s for s in normalized if s.get("signal_type") == "social_to_commercial"]
        # "all" or any other value returns everything

    # Sort by strength score
    normalized = sorted(normalized, key=lambda x: abs(x["strength_score"]), reverse=True)
    return {"latest_validated_month": latest_validated_month, "items": normalized}
