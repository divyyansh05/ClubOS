from __future__ import annotations
import enum
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import String, Integer, Float, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class AlertBase(DeclarativeBase):
    pass


class AlertType(str, enum.Enum):
    NEW_IN_TOP_N = "new_in_top_n"
    RANK_JUMPED_INTO_TOP = "rank_jumped_into_top"
    RANK_DROPPED_SIGNIFICANTLY = "rank_dropped_significantly"
    SCORE_JUMP = "score_jump"
    DROPPED_OUT = "dropped_out_of_top_n"
    PERSISTENT_TOP = "persistent_top"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class WatchdogAlertORM(AlertBase):
    __tablename__ = "watchdog_alerts"

    alert_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    current_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_current: Mapped[float] = mapped_column(Float, nullable=False)
    score_previous: Mapped[float | None] = mapped_column(Float, nullable=True)
    triggered_by_rule: Mapped[str] = mapped_column(String(100), nullable=False)
    context_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class WatchdogAlertCreate(BaseModel):
    alert_id: str
    metric_name: str
    alert_type: AlertType
    severity: AlertSeverity
    current_rank: int
    previous_rank: int | None = None
    rank_delta: int | None = None
    score_current: float
    score_previous: float | None = None
    triggered_by_rule: str
    context_snapshot: str
    source: str
    run_id: str


class WatchdogAlertRead(WatchdogAlertCreate):
    created_at: datetime
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None

    model_config = {"from_attributes": True}
