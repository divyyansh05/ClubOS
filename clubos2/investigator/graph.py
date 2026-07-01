from __future__ import annotations
import logging
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from clubos2.investigator.state import InvestigatorState
from clubos2.investigator.tools import INVESTIGATOR_TOOLS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = Path("prompts/investigator_v1.md")


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text()


def build_llm():
    """Build Claude bound with Investigator tools for LangGraph."""
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0,
        max_tokens=4096,
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


def tool_node_wrapper(state: InvestigatorState) -> dict:
    """Execute tools and track tool calls + reasoning trace."""
    base_tool_node = ToolNode(INVESTIGATOR_TOOLS)
    result = base_tool_node.invoke(state)

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
