from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConnectorStatus:
    connector_id: str
    name: str
    status: str          # "connected" | "error" | "not_configured"
    last_sync: Optional[datetime]
    records_fetched: int
    error_message: Optional[str]
    auth_type: str       # "api_key" | "oauth" | "none"
    data_type: str       # what kind of data this returns

@dataclass
class ConnectorResult:
    success: bool
    records: list
    fetched_at: datetime
    error: Optional[str] = None

class BaseConnector(ABC):
    connector_id: str
    name: str
    auth_type: str
    data_type: str

    @abstractmethod
    def test_connection(self) -> ConnectorStatus:
        """Test if the connector can reach the API."""
        pass

    @abstractmethod
    def fetch(self, days_back: int = 30) -> ConnectorResult:
        """Fetch data from the API."""
        pass

    @abstractmethod
    def to_metric_rows(self, records: list) -> list[dict]:
        """Convert raw API records to ClubOS metric format."""
        pass
