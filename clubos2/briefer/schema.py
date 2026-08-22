from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any

import sqlalchemy as sa
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from clubos2.agents.scout_schemas import Citation


class BriefingStatus(str, Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class BriefingType(str, Enum):
    MONTHLY_SCHEDULED = "monthly_scheduled"
    AD_HOC_SUMMARY = "ad_hoc_summary"
    METRIC_FOCUS = "metric_focus"
    INCIDENT_RECAP = "incident_recap"


class Base(DeclarativeBase):
    pass


class BriefingORM(Base):
    __tablename__ = "briefings"

    briefing_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    briefing_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    scope_key: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    period_start: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    triggered_by: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="generating")
    executive_summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    body_markdown: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    citations: Mapped[str] = mapped_column(sa.Text, nullable=False, default="[]")
    investigations_referenced: Mapped[str] = mapped_column(sa.Text, nullable=False, default="[]")
    alerts_referenced: Mapped[str] = mapped_column(sa.Text, nullable=False, default="[]")
    metrics_covered: Mapped[str] = mapped_column(sa.Text, nullable=False, default="[]")
    total_tokens: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    latency_seconds: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    trace_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    freshness_days: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=7)
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime, nullable=True)


class BriefingRead(BaseModel):
    model_config = {"from_attributes": True}

    briefing_id: str
    briefing_type: BriefingType
    scope_key: str
    period_start: datetime
    period_end: datetime
    triggered_by: str
    status: BriefingStatus
    executive_summary: str | None = None
    body_markdown: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    investigations_referenced: list[str] = Field(default_factory=list)
    alerts_referenced: list[str] = Field(default_factory=list)
    metrics_covered: list[str] = Field(default_factory=list)
    total_tokens: int | None = None
    cost_usd: float | None = None
    latency_seconds: float | None = None
    trace_url: str | None = None
    freshness_days: int = 7
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, data: Any) -> Any:
        if hasattr(data, "__dict__"):
            d = {c.key: getattr(data, c.key) for c in data.__table__.columns}
            for field in ("citations", "investigations_referenced", "alerts_referenced", "metrics_covered"):
                raw = d.get(field, "[]") or "[]"
                d[field] = json.loads(raw) if isinstance(raw, str) else raw
            return d
        return data
