import csv
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


EVENTS_CSV_PATH = Path(__file__).resolve().parents[4] / "data" / "gold_snapshots" / "gold_events.csv"


def _read_events_csv() -> list[dict]:
    """Read all events from gold_events.csv"""
    if not EVENTS_CSV_PATH.exists():
        return []

    events = []
    with open(EVENTS_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse affected_assets from expected_impact (comma-separated)
            affected_assets = [asset.strip() for asset in row["expected_impact"].split(",") if asset.strip()]

            events.append({
                "event_id": row["event_id"],
                "event_date": row["event_date"],
                "event_name": row["event_name"],
                "event_category": row["event_category"],
                "event_description": row["event_description"],
                "expected_impact": row["expected_impact"],
                "affected_assets": affected_assets,
                "impact_magnitude": row["impact_magnitude"],
            })

    return events


def _write_events_csv(events: list[dict]) -> None:
    """Write all events to gold_events.csv"""
    with open(EVENTS_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["event_id", "event_date", "event_name", "event_category",
                      "event_description", "expected_impact", "affected_assets", "impact_magnitude"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for event in events:
            # Convert affected_assets list back to comma-separated string for CSV
            row = event.copy()
            if isinstance(row.get("affected_assets"), list):
                row["expected_impact"] = ",".join(row["affected_assets"])
                row.pop("affected_assets", None)
            writer.writerow(row)


def get_all_events() -> dict:
    """Get all events, sorted by date descending"""
    events = _read_events_csv()
    # Sort by event_date descending (most recent first)
    events.sort(key=lambda x: x["event_date"], reverse=True)

    return {
        "total_count": len(events),
        "items": events
    }


def get_events_in_range(start_date: str, end_date: str) -> dict:
    """Get events within a date range"""
    events = _read_events_csv()
    filtered = [
        e for e in events
        if start_date <= e["event_date"] <= end_date
    ]
    filtered.sort(key=lambda x: x["event_date"], reverse=True)

    return {
        "total_count": len(filtered),
        "items": filtered
    }


def get_events_for_month(month_str: str) -> dict:
    """Get events for a specific month (format: YYYY-MM)"""
    events = _read_events_csv()
    filtered = [
        e for e in events
        if e["event_date"].startswith(month_str)
    ]
    filtered.sort(key=lambda x: x["event_date"], reverse=True)

    return {
        "total_count": len(filtered),
        "items": filtered
    }


def create_event(event_data: dict) -> dict:
    """Create a new event and append to CSV"""
    events = _read_events_csv()

    # Generate new event_id
    event_id = f"evt_{str(uuid.uuid4())[:8]}"

    # Parse affected_assets from expected_impact
    affected_assets = [asset.strip() for asset in event_data["expected_impact"].split(",") if asset.strip()]

    new_event = {
        "event_id": event_id,
        "event_date": event_data["event_date"],
        "event_name": event_data["event_name"],
        "event_category": event_data["event_category"],
        "event_description": event_data["event_description"],
        "expected_impact": event_data["expected_impact"],
        "affected_assets": affected_assets,
        "impact_magnitude": event_data["impact_magnitude"],
    }

    events.append(new_event)
    _write_events_csv(events)

    return new_event


def delete_event(event_id: str) -> bool:
    """Delete an event from CSV"""
    events = _read_events_csv()
    original_count = len(events)

    events = [e for e in events if e["event_id"] != event_id]

    if len(events) == original_count:
        return False  # Event not found

    _write_events_csv(events)
    return True


def get_events_near_metric_movement(asset: str, metric: str, month_str: str) -> dict:
    """Get events within 30 days of a specific month for a specific asset"""
    events = _read_events_csv()

    # Parse month string (YYYY-MM or YYYY-MM-DD)
    if len(month_str) == 7:  # YYYY-MM
        month_date = datetime.strptime(month_str + "-01", "%Y-%m-%d")
    else:
        month_date = datetime.strptime(month_str, "%Y-%m-%d")

    # Define 30-day window around the month
    start_date = month_date - timedelta(days=30)
    end_date = month_date + timedelta(days=30)

    filtered = []
    for e in events:
        event_date = datetime.strptime(e["event_date"], "%Y-%m-%d")

        # Check if event is within date window
        if start_date <= event_date <= end_date:
            # Check if asset is affected
            if asset in e["affected_assets"] or "all" in e["affected_assets"]:
                filtered.append(e)

    filtered.sort(key=lambda x: x["event_date"])

    return {
        "total_count": len(filtered),
        "items": filtered
    }
