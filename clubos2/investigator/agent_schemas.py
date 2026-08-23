from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from clubos2.agents.scout_schemas import Citation


class InvestigationConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReasoningStep(BaseModel):
    step_number: int
    thought: str = Field(..., description="What the agent reasoned at this step")
    action: str = Field(..., description="The tool called, or 'conclude'")
    action_input: dict = Field(default_factory=dict)
    observation: str = Field(default="")


class InvestigatorInput(BaseModel):
    alert_id: str
    metric_name: str
    triggered_by: str = "manual"
    max_steps: int = 8


class InvestigatorFinding(BaseModel):
    alert_id: str
    metric_name: str
    cause_hypothesis: str = Field(..., description="Primary explanation, 2-4 sentences")
    confidence: InvestigationConfidence
    evidence_summary: str = Field(..., description="Bullet-list in markdown")
    citations: list[Citation]
    reasoning_trace: list[ReasoningStep]
    tools_called: list[str]
    total_steps: int
    is_seasonal_or_expected: bool = False
    data_gaps: list[str] = Field(default_factory=list)
