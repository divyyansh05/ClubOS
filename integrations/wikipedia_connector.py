import requests
from datetime import datetime, timedelta
from base_connector import BaseConnector, ConnectorStatus, ConnectorResult

WIKI_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
ARTICLE = "Real_Madrid_C.F."
PROJECT = "en.wikipedia"

class WikipediaConnector(BaseConnector):
    connector_id = "wikipedia"
    name = "Wikipedia Pageviews API"
    auth_type = "none"
    data_type = "brand_attention_proxy"

    def test_connection(self) -> ConnectorStatus:
        try:
            yesterday = (datetime.utcnow() - timedelta(days=2)).strftime("%Y%m%d")
            resp = requests.get(
                f"{WIKI_API}/{PROJECT}/all-access/all-agents"
                f"/{ARTICLE}/daily/{yesterday}/{yesterday}",
                headers={"User-Agent": "ClubOS/1.0 (contact@clubos.ai)"},
                timeout=10
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            return ConnectorStatus(
                connector_id=self.connector_id,
                name=self.name,
                status="connected",
                last_sync=datetime.utcnow(),
                records_fetched=len(items),
                error_message=None,
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
            end = datetime.utcnow() - timedelta(days=1)
            start = end - timedelta(days=days_back)
            resp = requests.get(
                f"{WIKI_API}/{PROJECT}/all-access/all-agents"
                f"/{ARTICLE}/daily"
                f"/{start.strftime('%Y%m%d')}"
                f"/{end.strftime('%Y%m%d')}",
                headers={"User-Agent": "ClubOS/1.0"},
                timeout=15
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            return ConnectorResult(
                success=True,
                records=items,
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
        return [
            {
                "metric": "wikipedia_daily_pageviews",
                "label": f"Wikipedia Views — {r['timestamp'][:8]}",
                "value": r["views"],
                "date": r["timestamp"][:8],
                "unit": "pageviews",
                "source": "Wikipedia Pageviews API"
            }
            for r in records
        ]
