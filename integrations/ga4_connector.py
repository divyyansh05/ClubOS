import os
from datetime import datetime
from base_connector import BaseConnector, ConnectorStatus, ConnectorResult

class GA4Connector(BaseConnector):
    connector_id = "ga4"
    name = "Google Analytics 4"
    auth_type = "oauth"
    data_type = "website_traffic"

    def test_connection(self) -> ConnectorStatus:
        credentials = os.getenv("GA4_CREDENTIALS_PATH", "")
        return ConnectorStatus(
            connector_id=self.connector_id,
            name=self.name,
            status="not_configured" if not credentials else "error",
            last_sync=None,
            records_fetched=0,
            error_message=(
                "GA4 credentials not configured. "
                "Set GA4_CREDENTIALS_PATH environment variable "
                "with path to Google service account JSON."
            ) if not credentials else "GA4 integration requires credentials",
            auth_type=self.auth_type,
            data_type=self.data_type
        )

    def fetch(self, days_back: int = 30) -> ConnectorResult:
        raise NotImplementedError(
            "GA4 connector requires google-analytics-data package "
            "and service account credentials. "
            "See docs/architecture/daily_granularity_plan.md"
        )

    def to_metric_rows(self, records: list) -> list[dict]:
        return []
