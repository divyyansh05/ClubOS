import os
import json
import requests
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

def _get_category_emoji(category: str) -> str:
    mapping = {
        "conversion_weakness": "🛒",
        "benchmark_underperformance": "📊",
        "engagement_opportunity": "📈",
        "social_engagement": "📱",
        "revenue_decline": "💰",
        "event_context": "📅",
    }
    return mapping.get(category, "⚠️")

def _format_slack_message(
    top_priorities: list,
    rank_changes: list,
    month: str,
    app_url: str = ""
) -> dict:
    """Build a rich Slack message block."""

    # Header
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📋 ClubOS Priority Update — {month}"
            }
        },
        {"type": "divider"}
    ]

    # Rank changes section
    if rank_changes:
        change_lines = []
        for change in rank_changes[:3]:
            direction = "🔺" if change["direction"] == "up" else "🔻"
            change_lines.append(
                f"{direction} *{change['metric']}* "
                f"({change['asset']}) "
                f"#{change['old_rank']} → #{change['new_rank']}"
            )
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Rank Changes This Month:*\n" +
                        "\n".join(change_lines)
            }
        })
        blocks.append({"type": "divider"})

    # Top 5 priorities
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Current Top 5 Priorities:*"
        }
    })

    for p in top_priorities[:5]:
        emoji = _get_category_emoji(p.get("priority_category", ""))
        score = p.get("priority_score", 0)
        
        # Get important details, preferring summary text
        details = p.get("summary_text", "") or p.get("why_it_matters", "No details provided.")
        if len(details) > 120:
            details = details[:117] + "..."
            
        # Create deep link if app_url is configured, otherwise fallback to ID
        action_link = f"<{app_url}/priorities?id={p.get('priority_id', '')}|View Priority in ClubOS>" if app_url else f"`Priority ID: {p.get('priority_id', '')}`"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"{emoji} *#{p.get('priority_rank', '?')} {p.get('primary_metric', '')}* — _{p.get('asset_name', '').upper()}_\n"
                    f"> {details}\n"
                    f"Score: *{score:.2f}* | {action_link}"
                )
            }
        })

    blocks.append({"type": "divider"})

    # Footer with link
    footer_text = "ClubOS Monthly Digital Business Operating System"
    if app_url:
        footer_text += f" | <{app_url}/priorities|View Priority Board>"

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": footer_text
            }
        ]
    })

    return {
        "text": f"ClubOS Priority Update — {month}",
        "blocks": blocks
    }

def detect_rank_changes(
    current_priorities: list,
    previous_priorities: list,
    threshold: int = 2
) -> list:
    """Detect significant rank changes between two months."""
    changes = []

    current_map = {
        p["primary_metric"]: p["priority_rank"]
        for p in current_priorities
    }
    previous_map = {
        p["primary_metric"]: p["priority_rank"]
        for p in previous_priorities
    }

    for metric, current_rank in current_map.items():
        if metric in previous_map:
            old_rank = previous_map[metric]
            rank_change = old_rank - current_rank
            # Positive means moved up (worse — higher priority)
            if abs(rank_change) >= threshold:
                changes.append({
                    "metric": metric,
                    "asset": next(
                        (p["asset_name"] for p in current_priorities
                         if p["primary_metric"] == metric), ""
                    ),
                    "old_rank": old_rank,
                    "new_rank": current_rank,
                    "direction": "up" if rank_change > 0 else "down",
                    "change_magnitude": abs(rank_change)
                })
        else:
            # New entry in top 10
            changes.append({
                "metric": metric,
                "asset": next(
                    (p["asset_name"] for p in current_priorities
                     if p["primary_metric"] == metric), ""
                ),
                "old_rank": 99,
                "new_rank": current_rank,
                "direction": "up",
                "change_magnitude": 99
            })

    return sorted(
        changes,
        key=lambda x: x["change_magnitude"],
        reverse=True
    )

def send_priority_alert(
    current_priorities: list,
    previous_priorities: list,
    month: str,
    app_url: str = "",
    force: bool = False
) -> dict:
    """
    Send Slack alert if significant rank changes detected.
    Set force=True to send regardless of changes (for demo/testing).
    """
    if not SLACK_WEBHOOK_URL:
        return {
            "sent": False,
            "reason": "SLACK_WEBHOOK_URL not configured"
        }

    rank_changes = detect_rank_changes(
        current_priorities,
        previous_priorities
    )

    if not rank_changes and not force:
        return {
            "sent": False,
            "reason": "No significant rank changes detected"
        }

    message = _format_slack_message(
        top_priorities=current_priorities,
        rank_changes=rank_changes,
        month=month,
        app_url=app_url
    )

    try:
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json=message,
            timeout=10
        )
        resp.raise_for_status()
        logger.info(f"Slack alert sent for {month}")
        return {
            "sent": True,
            "month": month,
            "rank_changes": len(rank_changes),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Slack alert failed: {e}")
        return {
            "sent": False,
            "reason": str(e)
        }
