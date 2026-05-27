import os
import requests
from datetime import datetime
from base_connector import BaseConnector, ConnectorStatus, ConnectorResult

REAL_MADRID_CHANNEL_ID = "UCgnj7FRt2VGdFMf5bBEnlKA"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

class YouTubeConnector(BaseConnector):
    connector_id = "youtube"
    name = "YouTube Data API v3"
    auth_type = "api_key"
    data_type = "streaming_performance"

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")

    def test_connection(self) -> ConnectorStatus:
        if not self.api_key:
            return ConnectorStatus(
                connector_id=self.connector_id,
                name=self.name,
                status="not_configured",
                last_sync=None,
                records_fetched=0,
                error_message="YOUTUBE_API_KEY environment variable not set",
                auth_type=self.auth_type,
                data_type=self.data_type
            )
        try:
            resp = requests.get(
                f"{YOUTUBE_API_BASE}/channels",
                params={
                    "part": "snippet,statistics",
                    "id": REAL_MADRID_CHANNEL_ID,
                    "key": self.api_key
                },
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("items"):
                channel = data["items"][0]["statistics"]
                return ConnectorStatus(
                    connector_id=self.connector_id,
                    name=self.name,
                    status="connected",
                    last_sync=datetime.utcnow(),
                    records_fetched=int(channel.get("videoCount", 0)),
                    error_message=None,
                    auth_type=self.auth_type,
                    data_type=self.data_type
                )
            else:
                return ConnectorStatus(
                    connector_id=self.connector_id,
                    name=self.name,
                    status="error",
                    last_sync=None,
                    records_fetched=0,
                    error_message="YouTube API returned no channel data",
                    auth_type=self.auth_type,
                    data_type=self.data_type
                )
        except Exception as e:
            return ConnectorStatus(
                connector_id=self.connector_id,
                name=self.name,
                status="error",
                last_sync=None,
                records_fetched=0,
                error_message=str(e),
                auth_type=self.auth_type,
                data_type=self.data_type
            )

    def fetch(self, days_back: int = 30) -> ConnectorResult:
        try:
            # Fetch channel statistics
            channel_resp = requests.get(
                f"{YOUTUBE_API_BASE}/channels",
                params={
                    "part": "statistics,snippet",
                    "id": REAL_MADRID_CHANNEL_ID,
                    "key": self.api_key
                },
                timeout=10
            )
            channel_resp.raise_for_status()
            channel_json = channel_resp.json()
            if not channel_json.get("items"):
                return ConnectorResult(
                    success=False,
                    records=[],
                    fetched_at=datetime.utcnow(),
                    error="No channel data found"
                )
            channel_data = channel_json["items"][0]

            # Fetch latest 10 videos
            videos_resp = requests.get(
                f"{YOUTUBE_API_BASE}/search",
                params={
                    "part": "snippet",
                    "channelId": REAL_MADRID_CHANNEL_ID,
                    "order": "date",
                    "maxResults": 10,
                    "type": "video",
                    "key": self.api_key
                },
                timeout=10
            )
            videos_resp.raise_for_status()
            video_ids = [
                item["id"]["videoId"]
                for item in videos_resp.json().get("items", [])
            ]

            # Fetch video statistics
            video_stats = []
            if video_ids:
                stats_resp = requests.get(
                    f"{YOUTUBE_API_BASE}/videos",
                    params={
                        "part": "statistics,snippet",
                        "id": ",".join(video_ids),
                        "key": self.api_key
                    },
                    timeout=10
                )
                stats_resp.raise_for_status()
                video_stats = stats_resp.json().get("items", [])

            records = {
                "channel": channel_data,
                "videos": video_stats,
                "fetched_at": datetime.utcnow().isoformat()
            }

            return ConnectorResult(
                success=True,
                records=[records],
                fetched_at=datetime.utcnow()
            )

        except Exception as e:
            return ConnectorResult(
                success=False,
                records=[],
                fetched_at=datetime.utcnow(),
                error=str(e)
            )

    def to_metric_rows(self, records: list) -> list[dict]:
        if not records:
            return []
        data = records[0]
        channel = data["channel"]["statistics"]
        videos = data["videos"]

        rows = [
            {
                "metric": "subscriber_count",
                "label": "Subscribers",
                "value": int(channel.get("subscriberCount", 0)),
                "unit": "count",
                "source": "YouTube Channel API"
            },
            {
                "metric": "total_views",
                "label": "Total Channel Views",
                "value": int(channel.get("viewCount", 0)),
                "unit": "count",
                "source": "YouTube Channel API"
            },
            {
                "metric": "video_count",
                "label": "Total Videos Published",
                "value": int(channel.get("videoCount", 0)),
                "unit": "count",
                "source": "YouTube Channel API"
            },
        ]

        # Add per-video stats for latest videos
        for video in videos[:5]:
            stats = video.get("statistics", {})
            title = video["snippet"]["title"][:40]
            rows.append({
                "metric": "video_views",
                "label": f"Views: {title}",
                "value": int(stats.get("viewCount", 0)),
                "unit": "views",
                "source": "YouTube Video API",
                "video_id": video["id"],
                "published_at": video["snippet"]["publishedAt"]
            })

        return rows
