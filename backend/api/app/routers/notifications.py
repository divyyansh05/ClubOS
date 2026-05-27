from fastapi import APIRouter
import pandas as pd
import os
from app.services.notification_service import (
    send_priority_alert,
    detect_rank_changes
)
from app.config.settings import settings

router = APIRouter(prefix="/notifications", tags=["notifications"])

def _load_priorities(month: str = None) -> list:
    path = os.path.join(
        settings.clubos_gold_snapshot_dir,
        "gold_priority_board.csv"
    )
    df = pd.read_csv(path)
    if month:
        df = df[df["month"] == month]
    return df.to_dict(orient="records")

@router.post("/test-slack")
def test_slack_alert():
    """
    Send a test Slack alert using current priority data.
    Always sends regardless of rank changes (force=True).
    Use this for demo purposes.
    """
    all_priorities = _load_priorities()
    months = sorted(
        set(p["month"] for p in all_priorities),
        reverse=True
    )

    current = [p for p in all_priorities if p["month"] == months[0]]
    previous = [p for p in all_priorities if p["month"] == months[1]] \
        if len(months) > 1 else []

    result = send_priority_alert(
        current_priorities=current,
        previous_priorities=previous,
        month=months[0][:7],
        app_url=os.getenv("CLUBOS_APP_URL", ""),
        force=True
    )
    return result

@router.get("/status")
def notification_status():
    """Check if Slack webhook is configured."""
    import os
    webhook = os.getenv("SLACK_WEBHOOK_URL", "")
    return {
        "slack_configured": bool(webhook),
        "webhook_preview": (
            webhook[:30] + "..." if webhook else "not set"
        )
    }
