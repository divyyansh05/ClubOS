from typing import Optional

from app.services import event_service


def _build_interpretation(event_category: str, event_name: str) -> str:
    """Generate interpretation string based on event category"""
    interpretations = {
        "player_signing": f"Spike consistent with {event_name} signing effect. Digital surge expected and commercially positive.",
        "player_departure": f"Movement may reflect {event_name} departure impact. Monitor for stabilization in following months.",
        "match_result_win": f"Engagement spike aligns with {event_name}. Trophy/victory effects typically last 2-4 weeks across digital platforms.",
        "match_result_loss": f"Decline may correlate with {event_name}. Fan engagement typically recovers within 1-2 weeks.",
        "trophy_win": f"Exceptional performance spike consistent with trophy win. Sustained elevation expected for 4-8 weeks.",
        "trophy_loss": f"Temporary decline aligns with {event_name}. Historical patterns show recovery within 2-3 weeks.",
        "transfer_window": f"Activity consistent with {event_name} period. Transfer speculation typically drives elevated digital traffic.",
        "media_event": f"Spike aligns with {event_name}. Media coverage events create short-term engagement peaks (1-2 weeks).",
        "injury_news": f"Decline may be partially explained by {event_name}. Monitor for recovery to baseline in following month.",
        "commercial_event": f"Movement consistent with {event_name}. Commercial campaigns typically show measurable impact within 14-day window.",
    }
    return interpretations.get(event_category, f"Movement may be related to {event_name}.")


def classify_metric_movement(
    asset: str,
    metric: str,
    month_str: str,
    deviation_value: Optional[float],
    health_status: str
) -> dict:
    """
    Classify a metric movement as event-driven, partially explained, or unexplained.

    Args:
        asset: Digital asset name (main_website, ecommerce, streaming, fan_app)
        metric: Metric name
        month_str: Month in YYYY-MM format
        deviation_value: Deviation from seasonal baseline (can be None)
        health_status: Current health status of the metric

    Returns:
        Dictionary with classification context
    """
    # Get events near this metric movement
    try:
        events_response = event_service.get_events_near_metric_movement(asset, metric, month_str)
        nearby_events = events_response.get("items", [])
    except Exception:
        nearby_events = []

    # No events found - unexplained movement
    if not nearby_events:
        return {
            "context_type": "unexplained",
            "suppress_from_priority_board": False
        }

    # Find highest magnitude event
    high_magnitude_event = None
    medium_or_low_event = None

    for event in nearby_events:
        if event["impact_magnitude"] == "high":
            # Prioritize high magnitude events
            if high_magnitude_event is None:
                high_magnitude_event = event
        elif medium_or_low_event is None:
            medium_or_low_event = event

    # High magnitude event with significant deviation - event-driven
    if high_magnitude_event and deviation_value is not None and abs(deviation_value) > 1.5:
        return {
            "context_type": "event_driven",
            "event_name": high_magnitude_event["event_name"],
            "event_date": high_magnitude_event["event_date"],
            "event_category": high_magnitude_event["event_category"],
            "adjusted_status": "Event-Driven Movement",
            "original_status": health_status,
            "interpretation": _build_interpretation(
                high_magnitude_event["event_category"],
                high_magnitude_event["event_name"]
            ),
            "suppress_from_priority_board": True,  # Strong event context
            "event_id": high_magnitude_event["event_id"]
        }

    # Medium/low magnitude or smaller deviation - partially explained
    context_event = high_magnitude_event or medium_or_low_event
    if context_event:
        return {
            "context_type": "partially_explained",
            "event_name": context_event["event_name"],
            "event_date": context_event["event_date"],
            "event_category": context_event["event_category"],
            "adjusted_status": "Partially Context-Explained",
            "original_status": health_status,
            "interpretation": _build_interpretation(
                context_event["event_category"],
                context_event["event_name"]
            ),
            "suppress_from_priority_board": False,  # Still needs attention
            "event_id": context_event["event_id"]
        }

    # Fallback - unexplained
    return {
        "context_type": "unexplained",
        "suppress_from_priority_board": False
    }
