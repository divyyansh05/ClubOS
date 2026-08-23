from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from clubos2.tools import TOOL_REGISTRY, get_benchmark, get_signal, query_metrics, search_knowledge


@pytest.mark.asyncio
async def test_query_metrics_stub():
    """Verify query_metrics returns non-empty list of MetricRow with source populated."""
    rows = await query_metrics("streaming_daily_users")
    assert len(rows) > 0
    for row in rows:
        assert row.metric_name == "streaming_daily_users"
        assert row.source != ""
        assert row.value > 0.0


@pytest.mark.asyncio
async def test_search_knowledge_stub():
    """Verify search_knowledge returns non-empty list of KnowledgeChunk with source populated."""
    from clubos2.tools.registry import KnowledgeChunk

    fake_chunks = [
        KnowledgeChunk(text="Mocked text", source="mock.md", section="Mock Section", score=0.9)
    ]
    with patch("clubos2.rag.retriever.retrieve", return_value=fake_chunks) as mock_retrieve:
        chunks = await search_knowledge("seasonal z-score", k=2)
        mock_retrieve.assert_called_once()
    assert len(chunks) > 0
    assert len(chunks) <= 2
    for chunk in chunks:
        assert chunk.source != ""
        assert chunk.text != ""


@pytest.mark.asyncio
async def test_get_signal_stub():
    """Verify get_signal returns a valid signal dictionary with source populated."""
    sig = await get_signal("sig_001")
    assert isinstance(sig, dict)
    assert sig["signal_id"] == "sig_001"
    assert sig["source"] != ""


@pytest.mark.asyncio
async def test_get_benchmark_stub():
    """Verify get_benchmark returns a valid benchmark dictionary with source populated."""
    bench = await get_benchmark("streaming_daily_users")
    assert isinstance(bench, dict)
    assert bench["metric_name"] == "streaming_daily_users"
    assert bench["source"] != ""


def test_tool_registry():
    """Verify the registry maps names to the actual tool functions."""
    assert TOOL_REGISTRY["query_metrics"] == query_metrics
    assert TOOL_REGISTRY["search_knowledge"] == search_knowledge
    assert TOOL_REGISTRY["get_signal"] == get_signal
    assert TOOL_REGISTRY["get_benchmark"] == get_benchmark


def test_traced_decorators_applied():
    """Verify that every tool function is decorated with @traced(..., run_type='tool')."""
    # We patch the traced decorator and reload the registry module to verify it was applied
    mock_traced = MagicMock(side_effect=lambda name, run_type: lambda f: f)

    # Evict tools modules from cache so it re-imports and invokes decorators
    sys.modules.pop("clubos2.tools.registry", None)
    sys.modules.pop("clubos2.tools", None)

    with patch("clubos2.observability.tracing.traced", mock_traced):
        import clubos2.tools.registry as registry  # noqa: F401

    # Check if ruff/mypy-safe wrapper decorations were checked using keyword arguments
    mock_traced.assert_any_call(name="tool:query_metrics", run_type="tool")
    mock_traced.assert_any_call(name="tool:search_knowledge", run_type="tool")
    mock_traced.assert_any_call(name="tool:get_signal", run_type="tool")
    mock_traced.assert_any_call(name="tool:get_benchmark", run_type="tool")
