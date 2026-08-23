from __future__ import annotations
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class InvestigatorState(TypedDict):
    alert_id: str
    metric_name: str
    triggered_by: str
    max_steps: int
    messages: Annotated[list[BaseMessage], add_messages]
    step_count: int
    tools_called: list[str]
    reasoning_trace: list[dict]
    finding: dict | None
    finished: bool
