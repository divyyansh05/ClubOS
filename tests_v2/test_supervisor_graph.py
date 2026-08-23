from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from clubos2.supervisor.graph import (
    SupervisorPlan,
    SupervisorState,
    SupervisorStep,
    build_supervisor_graph,
    executor_node,
    planner_node,
    synthesis_node,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_state(**overrides) -> SupervisorState:
    state: SupervisorState = {
        "user_query": "test query",
        "messages": [],
        "plan": None,
        "step_index": 0,
        "step_results": [],
        "final_synthesis": None,
        "finished": False,
    }
    state.update(overrides)
    return state


def _mock_scout_answer():
    from clubos2.agents.scout_schemas import ScoutAnswer, Citation
    return ScoutAnswer(
        answer="Streaming daily users is 50,000.",
        metric_name="streaming_daily_users",
        value=50000.0,
        unit="users",
        citations=[Citation(claim="50k users", source="metric_registry", section=None, quote=None)],
        confidence="high",
        caveat=None,
    )


# ---------------------------------------------------------------------------
# build_supervisor_graph — structural check
# ---------------------------------------------------------------------------

def test_build_supervisor_graph_returns_compiled_graph():
    graph = build_supervisor_graph()
    assert graph is not None
    # LangGraph compiled graphs have an `invoke` method
    assert callable(getattr(graph, "invoke", None))
    assert callable(getattr(graph, "ainvoke", None))


# ---------------------------------------------------------------------------
# planner_node unit tests
# ---------------------------------------------------------------------------

def test_planner_node_single_scout_step():
    """Planner produces a 1-step Scout plan from a mocked LLM."""
    plan = SupervisorPlan(
        reasoning="Simple metric question → Scout only.",
        steps=[SupervisorStep(agent="scout", purpose="Get metric value", question="what is streaming_daily_users")],
    )
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = plan
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    with patch("clubos2.supervisor.graph.ChatOpenAI", return_value=mock_llm):
        result = planner_node(_base_state(user_query="what is streaming_daily_users"))

    assert result["plan"] == [step.model_dump() for step in plan.steps]
    assert result["step_index"] == 0
    assert len(result["plan"]) == 1
    assert result["plan"][0]["agent"] == "scout"


def test_planner_node_multi_step_plan():
    """Planner returns a 2-step plan when query is complex."""
    plan = SupervisorPlan(
        reasoning="Needs metric data then investigation.",
        steps=[
            SupervisorStep(agent="scout", purpose="Get current value", question="net_sales"),
            SupervisorStep(agent="investigator", purpose="Explain drop", alert_id="alrt_abc123", metric_name="net_sales"),
        ],
    )
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = plan
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    with patch("clubos2.supervisor.graph.ChatOpenAI", return_value=mock_llm):
        result = planner_node(_base_state(user_query="what is net_sales and why did it drop?"))

    assert len(result["plan"]) == 2
    assert result["plan"][0]["agent"] == "scout"
    assert result["plan"][1]["agent"] == "investigator"


def test_planner_node_llm_failure_returns_empty_plan():
    """If planner LLM raises, returns empty plan rather than crashing."""
    mock_structured = MagicMock()
    mock_structured.invoke.side_effect = RuntimeError("OpenAI down")
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    with patch("clubos2.supervisor.graph.ChatOpenAI", return_value=mock_llm):
        result = planner_node(_base_state())

    assert result["plan"] == []
    assert result["step_index"] == 0


# ---------------------------------------------------------------------------
# executor_node unit tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_executor_node_scout_step():
    """Executor runs Scout and records result."""
    answer = _mock_scout_answer()
    state = _base_state(
        user_query="what is streaming_daily_users",
        plan=[{"agent": "scout", "purpose": "get value", "question": "what is streaming_daily_users"}],
        step_index=0,
        step_results=[],
    )

    with patch("clubos2.supervisor.graph.executor_node.__wrapped__" if hasattr(executor_node, "__wrapped__") else "clubos2.agents.scout.run_scout", new=AsyncMock(return_value=answer)):
        # Patch run_scout inside executor_node's import namespace
        async def mock_run_scout(inp):
            return answer

        with patch("clubos2.agents.scout.run_scout", side_effect=mock_run_scout):
            result = await executor_node(state)

    assert result["step_index"] == 1
    assert len(result["step_results"]) == 1
    assert result["step_results"][0]["agent"] == "scout"


@pytest.mark.asyncio
async def test_executor_node_investigator_no_alert_id():
    """Executor records error when investigator step has no alert_id."""
    state = _base_state(
        plan=[{"agent": "investigator", "purpose": "investigate"}],
        step_index=0,
        step_results=[],
    )
    result = await executor_node(state)
    assert result["step_index"] == 1
    assert result["step_results"][0]["agent"] == "investigator"
    assert "no alert_id" in result["step_results"][0]["error"]
    assert result["step_results"][0]["output"] is None


@pytest.mark.asyncio
async def test_executor_node_step_failure_captured_not_raised():
    """If a step raises, error is captured in step_results and execution continues."""
    state = _base_state(
        plan=[{"agent": "scout", "purpose": "get value", "question": "x"}],
        step_index=0,
        step_results=[],
    )

    async def failing_scout(inp):
        raise RuntimeError("Scout API failure")

    with patch("clubos2.agents.scout.run_scout", side_effect=failing_scout):
        result = await executor_node(state)

    assert result["step_index"] == 1
    assert result["step_results"][0]["agent"] == "scout"
    assert "Scout API failure" in result["step_results"][0]["error"]


@pytest.mark.asyncio
async def test_executor_node_past_end_returns_finished():
    """Executor called when step_index >= len(plan) sets finished=True."""
    state = _base_state(plan=[], step_index=0, step_results=[])
    result = await executor_node(state)
    assert result.get("finished") is True


# ---------------------------------------------------------------------------
# synthesis_node unit tests
# ---------------------------------------------------------------------------

def test_synthesis_node_skipped_for_single_result():
    """Single step result → synthesis skipped, final_synthesis=None."""
    state = _base_state(
        step_results=[{"agent": "scout", "output": {"answer": "50k users"}}],
    )
    result = synthesis_node(state)
    assert result["finished"] is True
    assert result["final_synthesis"] is None


def test_synthesis_node_runs_for_multiple_results():
    """Two step results → synthesis LLM is called."""
    state = _base_state(
        user_query="what is net_sales and why did it drop?",
        step_results=[
            {"agent": "scout", "output": {"answer": "net_sales is 1M"}},
            {"agent": "investigator", "output": {"finding": {"cause_hypothesis": "promo ended"}}},
        ],
    )
    mock_response = MagicMock()
    mock_response.content = "Net sales is 1M. The investigation found the promo ended."
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_response

    with patch("clubos2.supervisor.graph.ChatOpenAI", return_value=mock_llm):
        result = synthesis_node(state)

    assert result["finished"] is True
    assert result["final_synthesis"] == mock_response.content


def test_synthesis_node_skipped_for_zero_results():
    """Zero step results (empty plan ran) → synthesis skipped gracefully."""
    state = _base_state(step_results=[])
    result = synthesis_node(state)
    assert result["finished"] is True
    assert result["final_synthesis"] is None


# ---------------------------------------------------------------------------
# Full graph integration (mocked agents + LLM)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_graph_single_scout_step_no_synthesis():
    """Full graph run: 1-step Scout plan → step_results has 1 entry, final_synthesis=None."""
    scout_answer = _mock_scout_answer()

    plan = SupervisorPlan(
        reasoning="Scout only.",
        steps=[SupervisorStep(agent="scout", purpose="get metric", question="test query")],
    )
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = plan
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    async def mock_run_scout(inp):
        return scout_answer

    with patch("clubos2.supervisor.graph.ChatOpenAI", return_value=mock_llm):
        with patch("clubos2.agents.scout.run_scout", side_effect=mock_run_scout):
            graph = build_supervisor_graph()
            final_state = await graph.ainvoke({
                "user_query": "test query",
                "messages": [],
                "plan": None,
                "step_index": 0,
                "step_results": [],
                "final_synthesis": None,
                "finished": False,
            })

    assert len(final_state["step_results"]) == 1
    assert final_state["step_results"][0]["agent"] == "scout"
    assert final_state["final_synthesis"] is None


@pytest.mark.asyncio
async def test_graph_multi_step_runs_synthesis():
    """Full graph: 2-step Scout+Scout plan → synthesis runs, final_synthesis set."""
    scout_answer = _mock_scout_answer()

    plan = SupervisorPlan(
        reasoning="Two scout steps for demonstration.",
        steps=[
            SupervisorStep(agent="scout", purpose="step 1", question="metric A"),
            SupervisorStep(agent="scout", purpose="step 2", question="metric B"),
        ],
    )
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = plan

    synthesis_response = MagicMock()
    synthesis_response.content = "Combined answer from both metrics."

    # LLM used for both planning (with_structured_output) and synthesis (invoke)
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    mock_llm.invoke.return_value = synthesis_response

    async def mock_run_scout(inp):
        return scout_answer

    with patch("clubos2.supervisor.graph.ChatOpenAI", return_value=mock_llm):
        with patch("clubos2.agents.scout.run_scout", side_effect=mock_run_scout):
            graph = build_supervisor_graph()
            final_state = await graph.ainvoke({
                "user_query": "compare metric A and metric B",
                "messages": [],
                "plan": None,
                "step_index": 0,
                "step_results": [],
                "final_synthesis": None,
                "finished": False,
            })

    assert len(final_state["step_results"]) == 2
    assert final_state["final_synthesis"] == synthesis_response.content


@pytest.mark.asyncio
async def test_graph_empty_plan_handles_gracefully():
    """LLM returns 0-step plan → graph reaches synthesis with empty results, no crash."""
    plan = SupervisorPlan(reasoning="Cannot determine appropriate steps.", steps=[])
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = plan
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    with patch("clubos2.supervisor.graph.ChatOpenAI", return_value=mock_llm):
        graph = build_supervisor_graph()
        final_state = await graph.ainvoke({
            "user_query": "something unclear",
            "messages": [],
            "plan": None,
            "step_index": 0,
            "step_results": [],
            "final_synthesis": None,
            "finished": False,
        })

    assert final_state["step_results"] == []
    assert final_state["final_synthesis"] is None
    assert final_state["finished"] is True


@pytest.mark.asyncio
async def test_graph_executor_failure_continues_to_next_step():
    """One step fails → error captured, next step runs, synthesis eventually called."""
    scout_answer = _mock_scout_answer()

    plan = SupervisorPlan(
        reasoning="Two steps.",
        steps=[
            SupervisorStep(agent="scout", purpose="failing step", question="bad"),
            SupervisorStep(agent="scout", purpose="good step", question="good"),
        ],
    )
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = plan

    synthesis_response = MagicMock()
    synthesis_response.content = "Partial result."
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    mock_llm.invoke.return_value = synthesis_response

    call_count = 0

    async def sometimes_failing_scout(inp):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("first call fails")
        return scout_answer

    with patch("clubos2.supervisor.graph.ChatOpenAI", return_value=mock_llm):
        with patch("clubos2.agents.scout.run_scout", side_effect=sometimes_failing_scout):
            graph = build_supervisor_graph()
            final_state = await graph.ainvoke({
                "user_query": "test",
                "messages": [],
                "plan": None,
                "step_index": 0,
                "step_results": [],
                "final_synthesis": None,
                "finished": False,
            })

    assert len(final_state["step_results"]) == 2
    assert "error" in final_state["step_results"][0]
    assert final_state["step_results"][1]["agent"] == "scout"
    assert final_state["step_results"][1]["output"] is not None
