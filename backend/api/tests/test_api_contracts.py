"""
API contract tests for core MVP endpoints.

Tests that:
1. Core endpoints return expected status codes
2. Response schemas match expected contracts
3. Data types are correct
4. Required fields are present
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_priorities_latest_contract() -> None:
    """Test /priorities/latest returns expected schema."""
    response = client.get("/priorities/latest")
    assert response.status_code == 200

    data = response.json()
    assert "latest_month" in data
    assert "items" in data
    assert isinstance(data["items"], list)

    if len(data["items"]) > 0:
        item = data["items"][0]
        assert "priority_id" in item
        assert "month" in item
        assert "title" in item
        assert "category" in item
        assert "score" in item
        assert "rank" in item
        assert "asset_name" in item
        assert "primary_metric" in item
        assert "summary_text" in item
        assert "why_it_matters" in item
        assert "suggested_next_investigation" in item
        assert isinstance(item["score"], (int, float))
        assert isinstance(item["rank"], int)


def test_priority_detail_contract() -> None:
    """Test /priorities/{id} returns expected schema or 404."""
    # Get a real priority ID first
    response = client.get("/priorities/latest")
    assert response.status_code == 200
    items = response.json()["items"]

    if len(items) > 0:
        priority_id = items[0]["priority_id"]
        detail_response = client.get(f"/priorities/{priority_id}")
        assert detail_response.status_code == 200

        detail = detail_response.json()
        assert "priority_id" in detail
        assert "supporting_metrics" in detail
        assert isinstance(detail["supporting_metrics"], dict)


def test_health_summary_contract() -> None:
    """Test /health/summary returns expected schema."""
    response = client.get("/health/summary")
    assert response.status_code == 200

    data = response.json()
    assert "latest_month" in data
    assert "metric_count" in data
    assert "good_count" in data
    assert "review_count" in data
    assert "stable_count" in data
    assert isinstance(data["metric_count"], int)
    assert isinstance(data["good_count"], int)
    assert isinstance(data["review_count"], int)
    assert isinstance(data["stable_count"], int)


def test_benchmark_contract() -> None:
    """Test /benchmark/{asset}/{metric} returns expected schema."""
    response = client.get("/benchmark/ecommerce/conversion_rate")
    assert response.status_code == 200

    data = response.json()
    assert "asset" in data
    assert "metric" in data
    assert "points" in data
    assert isinstance(data["points"], list)

    if len(data["points"]) > 0:
        point = data["points"][0]
        assert "month" in point
        assert "rm_value" in point
        assert "peer_median" in point
        assert "peer_leader_value" in point
        assert "rm_rank" in point
        assert "club_count" in point
        assert "raw_gap_to_peer_median" in point
        assert "gap_to_peer_median" in point
        assert "gap_to_leader" in point
        assert isinstance(point["rm_rank"], int)
        assert isinstance(point["club_count"], int)


def test_signals_contract() -> None:
    """Test /signals returns expected schema."""
    response = client.get("/signals")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)

    if len(data["items"]) > 0:
        signal = data["items"][0]
        assert "signal_id" in signal
        assert "source_asset" in signal
        assert "source_metric" in signal
        assert "target_asset" in signal
        assert "target_metric" in signal
        assert "lag_months" in signal
        assert "relationship_direction" in signal
        assert "strength_score" in signal
        assert "validation_status" in signal
        assert isinstance(signal["lag_months"], int)
        assert isinstance(signal["strength_score"], (int, float))


def test_briefing_latest_contract() -> None:
    """Test /briefing/latest returns expected schema."""
    response = client.get("/briefing/latest")
    assert response.status_code == 200

    data = response.json()
    assert "month" in data
    assert "top_priorities" in data
    assert "top_anomalies" in data
    assert "strongest_signals" in data
    assert isinstance(data["top_priorities"], list)
    assert isinstance(data["top_anomalies"], list)
    assert isinstance(data["strongest_signals"], list)

    if len(data["top_priorities"]) > 0:
        priority = data["top_priorities"][0]
        assert "priority_id" in priority
        assert "priority_rank" in priority
        assert "priority_title" in priority
        assert "priority_score" in priority

    if len(data["top_anomalies"]) > 0:
        anomaly = data["top_anomalies"][0]
        assert "anomaly_rank" in anomaly
        assert "asset_name" in anomaly
        assert "metric_name" in anomaly
        assert "metric_value" in anomaly
        assert "deviation_from_rolling_avg" in anomaly


def test_refresh_status_contract() -> None:
    """Test /refresh/status returns expected schema."""
    response = client.get("/refresh/status")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "latest_gold_month" in data
    assert "required_failed_checks_count" in data
    assert isinstance(data["required_failed_checks_count"], int)
    # last_run_timestamp is optional
    if "last_run_timestamp" in data:
        assert isinstance(data["last_run_timestamp"], str)
