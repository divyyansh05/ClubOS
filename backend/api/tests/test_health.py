from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_asset_health_breakdown() -> None:
    """Test that /health/assets returns per-asset health breakdown (V1.6.1)."""
    response = client.get("/health/assets")
    assert response.status_code == 200

    data = response.json()
    assert "assets" in data

    assets = data["assets"]
    assert isinstance(assets, dict)

    # Should have at least main_website, ecommerce, streaming, fan_app
    assert "main_website" in assets or len(assets) > 0

    # Check structure of first asset (if any exist)
    if assets:
        first_asset = next(iter(assets.values()))
        assert "metric_count" in first_asset
        assert "good_count" in first_asset
        assert "review_count" in first_asset
        assert "stable_count" in first_asset
        assert "health_percentage" in first_asset

        # Validate health_percentage is 0-100
        assert 0 <= first_asset["health_percentage"] <= 100
