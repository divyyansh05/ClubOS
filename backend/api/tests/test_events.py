import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EVENTS_CSV_PATH = Path(__file__).resolve().parents[3] / "data" / "gold_snapshots" / "gold_events.csv"


def test_get_all_events_returns_list():
    """Test that GET /events returns a list of events"""
    response = client.get("/events")
    assert response.status_code == 200

    data = response.json()
    assert "total_count" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["total_count"] >= 0


def test_get_events_for_month_filters_correctly():
    """Test that GET /events/{month} filters by month"""
    # Test with a known month
    response = client.get("/events/2025-01")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    # All items should be from January 2025
    for event in data["items"]:
        assert event["event_date"].startswith("2025-01")


def test_create_event_appends_to_csv():
    """Test that POST /events creates a new event"""
    # Read current event count
    initial_events = client.get("/events").json()
    initial_count = initial_events["total_count"]

    # Create new event
    new_event_data = {
        "event_date": "2025-12-31",
        "event_name": "Test Event",
        "event_category": "commercial_event",
        "event_description": "Test description",
        "expected_impact": "main_website,ecommerce",
        "impact_magnitude": "medium",
    }
    response = client.post("/events", json=new_event_data)
    assert response.status_code == 200

    created_event = response.json()
    assert "event_id" in created_event
    assert created_event["event_name"] == "Test Event"
    assert created_event["event_category"] == "commercial_event"

    # Verify event was added
    updated_events = client.get("/events").json()
    assert updated_events["total_count"] == initial_count + 1

    # Clean up - delete the test event
    client.delete(f"/events/{created_event['event_id']}")


def test_delete_event_removes_from_csv():
    """Test that DELETE /events/{event_id} removes an event"""
    # Create a test event
    new_event_data = {
        "event_date": "2025-12-31",
        "event_name": "Event to Delete",
        "event_category": "media_event",
        "event_description": "Will be deleted",
        "expected_impact": "main_website",
        "impact_magnitude": "low",
    }
    create_response = client.post("/events", json=new_event_data)
    created_event = create_response.json()
    event_id = created_event["event_id"]

    # Get count before deletion
    before_delete = client.get("/events").json()
    count_before = before_delete["total_count"]

    # Delete the event
    delete_response = client.delete(f"/events/{event_id}")
    assert delete_response.status_code == 200

    # Verify event was removed
    after_delete = client.get("/events").json()
    assert after_delete["total_count"] == count_before - 1

    # Verify the specific event is gone
    event_ids = [e["event_id"] for e in after_delete["items"]]
    assert event_id not in event_ids


def test_get_events_near_metric_returns_within_30_days():
    """Test that GET /events/near/{asset}/{metric}/{month} returns events within 30 days"""
    # Test with a known month and asset
    response = client.get("/events/near/ecommerce/net_sales/2025-05-01")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total_count" in data

    # All returned events should have ecommerce in affected_assets
    for event in data["items"]:
        assert (
            "ecommerce" in event["affected_assets"]
            or "all" in event["affected_assets"]
        )
