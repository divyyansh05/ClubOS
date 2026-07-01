from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from clubos2.agents.scout import extract_terms, run_scout
from clubos2.agents.scout_schemas import Citation, Confidence, ScoutAnswer, ScoutInput
from clubos2.tools.registry import KnowledgeChunk, MetricRow


def test_extract_terms():
    """Verify terms extraction filters stopwords and returns bigrams."""
    terms = extract_terms("what is streaming daily users this month?")
    assert "streaming" in terms
    assert "daily" in terms
    assert "users" in terms
    assert "streaming daily" in terms
    assert "daily users" in terms
    assert "what" not in terms


@pytest.mark.asyncio
@patch("clubos2.agents.scout.detect_ambiguity")
@patch("clubos2.agents.scout.lookup_metrics_by_terms")
@patch("clubos2.agents.scout.query_metrics", new_callable=AsyncMock)
@patch("clubos2.agents.scout.search_knowledge", new_callable=AsyncMock)
@patch("clubos2.agents.scout.call_llm", new_callable=AsyncMock)
async def test_run_scout_happy_path(
    mock_call_llm,
    mock_search_knowledge,
    mock_query_metrics,
    mock_lookup_metrics,
    mock_detect_ambiguity,
):
    """Clean question should call tools and call LLM, returning ScoutAnswer."""
    # 1. Setup mock returns
    mock_detect_ambiguity.return_value = []

    # Mock a matched metric registry row
    mock_metric = AsyncMock()
    mock_metric.metric_name = "streaming_daily_users"
    mock_metric.business_name = "Streaming Daily Active Users"
    mock_metric.platform = "streaming"
    mock_metric.polarity = "positive"
    mock_metric.seasonal_note = "dips in Jan"
    mock_metric.definition = "daily streaming users"
    mock_lookup_metrics.return_value = [mock_metric]

    # Mock tool results
    mock_query_metrics.return_value = [
        MetricRow(
            metric_name="streaming_daily_users",
            business_name="Streaming Daily Active Users",
            value=85420.0,
            month="2025-11-01",
            polarity="higher_is_better",
            source="data/gold_snapshots/gold_kpi_health.csv",
        )
    ]
    mock_search_knowledge.return_value = [
        KnowledgeChunk(
            text="Narrative context about streaming users.",
            source="peer_benchmark.md",
            section="Streaming",
            score=0.9,
        )
    ]

    # Mock LLM return
    mock_call_llm.return_value = ScoutAnswer(
        answer="Streaming daily active users are 85,420 for November 2025.",
        citations=[
            Citation(
                claim="Streaming daily active users are 85,420",
                source="data/gold_snapshots/gold_kpi_health.csv",
                quote="streaming_daily_users 2025-11-01: 85,420",
            )
        ],
        confidence=Confidence.HIGH,
        assumptions_made=[],
    )

    # 2. Run
    ans = await run_scout(ScoutInput(question="what is streaming daily users this month?"))

    # 3. Verify
    assert ans.confidence == Confidence.HIGH
    assert len(ans.citations) == 1
    assert "streaming_daily_users" in ans.metrics_queried
    assert ans.chunks_retrieved == 1
    mock_call_llm.assert_called_once()
    mock_query_metrics.assert_called_once_with("streaming_daily_users")
    mock_search_knowledge.assert_called_once_with("what is streaming daily users this month?", k=5)


@pytest.mark.asyncio
@patch("clubos2.agents.scout.detect_ambiguity")
@patch("clubos2.agents.scout.lookup_metrics_by_terms")
@patch("clubos2.agents.scout.query_metrics", new_callable=AsyncMock)
@patch("clubos2.agents.scout.search_knowledge", new_callable=AsyncMock)
@patch("clubos2.agents.scout.call_llm", new_callable=AsyncMock)
async def test_run_scout_ambiguous_path(
    mock_call_llm,
    mock_search_knowledge,
    mock_query_metrics,
    mock_lookup_metrics,
    mock_detect_ambiguity,
):
    """Ambiguous question should note assumption in assumptions_made."""
    # 1. Setup mock returns
    mock_lookup_metrics.return_value = []
    mock_query_metrics.return_value = []
    mock_search_knowledge.return_value = []

    # Mock ambiguity warning
    from clubos2.semantic_layer.lookup import AmbiguityWarning

    mock_detect_ambiguity.return_value = [
        AmbiguityWarning(
            detected_term="conversion rate",
            candidate_metrics=["conversion_rate_ecommerce", "conversion_rate_streaming"],
            default="conversion_rate_ecommerce",
            rule_text="default to ecommerce",
        )
    ]

    mock_call_llm.return_value = ScoutAnswer(
        answer="I default to ecommerce conversion rate as per rule.",
        citations=[],
        confidence=Confidence.MEDIUM,
        assumptions_made=["defaulted to conversion_rate_ecommerce"],
    )

    # 2. Run
    ans = await run_scout(ScoutInput(question="how is conversion rate?"))

    # 3. Verify
    assert ans.confidence == Confidence.MEDIUM
    assert "defaulted to conversion_rate_ecommerce" in ans.assumptions_made


@pytest.mark.asyncio
@patch("clubos2.agents.scout.detect_ambiguity")
@patch("clubos2.agents.scout.lookup_metrics_by_terms")
@patch("clubos2.agents.scout.query_metrics", new_callable=AsyncMock)
@patch("clubos2.agents.scout.search_knowledge", new_callable=AsyncMock)
@patch("clubos2.agents.scout.call_llm", new_callable=AsyncMock)
async def test_run_scout_unanswerable_path(
    mock_call_llm,
    mock_search_knowledge,
    mock_query_metrics,
    mock_lookup_metrics,
    mock_detect_ambiguity,
):
    """Unanswerable question should return LOW confidence and empty citations."""
    # 1. Setup mock returns
    mock_detect_ambiguity.return_value = []
    mock_lookup_metrics.return_value = []
    mock_query_metrics.return_value = []
    mock_search_knowledge.return_value = []

    mock_call_llm.return_value = ScoutAnswer(
        answer="I don't have data in my current context that answers this question.",
        citations=[],
        confidence=Confidence.LOW,
        assumptions_made=[],
    )

    # 2. Run
    ans = await run_scout(ScoutInput(question="what is the player roster?"))

    # 3. Verify
    assert ans.confidence == Confidence.LOW
    assert len(ans.citations) == 0
