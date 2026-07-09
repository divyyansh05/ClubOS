from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from clubos2.agents.scout_schemas import Citation
from clubos2.briefer.schema import BriefingType


class BriefingInput(BaseModel):
    briefing_type: BriefingType
    scope_key: str
    period_start: datetime
    period_end: datetime
    triggered_by: str = "manual"
    freshness_days: int = 7
    force_regenerate: bool = False


class BriefingContent(BaseModel):
    """Structured output produced by the Briefer LLM."""

    executive_summary: str = Field(
        ...,
        description="3-5 sentence headline written for a busy Head of Data.",
    )
    body_markdown: str = Field(
        ...,
        description="Full briefing in markdown with section headers.",
    )
    citations: list[Citation]
    investigations_referenced: list[str] = Field(
        default_factory=list,
        description="investigation_ids drawn from in this briefing.",
    )
    alerts_referenced: list[str] = Field(
        default_factory=list,
        description="alert_ids referenced in this briefing.",
    )
    metrics_covered: list[str] = Field(
        default_factory=list,
        description="Canonical metric names discussed.",
    )


class BriefingRunResult(BaseModel):
    briefing_id: str
    briefing_type: BriefingType
    scope_key: str
    status: str  # 'completed' / 'failed' / 'cached'
    was_cached: bool
    content: BriefingContent | None
    latency_seconds: float
    total_tokens: int | None = None
    cost_usd: float | None = None
    trace_url: str | None = None
    error: str | None = None
