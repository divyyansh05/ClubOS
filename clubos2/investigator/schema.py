from __future__ import annotations
import json
from datetime import datetime
from enum import Enum
from typing import Any

import sqlalchemy as sa
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from clubos2.agents.scout_schemas import Citation


class InvestigationStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Base(DeclarativeBase):
    pass


class InvestigationORM(Base):
    __tablename__ = "investigations"

    investigation_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    alert_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    metric_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    triggered_by: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="running")
    cause_hypothesis: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    confidence: Mapped[str | None] = mapped_column(sa.String(10), nullable=True)
    evidence_summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    citations: Mapped[str] = mapped_column(sa.Text, nullable=False, default="[]")
    reasoning_trace: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    tools_called: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    total_steps: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    latency_seconds: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    trace_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime, nullable=True)


class InvestigationCreate(BaseModel):
    investigation_id: str
    alert_id: str
    metric_name: str
    triggered_by: str
    started_at: datetime


class InvestigationRead(BaseModel):
    model_config = {"from_attributes": True}

    investigation_id: str
    alert_id: str
    metric_name: str
    triggered_by: str
    status: InvestigationStatus
    cause_hypothesis: str | None = None
    confidence: Confidence | None = None
    evidence_summary: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    reasoning_trace: list[dict] = Field(default_factory=list)
    tools_called: list[str] = Field(default_factory=list)
    total_steps: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    latency_seconds: float | None = None
    trace_url: str | None = None
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, data: Any) -> Any:
        if hasattr(data, "__dict__"):
            # ORM object
            citations_raw = getattr(data, "citations", "[]") or "[]"
            reasoning_raw = getattr(data, "reasoning_trace", "[]") or "[]"
            tools_raw = getattr(data, "tools_called", "[]") or "[]"
            d = {c.key: getattr(data, c.key) for c in data.__table__.columns}
            d["citations"] = json.loads(citations_raw) if isinstance(citations_raw, str) else citations_raw
            d["reasoning_trace"] = json.loads(reasoning_raw) if isinstance(reasoning_raw, str) else reasoning_raw
            d["tools_called"] = json.loads(tools_raw) if isinstance(tools_raw, str) else tools_raw
            return d
        return data


class InvestigationUpdate(BaseModel):
    status: InvestigationStatus | None = None
    cause_hypothesis: str | None = None
    confidence: str | None = None
    evidence_summary: str | None = None
    citations: list[Citation] | None = None
    reasoning_trace: list[dict] | None = None
    tools_called: list[str] | None = None
    total_steps: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    latency_seconds: float | None = None
    trace_url: str | None = None
    error_message: str | None = None
    completed_at: datetime | None = None
