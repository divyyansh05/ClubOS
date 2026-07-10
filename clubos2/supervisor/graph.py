from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from clubos2.gateway.client import GatewaySettings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class SupervisorState(TypedDict):
    user_query: str
    messages: Annotated[list[BaseMessage], add_messages]
    plan: list[dict] | None
    step_index: int
    step_results: list[dict]
    final_synthesis: str | None
    finished: bool


# ---------------------------------------------------------------------------
# Structured output models for the planner LLM
# ---------------------------------------------------------------------------

class SupervisorStep(BaseModel):
    model_config = {"extra": "forbid"}

    agent: Literal["scout", "investigator", "briefer"]
    purpose: str
    # Use specific optional fields instead of open dict to satisfy OpenAI strict schema
    question: str | None = None
    alert_id: str | None = None
    metric_name: str | None = None
    briefing_type: str | None = None
    scope_key: str | None = None
    period_start: str | None = None
    period_end: str | None = None


class SupervisorPlan(BaseModel):
    model_config = {"extra": "forbid"}

    reasoning: str
    steps: list[SupervisorStep]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SUPERVISOR_SYSTEM_PROMPT = """You are the ClubOS Supervisor. A user has asked a complex query
that requires coordination between multiple specialist agents. Your job is to plan the sequence
of agent invocations needed to answer.

Available agents:
- SCOUT: answers factual questions about specific metrics. Use for "what is X", "how much is Y".
- INVESTIGATOR: investigates root causes of alerts. Use for "why did X happen", "root cause of Y".
- BRIEFER: composes summaries and briefings. Use for "summarise last month", "brief me on Q1".

Rules:
1. Prefer FEWER steps. Simple queries need one step. Only add steps if genuinely required.
2. If a query is truly simple (just a Scout question), plan just one Scout step. Do not
   over-orchestrate.
3. If a query needs both facts and explanation, plan Scout FIRST, then Investigator (which
   can consume the Scout's findings via context).
4. If a query asks for a period summary, plan a single Briefer step. Do NOT combine with
   Scout/Investigator — Briefer already reads investigations directly.
5. Maximum 3 steps. If you need more, the query is too complex — plan only the most important
   3 steps and note the limitation in your reasoning.

Each step has these optional fields (set only the ones relevant to the agent):
- question: the question to ask Scout (agent=scout)
- alert_id: the alert identifier to investigate (agent=investigator)
- metric_name: metric name for the investigation (agent=investigator)
- briefing_type: type of briefing, e.g. "monthly_scheduled" (agent=briefer)
- scope_key: briefing scope key, e.g. "monthly:2026-03" (agent=briefer)
- period_start: ISO datetime string for start of period (agent=briefer)
- period_end: ISO datetime string for end of period (agent=briefer)

Output must be a JSON object matching the SupervisorPlan schema."""


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def _get_supervisor_model() -> str:
    return getattr(GatewaySettings(), "supervisor_model", "gpt-4o-mini")


def planner_node(state: SupervisorState) -> dict:
    """Ask an LLM to produce a step plan for the query."""
    llm = ChatOpenAI(model=_get_supervisor_model(), temperature=0,
                     api_key=GatewaySettings().openai_api_key or None)
    structured = llm.with_structured_output(SupervisorPlan)
    try:
        plan_result: SupervisorPlan = structured.invoke([
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=f"User query: {state['user_query']}\n\nProduce a plan."),
        ])
        steps = [step.model_dump() for step in plan_result.steps]
    except Exception as e:
        logger.warning(f"Planner LLM failed: {e}. Defaulting to empty plan.")
        steps = []

    return {
        "plan": steps,
        "step_index": 0,
    }


async def executor_node(state: SupervisorState) -> dict:
    """Execute the next step in the plan."""
    plan = state["plan"] or []
    idx = state["step_index"]

    if idx >= len(plan):
        return {"finished": True}

    step = plan[idx]
    agent = step["agent"]
    result: dict | None = None

    try:
        if agent == "scout":
            from clubos2.agents.scout import run_scout
            from clubos2.agents.scout_schemas import ScoutInput
            answer = await run_scout(ScoutInput(question=step.get("question") or state["user_query"]))
            result = {"agent": "scout", "output": answer.model_dump(mode="json")}

        elif agent == "investigator":
            from clubos2.investigator.orchestrator import run_investigation
            from clubos2.investigator.agent_schemas import InvestigatorInput
            alert_id = step.get("alert_id")
            if not alert_id:
                result = {"agent": "investigator", "error": "no alert_id provided", "output": None}
            else:
                inv_result = await run_investigation(InvestigatorInput(
                    alert_id=alert_id,
                    metric_name=step.get("metric_name") or "",
                    triggered_by="supervisor",
                ))
                result = {"agent": "investigator", "output": inv_result.model_dump(mode="json")}

        elif agent == "briefer":
            from clubos2.briefer.orchestrator import run_briefing
            from clubos2.briefer.agent_schemas import BriefingInput, BriefingType
            period_start_str = step.get("period_start")
            period_end_str = step.get("period_end")
            if not period_start_str or not period_end_str:
                result = {"agent": "briefer", "error": "period_start and period_end required for briefer", "output": None}
            else:
                brf_input = BriefingInput(
                    briefing_type=BriefingType(step.get("briefing_type") or "ad_hoc_summary"),
                    scope_key=step.get("scope_key") or f"adhoc:{state['user_query'][:100]}",
                    period_start=datetime.fromisoformat(period_start_str),
                    period_end=datetime.fromisoformat(period_end_str),
                    triggered_by="supervisor",
                )
                brf_result = await run_briefing(brf_input)
                result = {"agent": "briefer", "output": brf_result.model_dump(mode="json")}

        else:
            result = {"agent": agent, "error": f"unknown agent type: {agent}", "output": None}

    except Exception as e:
        logger.warning(f"Executor step {idx} ({agent}) failed: {e}")
        result = {"agent": agent, "error": str(e), "output": None}

    new_results = list(state["step_results"]) + [result]
    return {
        "step_results": new_results,
        "step_index": idx + 1,
    }


def synthesis_node(state: SupervisorState) -> dict:
    """If multiple steps ran, synthesise into a coherent final answer.
    Single-step: skip synthesis and return the result directly."""
    if len(state["step_results"]) <= 1:
        return {"finished": True, "final_synthesis": None}

    llm = ChatOpenAI(model=_get_supervisor_model(), temperature=0,
                     api_key=GatewaySettings().openai_api_key or None)
    prompt = (
        f"The user asked: {state['user_query']}\n\n"
        f"The following specialist agents were invoked:\n"
        f"{json.dumps(state['step_results'], indent=2)}\n\n"
        "Synthesise a coherent, cited answer for the user. Preserve all citations from the "
        "underlying agents. Do not invent new facts. Keep response concise."
    )
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        synthesis = response.content
    except Exception as e:
        logger.warning(f"Synthesis LLM failed: {e}")
        synthesis = f"[Synthesis failed: {e}]"

    return {"final_synthesis": synthesis, "finished": True}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _route_executor(state: SupervisorState) -> str:
    plan = state["plan"] or []
    if state["step_index"] < len(plan):
        return "executor"
    return "synthesis"


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------

def build_supervisor_graph():
    """Build and compile the supervisor LangGraph."""
    graph = StateGraph(SupervisorState)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("synthesis", synthesis_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_conditional_edges(
        "executor",
        _route_executor,
        {"executor": "executor", "synthesis": "synthesis"},
    )
    graph.add_edge("synthesis", END)

    return graph.compile()
