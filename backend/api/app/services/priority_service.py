import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from app.clients.databricks import DatabricksClient
from app.config.settings import settings
from app.services import anomaly_context_service, conversion_context_service, seasonal_service

logger = logging.getLogger(__name__)


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def _month_str(row: dict[str, Any], key: str = "month") -> str:
    val = row.get(key, "")
    return str(val)[:10] if val else ""


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _build_health_index(all_health: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Index health rows by (asset, metric), sorted newest first for fast 12m lookup."""
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in all_health:
        key = (_norm(row.get("asset_name")), _norm(row.get("metric_name")))
        index.setdefault(key, []).append(row)
    for rows in index.values():
        rows.sort(key=lambda x: _month_str(x), reverse=True)
    return index


def _build_peer_index(all_peer: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Index peer rows by (asset, metric, month)."""
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in all_peer:
        key = (_norm(row.get("asset_name")), _norm(row.get("metric_name")), _month_str(row))
        index[key] = row
    return index


def _load_metric_dictionary() -> dict[str, Any]:
    """Load metric dictionary for polarity and descriptions"""
    dict_path = Path(__file__).parent.parent.parent.parent.parent / "databricks" / "seeds" / "metric_dictionary.json"
    if dict_path.exists():
        with open(dict_path, 'r') as f:
            return json.load(f)
    return {}


def _load_scoring_config() -> dict[str, Any]:
    """Load scoring configuration"""
    config_path = Path(__file__).parent.parent / "config" / "scoring_config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


def _get_kpi_health_for_metric(
    asset_name: str,
    metric_name: str,
    month: str,
    all_health: Optional[list[dict[str, Any]]] = None,
    health_index: Optional[dict[tuple[str, str], list[dict[str, Any]]]] = None,
) -> list[dict[str, Any]]:
    """Get 12 months of KPI health data for a metric"""
    try:
        health_rows = all_health if all_health is not None else _client().read_gold_table("gold_kpi_health")
        metric_rows = None
        if health_index is not None:
            metric_rows = health_index.get((_norm(asset_name), _norm(metric_name)), [])
        if metric_rows is None:
            metric_rows = [
                r for r in health_rows
                if _norm(r.get("asset_name")) == _norm(asset_name)
                and _norm(r.get("metric_name")) == _norm(metric_name)
            ]
            metric_rows.sort(key=lambda x: _month_str(x), reverse=True)
        # Filter for this specific metric and last 12 months
        metric_health = [
            r for r in metric_rows
            if _month_str(r) <= month
        ]
        # Rows are already sorted descending from index path; keep behavior stable for fallback path.
        return metric_health[:12]
    except Exception as exc:
        logger.warning("Failed loading KPI health history for %s/%s: %s", asset_name, metric_name, exc)
        return []


def _get_peer_data_for_metric(
    asset_name: str,
    metric_name: str,
    month: str,
    all_peer: Optional[list[dict[str, Any]]] = None,
    peer_index: Optional[dict[tuple[str, str, str], dict[str, Any]]] = None,
) -> Optional[dict[str, Any]]:
    """Get peer benchmark data for a metric for the specified month"""
    try:
        peer_rows = all_peer if all_peer is not None else _client().read_gold_table("gold_peer_benchmark")
        if peer_index is not None:
            return peer_index.get((_norm(asset_name), _norm(metric_name), month))
        match = next(
            (
                r for r in peer_rows
                if _norm(r.get("asset_name")) == _norm(asset_name)
                and _norm(r.get("metric_name")) == _norm(metric_name)
                and _month_str(r) == month
            ),
            None
        )
        return match
    except Exception as exc:
        logger.warning("Failed loading peer data for %s/%s: %s", asset_name, metric_name, exc)
        return None


def _get_all_clubs_for_metric(
    asset_name: str,
    metric_name: str,
    month: str,
    all_peer: Optional[list[dict[str, Any]]] = None,
    peer_index: Optional[dict[tuple[str, str, str], dict[str, Any]]] = None,
) -> list[dict[str, Any]]:
    """Get all club values for a benchmarked metric in the specified month"""
    try:
        peer_row = _get_peer_data_for_metric(
            asset_name,
            metric_name,
            month,
            all_peer=all_peer,
            peer_index=peer_index,
        )
        if not peer_row:
            return []

        # Build club list: Real Madrid + anonymized peers
        clubs = []
        rm_value = float(peer_row.get("rm_value", 0))
        clubs.append({"club": "Real Madrid", "value": rm_value, "is_estimated": False})

        # Get peer values - we don't have individual peer values in the CSV,
        # but we can approximate from median, mean, and leader
        peer_median = float(peer_row.get("peer_median", 0))
        peer_leader = float(peer_row.get("peer_leader_value", 0))
        peer_mean = float(peer_row.get("peer_mean", 0))

        # Add peer values (anonymized)
        clubs.append({"club": "Peer 1 (Leader)", "value": peer_leader, "is_estimated": False})
        clubs.append({"club": "Peer 2 (Median)", "value": peer_median, "is_estimated": False})

        # Estimate other peer values around the mean
        if peer_mean > 0:
            clubs.append({"club": "Peer 3", "value": peer_mean * 0.95, "is_estimated": True})
            clubs.append({"club": "Peer 4", "value": peer_mean * 1.05, "is_estimated": True})
            clubs.append({"club": "Peer 5", "value": peer_mean * 0.90, "is_estimated": True})

        return clubs
    except Exception as exc:
        logger.warning("Failed building peer value list for %s/%s: %s", asset_name, metric_name, exc)
        return []


def _calculate_consecutive_declining_months(health_data: list[dict[str, Any]]) -> int:
    """Count consecutive months with 'down' trend direction from most recent"""
    count = 0
    for row in health_data:  # Already sorted newest first
        if str(row.get("trend_direction", "")).lower() == "down":
            count += 1
        else:
            break
    return count


def _build_data_driven_why_it_matters(
    row: dict[str, Any],
    supporting_json: dict[str, Any],
    peer_data: Optional[dict[str, Any]],
    consecutive_declining: int
) -> str:
    """Build data-driven why_it_matters using actual data"""
    sentences = []

    # Peer context sentence
    peer_context = supporting_json.get("peer_context", {})
    if peer_context and peer_context.get("peer_rank"):
        peer_rank = peer_context.get("peer_rank", 0)
        peer_count = peer_context.get("peer_club_count", 5)
        metric_name = str(row.get("primary_metric", "this metric"))
        gap_to_median = peer_context.get("gap_to_peer_median", 0)

        direction = "ahead of" if gap_to_median > 0 else "behind"
        abs_gap = abs(gap_to_median)

        sentences.append(
            f"Ranked {peer_rank} of {peer_count + 1} clubs on {metric_name}. "
            f"Gap to peer median: {gap_to_median:.4f} ({direction} peers by {abs_gap:.4f})."
        )

    # Persistence sentence
    if consecutive_declining >= 2:
        sentences.append(
            f"Declining for {consecutive_declining} consecutive months — a systemic trend, not a one-month anomaly."
        )

    # Evidence sentence
    evidence_count = len(supporting_json.get("linked_signal_references", []))
    if evidence_count > 0:
        sentences.append(
            f"Connected to {evidence_count} validated leading indicators — "
            "changes in this metric predict downstream commercial outcomes."
        )

    # If no data-driven sentences, keep original generic text
    if not sentences:
        return str(row.get("why_it_matters", "This metric requires attention based on current performance."))

    # Return max 2 sentences
    return " ".join(sentences[:2])


def _enrich_priority_row(
    row: dict[str, Any],
    include_detail: bool = False,
    all_health: Optional[list[dict[str, Any]]] = None,
    all_peer: Optional[list[dict[str, Any]]] = None,
    health_index: Optional[dict[tuple[str, str], list[dict[str, Any]]]] = None,
    peer_index: Optional[dict[tuple[str, str, str], dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Normalize and enrich a priority row with additional data"""
    month = _month_str(row)
    asset_name = str(row.get("asset_name", ""))
    metric_name = str(row.get("primary_metric", ""))

    # Parse supporting metrics JSON
    raw_support = str(row.get("supporting_metrics_json", "{}"))
    supporting_json = json.loads(raw_support) if raw_support else {}

    # Get KPI health history
    health_data = _get_kpi_health_for_metric(
        asset_name,
        metric_name,
        month,
        all_health=all_health,
        health_index=health_index,
    )

    # Get peer data
    peer_data = _get_peer_data_for_metric(
        asset_name,
        metric_name,
        month,
        all_peer=all_peer,
        peer_index=peer_index,
    )

    # Extract trend data from most recent health row
    trend_direction = None
    trend_slope = None
    if health_data:
        most_recent = health_data[0]
        trend_direction = str(most_recent.get("trend_direction", "stable"))
        # trend_slope not in CSV, use deviation as proxy
        deviation = most_recent.get("deviation_from_rolling_avg")
        if deviation is not None:
            trend_slope = float(deviation)

    # Calculate consecutive declining months
    consecutive_declining = _calculate_consecutive_declining_months(health_data)

    # Build historical values (last 12 months, oldest to newest)
    historical_values = []
    if health_data:
        # Reverse to get oldest first
        for h in reversed(health_data):
            historical_values.append({
                "month": _month_str(h),
                "value": float(h.get("metric_value", 0))
            })

    # Extract score breakdown from supporting JSON
    score_components = supporting_json.get("score_components", {})
    score_breakdown = None
    if score_components:
        # Load weights from config
        config = _load_scoring_config()
        weights = config.get("formula_weights", {
            "severity": 0.30,
            "persistence": 0.25,
            "peer_gap": 0.20,
            "commercial": 0.15,
            "evidence": 0.10
        })

        # Extract raw component scores (0-1 range)
        severity_score = float(score_components.get("severity", 0))
        persistence_score = float(score_components.get("persistence", 0))
        peer_gap_score = float(score_components.get("peer_gap", 0))
        commercial_score = float(score_components.get("commercial_weight", 0))
        evidence_score = float(score_components.get("supporting_evidence", 0))

        # Compute weighted contributions
        score_breakdown = {
            "severity": severity_score,
            "persistence": persistence_score,
            "peer_gap": peer_gap_score,
            "commercial": commercial_score,
            "evidence": evidence_score,
            "severity_contribution": round(severity_score * weights["severity"], 4),
            "persistence_contribution": round(persistence_score * weights["persistence"], 4),
            "peer_gap_contribution": round(peer_gap_score * weights["peer_gap"], 4),
            "commercial_contribution": round(commercial_score * weights["commercial"], 4),
            "evidence_contribution": round(evidence_score * weights["evidence"], 4)
        }

    # Get peer values and stats
    peer_values = None
    peer_median = None
    peer_leader_value = None
    if peer_data:
        peer_median = float(peer_data.get("peer_median", 0)) if peer_data.get("peer_median") else None
        peer_leader_value = float(peer_data.get("peer_leader_value", 0)) if peer_data.get("peer_leader_value") else None
        peer_values = _get_all_clubs_for_metric(
            asset_name,
            metric_name,
            month,
            all_peer=all_peer,
            peer_index=peer_index,
        )
        if peer_values:
            peer_values = [
                {
                    "club": p["club"],
                    "value": p["value"],
                    "is_estimated": bool(p.get("is_estimated", False)),
                }
                for p in peer_values
            ]

    # Build data-driven why_it_matters
    why_it_matters = _build_data_driven_why_it_matters(
        row, supporting_json, peer_data, consecutive_declining
    )

    # Get anomaly context classification (V1.5.2)
    anomaly_context = None
    event_suppressed = None
    try:
        # Get deviation value and health status from most recent health data
        deviation_value = None
        health_status = "stable"
        if health_data:
            most_recent = health_data[0]
            deviation_value = most_recent.get("deviation_from_rolling_avg")
            health_status = str(most_recent.get("health_status", "stable"))

        anomaly_context = anomaly_context_service.classify_metric_movement(
            asset_name, metric_name, month, deviation_value, health_status
        )

        # Check if movement is primarily event-driven and should be visually flagged
        if anomaly_context.get("context_type") == "event_driven":
            # Flag as event-suppressed if it's a spike driven by a single event
            # (not a persistent multi-month trend)
            if consecutive_declining <= 1:  # Not a persistent trend
                event_suppressed = True
    except Exception as e:
        # Fail gracefully - don't break priority response if event context fails
        logger.warning("Could not classify anomaly context for %s: %s", row["priority_id"], e)
        anomaly_context = {"context_type": "unexplained", "suppress_from_priority_board": False}

    # Get seasonal baseline intelligence (V1.5.3)
    seasonal_context = None
    try:
        seasonal_context = seasonal_service.get_seasonal_context_for_month(
            asset_name, metric_name, month
        )
    except Exception as e:
        # Fail gracefully - don't break priority response if seasonal context fails
        logger.warning("Could not get seasonal context for %s: %s", row["priority_id"], e)

    # Get conversion rate volume pairing context (V1.5.4)
    conversion_context = None
    if metric_name.lower() == "conversion_rate":
        try:
            conversion_context = conversion_context_service.get_conversion_context(
                asset_name, month
            )
        except Exception as e:
            # Fail gracefully - don't break priority response if conversion context fails
            logger.warning("Could not get conversion context for %s: %s", row["priority_id"], e)

    # Base normalized data
    result = {
        "priority_id": str(row.get("priority_id", "")),
        "month": month,
        "title": str(row.get("priority_title", "")),
        "category": str(row.get("priority_category", "")),
        "score": float(row.get("priority_score", 0)),
        "rank": int(row.get("priority_rank", 0)),
        "asset_name": asset_name,
        "primary_metric": metric_name,
        "summary_text": str(row.get("summary_text", "")),
        "why_it_matters": why_it_matters,
        "suggested_next_investigation": str(row.get("suggested_next_investigation", "")),
        # New enriched fields
        "consecutive_declining_months": consecutive_declining if consecutive_declining > 0 else None,
        "trend_direction": trend_direction,
        "trend_slope": trend_slope,
        "score_breakdown": score_breakdown,
        "historical_values": historical_values if historical_values else None,
        "peer_values": peer_values if peer_values else None,
        "peer_median": peer_median,
        "peer_leader_value": peer_leader_value,
        # Event-adjusted anomaly detection (V1.5.2)
        "anomaly_context": anomaly_context,
        "event_suppressed": event_suppressed,
        # Seasonal baseline intelligence (V1.5.3)
        "seasonal_context": seasonal_context,
        # Conversion rate volume pairing (V1.5.4)
        "conversion_context": conversion_context,
    }

    # Add supporting metrics for detail view
    if include_detail:
        result["supporting_metrics"] = supporting_json

    return result


def get_latest_priorities() -> dict[str, Any]:
    client = _client()
    rows = client.read_gold_table("gold_priority_board")
    if not rows:
        return {"latest_month": "", "items": []}

    all_health = client.read_gold_table("gold_kpi_health")
    all_peer = client.read_gold_table("gold_peer_benchmark")
    health_index = _build_health_index(all_health)
    peer_index = _build_peer_index(all_peer)

    latest_month = max(_month_str(r) for r in rows)
    month_rows = [
        _enrich_priority_row(
            r,
            include_detail=False,
            all_health=all_health,
            all_peer=all_peer,
            health_index=health_index,
            peer_index=peer_index,
        )
        for r in rows
        if _month_str(r) == latest_month
    ]
    month_rows = sorted(month_rows, key=lambda x: x["rank"])
    return {"latest_month": latest_month, "items": month_rows}


def get_priority_detail(priority_id: str) -> dict[str, Any]:
    client = _client()
    rows = client.read_gold_table("gold_priority_board")
    match = next((r for r in rows if str(r.get("priority_id")) == priority_id), None)
    if not match:
        raise KeyError(f"Priority '{priority_id}' not found.")

    all_health = client.read_gold_table("gold_kpi_health")
    all_peer = client.read_gold_table("gold_peer_benchmark")
    health_index = _build_health_index(all_health)
    peer_index = _build_peer_index(all_peer)
    detail = _enrich_priority_row(
        match,
        include_detail=True,
        all_health=all_health,
        all_peer=all_peer,
        health_index=health_index,
        peer_index=peer_index,
    )
    return detail
