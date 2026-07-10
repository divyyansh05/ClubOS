from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from clubos2.supervisor.classifier import (
    AgentType,
    ClassificationResult,
    _load_known_metric_names,
    classify_query,
)

# ---------------------------------------------------------------------------
# Patch metric registry for tests that don't need real DB
# ---------------------------------------------------------------------------

FAKE_METRICS = ["streaming_daily_users", "net_sales", "conversion_rate", "ticket_revenue"]


@pytest.fixture(autouse=True)
def patch_metrics(monkeypatch):
    """Avoid hitting the real DuckDB file in unit tests."""
    # lru_cache means we need to clear it between tests if we patch
    _load_known_metric_names.cache_clear()
    with patch(
        "clubos2.supervisor.classifier._load_known_metric_names",
        return_value=FAKE_METRICS,
    ):
        yield
    _load_known_metric_names.cache_clear()


# ---------------------------------------------------------------------------
# The 7 required test cases from the prompt spec
# ---------------------------------------------------------------------------

def test_monthly_summary_routes_to_briefer():
    result = classify_query("give me a monthly summary")
    assert result.agent == AgentType.BRIEFER
    assert result.confidence == "high"


def test_why_drop_routes_to_investigator_medium():
    result = classify_query("why did streaming_daily_users drop last week")
    # Investigation patterns fire before metric lookup, so it's Investigator
    assert result.agent == AgentType.INVESTIGATOR
    assert result.confidence == "medium"
    assert result.extracted_params.get("alert_id") is None


def test_alert_id_routes_to_investigator_high_with_extraction():
    result = classify_query("why did alert alrt_abc123ff fire")
    assert result.agent == AgentType.INVESTIGATOR
    assert result.confidence == "high"
    assert result.extracted_params.get("alert_id") == "alrt_abc123ff"


def test_known_metric_question_routes_to_scout_high():
    result = classify_query("what is streaming_daily_users this month")
    assert result.agent == AgentType.SCOUT
    assert result.confidence == "high"
    assert result.extracted_params.get("referenced_metric") == "streaming_daily_users"


def test_conversion_rate_space_form_routes_to_scout():
    """'conversion rate' (space) should match 'conversion_rate' (underscore) metric."""
    result = classify_query("how is our conversion rate looking")
    assert result.agent == AgentType.SCOUT


def test_vague_query_returns_unknown():
    result = classify_query("help me understand our business")
    assert result.agent == AgentType.UNKNOWN
    assert result.confidence == "low"


def test_complex_multi_step_returns_unknown():
    result = classify_query("compare last quarter to this quarter and tell me what changed and why")
    assert result.agent == AgentType.UNKNOWN


# ---------------------------------------------------------------------------
# Additional coverage
# ---------------------------------------------------------------------------

def test_brief_me_routes_to_briefer():
    result = classify_query("brief me on last month's performance")
    assert result.agent == AgentType.BRIEFER
    assert result.confidence == "high"


def test_monthly_briefing_keyword():
    result = classify_query("run the monthly briefing")
    assert result.agent == AgentType.BRIEFER


def test_root_cause_routes_to_investigator():
    result = classify_query("what is the root cause of the net_sales decline")
    # root_cause_keyword fires before metric lookup
    assert result.agent == AgentType.INVESTIGATOR


def test_alert_id_extraction_underscore_hex():
    result = classify_query("investigate alrt_deadbeef99")
    assert result.agent == AgentType.INVESTIGATOR
    assert result.extracted_params.get("alert_id") == "alrt_deadbeef99"


def test_what_is_routes_to_scout_shape():
    """Question shape fires when no metric name present."""
    result = classify_query("what is our revenue right now")
    assert result.agent == AgentType.SCOUT
    assert result.confidence == "medium"
    assert result.rule_matched == "value_question_shape"


def test_current_value_shape():
    result = classify_query("show me the latest numbers")
    assert result.agent == AgentType.SCOUT
    assert result.confidence == "medium"


def test_metric_underscore_and_space_both_match():
    """Both 'net_sales' and 'net sales' should resolve to Scout/high."""
    r1 = classify_query("what is net_sales today")
    r2 = classify_query("what is net sales today")
    assert r1.agent == AgentType.SCOUT
    assert r1.confidence == "high"
    assert r2.agent == AgentType.SCOUT
    assert r2.confidence == "high"


def test_result_is_classification_result_instance():
    result = classify_query("anything")
    assert isinstance(result, ClassificationResult)


# ---------------------------------------------------------------------------
# Performance — must return in <10ms averaged over 100 calls
# ---------------------------------------------------------------------------

def test_classify_latency_under_10ms_average():
    queries = [
        "what is streaming_daily_users",
        "give me a monthly summary",
        "why did alert alrt_abc123 fire",
        "help me understand our business",
        "compare last quarter to this quarter",
    ] * 20  # 100 total

    start = time.perf_counter()
    for q in queries:
        classify_query(q)
    elapsed_ms = (time.perf_counter() - start) * 1000
    avg_ms = elapsed_ms / len(queries)

    assert avg_ms < 10, f"Average classify_query latency {avg_ms:.2f}ms exceeds 10ms threshold"
