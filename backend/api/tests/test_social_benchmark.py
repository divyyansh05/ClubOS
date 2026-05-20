"""
Tests for Social Peer Benchmarking (V1.6.3)
"""

from fastapi.testclient import TestClient
from app.main import app
from app.services.social_benchmark_service import (
    get_social_peer_benchmark,
    get_social_benchmark_trend,
    get_social_benchmark_summary,
)

client = TestClient(app)


def test_social_benchmark_returns_10_clubs():
    """Test that social benchmark returns data for all 10 clubs"""
    result = get_social_peer_benchmark("avg_engagement_per_post")

    assert result is not None
    assert "clubs" in result
    assert result["club_count"] == 10
    assert len(result["clubs"]) == 10


def test_real_madrid_rank_is_correct_for_avg_engagement():
    """Test that Real Madrid's rank is computed correctly"""
    result = get_social_peer_benchmark("avg_engagement_per_post")

    assert result["rm_rank"] is not None
    assert 1 <= result["rm_rank"] <= 10
    assert result["rm_value"] is not None
    assert result["rm_value"] > 0

    # Verify Real Madrid is in the clubs list
    rm_club = next((c for c in result["clubs"] if c["is_real_madrid"]), None)
    assert rm_club is not None
    assert rm_club["rank"] == result["rm_rank"]
    assert rm_club["value"] == result["rm_value"]


def test_peer_median_computed_correctly():
    """Test that peer median is computed correctly (middle value of sorted list)"""
    result = get_social_peer_benchmark("avg_engagement_per_post")

    assert result["peer_median"] is not None
    assert result["peer_median"] > 0

    # Verify median is actually the middle value
    values = sorted([c["value"] for c in result["clubs"]])
    n = len(values)
    if n % 2 == 0:
        expected_median = (values[n // 2 - 1] + values[n // 2]) / 2
    else:
        expected_median = values[n // 2]

    assert abs(result["peer_median"] - expected_median) < 0.01


def test_benchmark_trend_returns_12_months():
    """Test that benchmark trend returns 12 months of data"""
    result = get_social_benchmark_trend("avg_engagement_per_post")

    assert result is not None
    assert "months" in result
    assert len(result["months"]) == 12

    # Verify each month has rm_rank
    for month_data in result["months"]:
        assert "month" in month_data
        assert "rm_rank" in month_data
        if month_data["rm_rank"]:  # May be None if data missing
            assert 1 <= month_data["rm_rank"] <= 10


def test_social_benchmark_summary_returns_all_metrics():
    """Test that summary endpoint returns all 4 metrics"""
    result = get_social_benchmark_summary()

    assert result is not None
    assert "metrics" in result
    assert len(result["metrics"]) >= 4  # At least 4 metrics

    # Check that expected metrics are present
    metric_names = [m["metric"] for m in result["metrics"]]
    assert "avg_engagement_per_post" in metric_names
    assert "total_engagement" in metric_names

    # Each metric should have a status
    for metric_data in result["metrics"]:
        assert "status" in metric_data
        assert metric_data["status"] in ["leader", "above_median", "below_median"]


def test_social_benchmark_endpoint_returns_200():
    """Test that GET /benchmark/social/{metric} returns 200"""
    response = client.get("/benchmark/social/avg_engagement_per_post")
    assert response.status_code == 200

    data = response.json()
    assert "clubs" in data
    assert "rm_rank" in data
    assert "peer_median" in data


def test_social_benchmark_trend_endpoint_returns_200():
    """Test that GET /benchmark/social/{metric}/trend returns 200"""
    response = client.get("/benchmark/social/avg_engagement_per_post/trend")
    assert response.status_code == 200

    data = response.json()
    assert "months" in data
    assert len(data["months"]) > 0


def test_social_benchmark_summary_endpoint_returns_200():
    """Test that GET /benchmark/social/summary returns 200"""
    response = client.get("/benchmark/social/summary")
    assert response.status_code == 200

    data = response.json()
    assert "metrics" in data
    assert len(data["metrics"]) > 0


def test_all_clubs_have_ranks():
    """Test that all 10 clubs are assigned valid ranks"""
    result = get_social_peer_benchmark("avg_engagement_per_post")

    ranks = [c["rank"] for c in result["clubs"]]
    assert len(ranks) == 10
    assert sorted(ranks) == list(range(1, 11))  # Should be 1, 2, 3, ..., 10


def test_leader_is_rank_1():
    """Test that the peer leader is the club with rank 1"""
    result = get_social_peer_benchmark("avg_engagement_per_post")

    leader_club = next((c for c in result["clubs"] if c["rank"] == 1), None)
    assert leader_club is not None
    assert result["peer_leader_club"] == leader_club["club"]
    assert result["peer_leader_value"] == leader_club["value"]
