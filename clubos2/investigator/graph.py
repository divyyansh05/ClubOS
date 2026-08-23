from __future__ import annotations
import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from clubos2.gateway.client import GatewaySettings
from clubos2.investigator.state import InvestigatorState
from clubos2.investigator.tools import INVESTIGATOR_TOOLS

logger = logging.getLogger(__name__)

_PROMPT_FILENAME = "investigator_v1.md"


def load_system_prompt() -> str:
    """Load the Investigator system prompt.

    Walks up from this module's directory looking for a prompts/ folder, so it
    works regardless of CWD (Cloud Run runs from /app/backend/api but the
    prompts/ dir sits at /app/prompts/). Falls back to CWD-relative path for
    legacy local-dev callers.
    """
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        candidate = parent / "prompts" / _PROMPT_FILENAME
        if candidate.exists():
            return candidate.read_text()
    fallback = Path("./prompts") / _PROMPT_FILENAME
    if fallback.exists():
        return fallback.read_text()
    raise FileNotFoundError(f"Could not find prompts/{_PROMPT_FILENAME}")


def build_llm():
    """Build the Investigator LLM bound with tools for LangGraph."""
    settings = GatewaySettings()
    llm = ChatOpenAI(
        model=settings.investigator_model,
        temperature=0,
        max_tokens=4096,
        api_key=settings.openai_api_key or None,
    )
    return llm.bind_tools(INVESTIGATOR_TOOLS)


def agent_node(state: InvestigatorState) -> dict:
    """Reasoning node: LLM reads conversation, decides what to do next."""
    llm = build_llm()

    if not state["messages"]:
        system_msg = SystemMessage(content=load_system_prompt())
        initial_user = HumanMessage(
            content=(
                f"Investigate the following alert:\n\n"
                f"- alert_id: {state['alert_id']}\n"
                f"- metric_name: {state['metric_name']}\n\n"
                f"Begin your investigation. Use tools as needed. When you have a confident "
                f"hypothesis, conclude by responding with a single JSON object matching the "
                f"InvestigatorFinding schema. Do not include any text outside the JSON."
            )
        )
        messages = [system_msg, initial_user]
    else:
        messages = state["messages"]

    response = llm.invoke(messages)
    return {
        "messages": [response],
        "step_count": state["step_count"] + 1,
    }


def should_continue(state: InvestigatorState) -> str:
    """Route to tools, end, or timeout."""
    if state["step_count"] >= state["max_steps"]:
        return "end_with_timeout"

    last_message = state["messages"][-1] if state["messages"] else None
    if not last_message:
        return "end"

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue_with_tools"

    return "end"


async def tool_node_wrapper(state: InvestigatorState) -> dict:
    """Execute tools and track tool calls + reasoning trace."""
    base_tool_node = ToolNode(INVESTIGATOR_TOOLS)
    result = await base_tool_node.ainvoke(state)

    last_ai_msg = state["messages"][-1]
    new_tools_called = list(state["tools_called"])
    new_trace = list(state["reasoning_trace"])

    if hasattr(last_ai_msg, "tool_calls"):
        for tc in last_ai_msg.tool_calls:
            new_tools_called.append(tc["name"])
            new_trace.append({
                "step_number": state["step_count"],
                "thought": last_ai_msg.content if isinstance(last_ai_msg.content, str) else "",
                "action": tc["name"],
                "action_input": tc.get("args", {}),
                "observation": "",
            })

    return {
        **result,
        "tools_called": new_tools_called,
        "reasoning_trace": new_trace,
    }


def build_graph(checkpointer=None):
    """Build the Investigator LangGraph.

    Args:
        checkpointer: Optional LangGraph checkpointer for STM persistence.
            Use SqliteSaver for production, MemorySaver for tests, None to disable.
    """
    graph = StateGraph(InvestigatorState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node_wrapper)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue_with_tools": "tools",
            "end": END,
            "end_with_timeout": END,
        },
    )
    graph.add_edge("tools", "agent")

    if checkpointer is None:
        return graph.compile()
    return graph.compile(checkpointer=checkpointer)
