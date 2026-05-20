"""
Tests for Social Anomaly Detection (V1.6.5).

Tests anomaly detection, classification, and event confirmation workflow.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.services import social_service, event_service

client = TestClient(app)


def test_detect_anomalies_finds_spikes_above_2_std():
    """Test that detect_social_anomalies finds metrics >2 std from mean."""
    anomalies = social_service.detect_social_anomalies()

    assert isinstance(anomalies, list)

    # All returned anomalies should have abs(z_score) > 2.0
    for anomaly in anomalies:
        assert abs(anomaly.z_score) > 2.0, (
            f"Anomaly {anomaly.metric} in {anomaly.month} has z_score {anomaly.z_score:.2f}, "
            f"should be >2.0"
        )


def test_anomaly_has_required_fields():
    """Test that SocialAnomaly has all required fields."""
    anomalies = social_service.detect_social_anomalies()

    if not anomalies:
        # If no anomalies detected in test data, skip
        return

    anomaly = anomalies[0]

    # Required fields
    assert hasattr(anomaly, "month")
    assert hasattr(anomaly, "metric")
    assert hasattr(anomaly, "actual_value")
    assert hasattr(anomaly, "mean_value")
    assert hasattr(anomaly, "std_value")
    assert hasattr(anomaly, "z_score")
    assert hasattr(anomaly, "direction")
    assert hasattr(anomaly, "likely_cause")
    assert hasattr(anomaly, "candidate_event_name")
    assert hasattr(anomaly, "candidate_category")
    assert hasattr(anomaly, "is_confirmed")
    assert hasattr(anomaly, "confidence_level")

    # Type checks
    assert isinstance(anomaly.month, str)
    assert isinstance(anomaly.metric, str)
    assert isinstance(anomaly.z_score, float)
    assert anomaly.direction in ["spike", "drop"]
    assert anomaly.confidence_level in ["high", "medium", "low"]
    assert isinstance(anomaly.is_confirmed, bool)


def test_anomaly_classification_by_metric_combination():
    """Test that anomaly classification produces valid categories."""
    anomalies = social_service.detect_social_anomalies()

    valid_causes = [
        "match_result_win",
        "match_result_loss",
        "trophy_win",
        "media_event",
        "player_signing",
        "injury_news",
        "poor_match_result"
    ]

    valid_categories = [
        "match_result_win",
        "match_result_loss",
        "trophy_win",
        "media_event",
        "player_signing",
        "injury_news"
    ]

    for anomaly in anomalies:
        assert anomaly.likely_cause in valid_causes, (
            f"Anomaly has invalid likely_cause: {anomaly.likely_cause}"
        )
        assert anomaly.candidate_category in valid_categories, (
            f"Anomaly has invalid candidate_category: {anomaly.candidate_category}"
        )


def test_unconfirmed_returns_only_events_not_in_calendar():
    """Test that get_unconfirmed_social_anomalies filters out existing events."""
    all_anomalies = social_service.detect_social_anomalies()
    unconfirmed = social_service.get_unconfirmed_social_anomalies()

    # Unconfirmed should be subset of all anomalies
    assert len(unconfirmed) <= len(all_anomalies)

    # Each unconfirmed anomaly should not have a matching event
    for anomaly in unconfirmed:
        has_event = social_service.check_if_event_exists_for_anomaly(
            anomaly.month,
            anomaly.likely_cause
        )
        assert not has_event, (
            f"Anomaly {anomaly.month} with cause {anomaly.likely_cause} "
            f"is in unconfirmed list but has matching event"
        )


def test_anomalies_endpoint_returns_200():
    """Test GET /social/anomalies returns 200."""
    response = client.get("/social/anomalies")
    assert response.status_code == 200

    data = response.json()
    assert "total_count" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_unconfirmed_anomalies_endpoint_returns_200():
    """Test GET /social/anomalies/unconfirmed returns 200."""
    response = client.get("/social/anomalies/unconfirmed")
    assert response.status_code == 200

    data = response.json()
    assert "total_count" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_confirm_anomaly_creates_event_in_calendar():
    """Test POST /social/anomalies/{month}/confirm creates event."""
    # Get unconfirmed anomalies
    unconfirmed_response = client.get("/social/anomalies/unconfirmed")
    unconfirmed = unconfirmed_response.json()

    if unconfirmed["total_count"] == 0:
        # No unconfirmed anomalies to test with
        return

    # Take first unconfirmed anomaly
    anomaly = unconfirmed["items"][0]
    month = anomaly["month"][:7]  # YYYY-MM

    # Count events before
    events_before_response = client.get(f"/events/{month}")
    events_before = events_before_response.json()
    count_before = events_before["total_count"]

    # Confirm anomaly
    confirm_request = {
        "confirmed_name": f"Test Event {month}",
        "confirmed_category": anomaly["candidate_category"],
        "description": f"Test event from anomaly confirmation: {anomaly['metric']}",
        "impact_magnitude": "medium",
        "affected_assets": "social_media"
    }

    confirm_response = client.post(
        f"/social/anomalies/{month}/confirm",
        json=confirm_request
    )
    assert confirm_response.status_code == 200

    created_event = confirm_response.json()
    assert "event_id" in created_event
    assert created_event["event_name"] == confirm_request["confirmed_name"]
    assert created_event["event_category"] == confirm_request["confirmed_category"]

    # Verify event was added to calendar
    events_after_response = client.get(f"/events/{month}")
    events_after = events_after_response.json()
    count_after = events_after["total_count"]

    assert count_after == count_before + 1, (
        f"Expected event count to increase by 1, but got {count_before} -> {count_after}"
    )

    # Clean up: delete the test event
    client.delete(f"/events/{created_event['event_id']}")


def test_dismiss_anomaly_returns_success():
    """Test POST /social/anomalies/{month}/dismiss returns success."""
    # Get unconfirmed anomalies
    unconfirmed_response = client.get("/social/anomalies/unconfirmed")
    unconfirmed = unconfirmed_response.json()

    if unconfirmed["total_count"] == 0:
        # No unconfirmed anomalies to test with, use a dummy month
        month = "2025-01"
    else:
        anomaly = unconfirmed["items"][0]
        month = anomaly["month"][:7]  # YYYY-MM

    response = client.post(f"/social/anomalies/{month}/dismiss")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data


def test_anomaly_confidence_level_based_on_z_score():
    """Test that confidence_level is correctly assigned based on z_score."""
    anomalies = social_service.detect_social_anomalies()

    for anomaly in anomalies:
        abs_z = abs(anomaly.z_score)

        if abs_z > 3.0:
            assert anomaly.confidence_level == "high", (
                f"Anomaly with z_score {anomaly.z_score:.2f} should have 'high' confidence"
            )
        elif abs_z > 2.5:
            assert anomaly.confidence_level == "medium", (
                f"Anomaly with z_score {anomaly.z_score:.2f} should have 'medium' confidence"
            )
        else:
            assert anomaly.confidence_level == "low", (
                f"Anomaly with z_score {anomaly.z_score:.2f} should have 'low' confidence"
            )


def test_candidate_event_name_format():
    """Test that candidate_event_name follows expected format."""
    anomalies = social_service.detect_social_anomalies()

    for anomaly in anomalies:
        # Should contain month YYYY-MM
        assert anomaly.month[:7] in anomaly.candidate_event_name, (
            f"Candidate event name '{anomaly.candidate_event_name}' should contain month {anomaly.month[:7]}"
        )

        # Should contain direction (Spike or Drop)
        assert "Spike" in anomaly.candidate_event_name or "Drop" in anomaly.candidate_event_name, (
            f"Candidate event name '{anomaly.candidate_event_name}' should contain 'Spike' or 'Drop'"
        )
