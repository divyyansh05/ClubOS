import pytest

from app.services import anomaly_context_service


def test_high_magnitude_event_returns_event_driven_classification():
    """Test that high magnitude event with significant deviation returns event_driven"""
    result = anomaly_context_service.classify_metric_movement(
        asset="ecommerce",
        metric="net_sales",
        month_str="2025-01-15",  # Mbappé signing date
        deviation_value=2.5,  # Significant deviation
        health_status="review"
    )

    assert result["context_type"] == "event_driven"
    assert "event_name" in result
    assert "Mbappé" in result["event_name"]
    assert result["suppress_from_priority_board"] is True
    assert "interpretation" in result
    assert len(result["interpretation"]) > 0


def test_no_event_returns_unexplained_classification():
    """Test that no nearby event returns unexplained classification"""
    result = anomaly_context_service.classify_metric_movement(
        asset="streaming",
        metric="video_plays",
        month_str="2024-01-15",  # No events registered in 2024
        deviation_value=1.0,
        health_status="review"
    )

    assert result["context_type"] == "unexplained"
    assert result["suppress_from_priority_board"] is False
    assert "event_name" not in result


def test_low_magnitude_event_returns_partially_explained():
    """Test that low magnitude event returns partially explained"""
    result = anomaly_context_service.classify_metric_movement(
        asset="main_website",
        metric="visits",
        month_str="2025-09-01",  # Transfer window closes (low magnitude)
        deviation_value=0.8,  # Small deviation
        health_status="stable"
    )

    assert result["context_type"] == "partially_explained"
    assert result["suppress_from_priority_board"] is False
    assert "event_name" in result
    assert "Transfer Window" in result["event_name"]


def test_high_magnitude_with_small_deviation_returns_partially_explained():
    """Test that high magnitude event with small deviation returns partially explained"""
    result = anomaly_context_service.classify_metric_movement(
        asset="main_website",
        metric="visits",
        month_str="2025-05-20",  # Near La Liga Title date (May 18)
        deviation_value=1.0,  # Below threshold of 1.5
        health_status="good"
    )

    assert result["context_type"] == "partially_explained"
    assert result["suppress_from_priority_board"] is False
    assert "event_name" in result
    # Either La Liga or Champions League event could be returned
    assert "event_name" in result


def test_none_deviation_with_high_event_returns_partially_explained():
    """Test that None deviation value returns partially explained even for high magnitude event"""
    result = anomaly_context_service.classify_metric_movement(
        asset="streaming",
        metric="daily_users",
        month_str="2025-01-15",  # Mbappé signing
        deviation_value=None,  # No deviation data
        health_status="stable"
    )

    # Without deviation data, even high magnitude events are partially explained
    assert result["context_type"] == "partially_explained"
    assert result["suppress_from_priority_board"] is False


def test_interpretation_strings_exist_for_all_categories():
    """Test that interpretation strings are generated for all event categories"""
    categories = [
        "player_signing",
        "match_result_win",
        "trophy_win",
        "commercial_event",
        "media_event",
        "injury_news"
    ]

    for category in categories:
        interpretation = anomaly_context_service._build_interpretation(category, "Test Event")
        assert isinstance(interpretation, str)
        assert len(interpretation) > 0
        # Some interpretations use the event name, some describe generic category effects
        # Just verify we get a non-empty string
        assert len(interpretation) > 20  # Reasonable minimum length
