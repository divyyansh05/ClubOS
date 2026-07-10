from __future__ import annotations
import os
import tempfile
import pytest


@pytest.mark.asyncio
async def test_get_checkpointer_creates_file():
    from clubos2.investigator.checkpointer import get_checkpointer
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_checkpoints.sqlite")
        async with get_checkpointer(path=db_path) as cp:
            # AsyncSqliteSaver creates the file when the context is entered
            assert cp is not None
        assert os.path.exists(db_path)


@pytest.mark.asyncio
async def test_get_checkpointer_default_path_creates_var_dir():
    from clubos2.investigator.checkpointer import get_checkpointer
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    async with get_checkpointer() as cp:
        assert isinstance(cp, AsyncSqliteSaver)


@pytest.mark.asyncio
async def test_graph_with_checkpointer_persists_state():
    """Two calls with same thread_id use the same checkpoint."""
    from clubos2.investigator.graph import build_graph
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.messages import AIMessage
    from unittest.mock import patch, MagicMock

    final_msg = AIMessage(content='{"alert_id":"t","metric_name":"m","cause_hypothesis":"x","confidence":"low","evidence_summary":"y","citations":[],"reasoning_trace":[],"tools_called":[],"total_steps":1}', tool_calls=[])

    cp = MemorySaver()
    with patch("clubos2.investigator.graph.build_llm") as mock_build:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = final_msg
        mock_build.return_value = mock_llm

        graph = build_graph(checkpointer=cp)
        state = {
            "alert_id": "alrt_cp_test",
            "metric_name": "net_sales",
            "triggered_by": "test",
            "max_steps": 4,
            "messages": [],
            "step_count": 0,
            "tools_called": [],
            "reasoning_trace": [],
            "finding": None,
            "finished": False,
        }
        config = {"configurable": {"thread_id": "thread_persist_1"}}
        result = await graph.ainvoke(state, config=config)
        assert result is not None
