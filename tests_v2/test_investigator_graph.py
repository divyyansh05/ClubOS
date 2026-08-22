from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage, ToolMessage


def _minimal_state(max_steps: int = 4) -> dict:
    return {
        "alert_id": "alrt_test",
        "metric_name": "streaming_daily_users",
        "triggered_by": "test",
        "max_steps": max_steps,
        "messages": [],
        "step_count": 0,
        "tools_called": [],
        "reasoning_trace": [],
        "finding": None,
        "finished": False,
    }


def test_build_graph_returns_compiled_graph():
    from clubos2.investigator.graph import build_graph
    graph = build_graph()
    assert graph is not None


def test_build_graph_with_memory_checkpointer():
    from clubos2.investigator.graph import build_graph
    from langgraph.checkpoint.memory import MemorySaver
    graph = build_graph(checkpointer=MemorySaver())
    assert graph is not None


def test_should_continue_routes_to_end_when_max_steps():
    from clubos2.investigator.graph import should_continue
    state = _minimal_state(max_steps=2)
    state["step_count"] = 2
    assert should_continue(state) == "end_with_timeout"


def test_should_continue_routes_to_tools_when_tool_call():
    from clubos2.investigator.graph import should_continue
    state = _minimal_state()
    state["step_count"] = 1
    mock_msg = MagicMock()
    mock_msg.tool_calls = [{"name": "get_metric_definition", "args": {}}]
    state["messages"] = [mock_msg]
    assert should_continue(state) == "continue_with_tools"


def test_should_continue_routes_to_end_when_no_tool_calls():
    from clubos2.investigator.graph import should_continue
    state = _minimal_state()
    state["step_count"] = 1
    mock_msg = MagicMock()
    mock_msg.tool_calls = []
    state["messages"] = [mock_msg]
    assert should_continue(state) == "end"


@pytest.mark.asyncio
async def test_graph_with_mocked_llm_terminates():
    """Graph terminates when mocked LLM returns a final answer (no tool calls)."""
    from clubos2.investigator.graph import build_graph
    from langgraph.checkpoint.memory import MemorySaver

    final_json = '{"alert_id": "alrt_test", "metric_name": "streaming_daily_users", "cause_hypothesis": "Test hypothesis.", "confidence": "low", "evidence_summary": "- Test", "citations": [], "reasoning_trace": [], "tools_called": [], "total_steps": 1}'
    final_msg = AIMessage(content=final_json, tool_calls=[])

    with patch("clubos2.investigator.graph.build_llm") as mock_build_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = final_msg
        mock_build_llm.return_value = mock_llm

        graph = build_graph(checkpointer=MemorySaver())
        state = _minimal_state()
        config = {"configurable": {"thread_id": "test_thread_1"}}
        result = await graph.ainvoke(state, config=config)

    assert result is not None
    assert len(result["messages"]) > 0
