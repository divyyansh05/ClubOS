from pydantic import BaseModel
from typing import Optional


class RefreshStatusResponse(BaseModel):
    status: str
    last_run_timestamp: Optional[str] = None
    latest_gold_month: Optional[str] = None
    required_failed_checks_count: int = 0
    message: str
