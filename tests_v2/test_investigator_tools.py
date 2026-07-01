from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def test_investigator_tools_importable():
    from clubos2.investigator.tools import (
        INVESTIGATOR_TOOLS, query_metrics, search_knowledge,
        get_recent_alerts, get_metric_definition, get_peer_benchmark, web_search,
    )
    assert len(INVESTIGATOR_TOOLS) == 6


def test_all_tools_have_names():
    from clubos2.investigator.tools import INVESTIGATOR_TOOLS
    names = [t.name for t in INVESTIGATOR_TOOLS]
    assert "query_metrics" in names
    assert "search_knowledge" in names
    assert "get_recent_alerts" in names
    assert "get_metric_definition" in names
    assert "get_peer_benchmark" in names
    assert "web_search" in names


@pytest.mark.asyncio
async def test_get_metric_definition_returns_source_for_valid_metric():
    from clubos2.investigator.tools import get_metric_definition
    # Use a metric that exists in the semantic layer registry
    from clubos2.semantic_layer.lookup import _REGISTRY_CACHE
    if not _REGISTRY_CACHE:
        pytest.skip("No metrics in registry")
    first_metric = next(iter(_REGISTRY_CACHE.keys()))
    result = await get_metric_definition.ainvoke({"metric_name": first_metric})
    assert "source" in result
    assert result["source"] == "metric_registry"


@pytest.mark.asyncio
async def test_get_metric_definition_returns_error_for_unknown():
    from clubos2.investigator.tools import get_metric_definition
    result = await get_metric_definition.ainvoke({"metric_name": "nonexistent_metric_xyz"})
    assert "error" in result
    assert "source" in result


@pytest.mark.asyncio
async def test_get_peer_benchmark_error_for_unknown_metric():
    from clubos2.investigator.tools import get_peer_benchmark
    result = await get_peer_benchmark.ainvoke({"metric_name": "nonexistent_xyz"})
    assert "error" in result
    assert "source" in result


@pytest.mark.asyncio
async def test_get_recent_alerts_returns_list():
    from clubos2.investigator.tools import get_recent_alerts
    with patch("clubos2.watchdog.alerts_repo.AlertsRepository") as MockRepo:
        mock_repo_instance = MagicMock()
        mock_repo_instance.list_recent = AsyncMock(return_value=[])
        MockRepo.return_value = mock_repo_instance
        result = await get_recent_alerts.ainvoke({"metric_name": "streaming_daily_users", "days": 7})
    assert isinstance(result, list)


def test_get_tool_overview_returns_markdown():
    from clubos2.investigator.tool_descriptions import get_tool_overview
    overview = get_tool_overview()
    assert "# Investigator Tools" in overview
    assert "query_metrics" in overview
    assert "web_search" in overview
