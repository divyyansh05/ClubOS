from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Confidence(str, Enum):
    HIGH = "high"  # all numbers cited, no ambiguity
    MEDIUM = "medium"  # some ambiguity resolved by default rule (note in assumptions)
    LOW = "low"  # partial answer or missing data


class Citation(BaseModel):
    claim: str  # the specific text being cited
    source: str  # which document or table
    section: str | None = None
    quote: str | None = None  # the exact text from source that supports the claim


class ScoutInput(BaseModel):
    question: str
    user_id: str | None = None  # for permission scoping later
    session_id: str | None = None  # for conversation memory later


class ScoutAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: Confidence
    assumptions_made: list[str] = Field(default_factory=list)
    metrics_queried: list[str] = Field(default_factory=list)
    chunks_retrieved: int = 0

    def has_uncited_numbers(self) -> bool:
        """Stub for guardrail check in Phase 1.5 — detects numbers in answer not in citations."""
        return False
