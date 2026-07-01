from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    QUANTITATIVE = "quantitative"
    NARRATIVE = "narrative"
    MIXED = "mixed"
    AMBIGUOUS = "ambiguous"
    UNANSWERABLE = "unanswerable"
    WATCHDOG_RUN = "watchdog_run"
    INVESTIGATION = "investigation"


class ExpectedConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GoldenEntry(BaseModel):
    id: str = Field(..., description="Stable ID like 'gq_001'")
    question: str = Field(..., min_length=10, max_length=500)
    question_type: QuestionType
    expected_answer_facts: list[str] = Field(
        default_factory=list,
        description="Key facts/numbers that must appear in the answer. Empty for UNANSWERABLE.",
    )
    expected_metric_names: list[str] = Field(
        default_factory=list,
        description="Which metrics from the registry the Scout should query",
    )
    required_citation_sources: list[str] = Field(
        default_factory=list,
        description="Source files/tables that MUST be cited. e.g. 'priority_board.md'",
    )
    expected_confidence: ExpectedConfidence
    must_state_assumption: bool = False
    must_refuse: bool = False
    tempts_fabrication: bool = False
    tempts_injection: bool = False
    scenario_setup: str | None = None  # Only for WATCHDOG_RUN entries; describes initial state
    author: str
    created_at: str
    notes: str = ""


class GoldenSet(BaseModel):
    version: str
    entries: list[GoldenEntry]

    def by_type(self, qt: QuestionType) -> list[GoldenEntry]:
        return [e for e in self.entries if e.question_type == qt]
