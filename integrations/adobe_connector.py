from datetime import datetime
from base_connector import BaseConnector, ConnectorStatus, ConnectorResult

class AdobeAnalyticsConnector(BaseConnector):
    connector_id = "adobe"
    name = "Adobe Analytics"
    auth_type = "oauth"
    data_type = "website_traffic"

    def test_connection(self) -> ConnectorStatus:
        return ConnectorStatus(
            connector_id=self.connector_id,
            name=self.name,
            status="not_configured",
            last_sync=None,
            records_fetched=0,
            error_message="Adobe Analytics connector not yet configured.",
            auth_type=self.auth_type,
            data_type=self.data_type
        )

    def fetch(self, days_back: int = 30) -> ConnectorResult:
        raise NotImplementedError("Adobe connector stub")

    def to_metric_rows(self, records: list) -> list[dict]:
        return []
