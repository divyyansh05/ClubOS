from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from clubos2.eval.supervisor_scorer import check_supervisor_fact, SupervisorScenarioResult
from clubos2.eval.briefer_scorer import check_briefer_fact, BrieferScenarioResult


# ---------------------------------------------------------------------------
# check_supervisor_fact — unit tests
# ---------------------------------------------------------------------------

def _sup_result(**overrides) -> dict:
    base = {
        "query": "test",
        "dispatch_path": "direct_scout",
        "classification": {
            "agent": "scout",
            "confidence": "high",
            "rule_matched": "known_metric_referenced",
            "reasoning": "...",
            "extracted_params": {"raw_query": "test"},
        },
        "result": {"answer": "50k"},
        "latency_seconds": 0.5,
        "trace_url": None,
        "error": None,
    }
    base.update(overrides)
    return base


def test_sup_fact_dispatch_path_match():
    assert check_supervisor_fact("dispatch_path=direct_scout", _sup_result()) is True


def test_sup_fact_dispatch_path_no_match():
    assert check_supervisor_fact("dispatch_path=direct_briefer", _sup_result()) is False


def test_sup_fact_dispatch_path_in_set_match():
    assert check_supervisor_fact(
        "dispatch_path in [direct_scout, langgraph_supervisor]",
        _sup_result(dispatch_path="langgraph_supervisor"),
    ) is True


def test_sup_fact_dispatch_path_in_set_no_match():
    assert check_supervisor_fact(
        "dispatch_path in [direct_briefer, direct_investigator]",
        _sup_result(dispatch_path="direct_scout"),
    ) is False


def test_sup_fact_classification_agent():
    assert check_supervisor_fact("classification.agent=scout", _sup_result()) is True
    assert check_supervisor_fact("classification.agent=briefer", _sup_result()) is False


def test_sup_fact_classification_agent_in_set():
    r = _sup_result()
    r["classification"]["agent"] = "unknown"
    assert check_supervisor_fact("classification.agent in [scout, unknown]", r) is True
    assert check_supervisor_fact("classification.agent in [briefer, investigator]", r) is False


def test_sup_fact_classification_confidence():
    assert check_supervisor_fact("classification.confidence=high", _sup_result()) is True
    assert check_supervisor_fact("classification.confidence=low", _sup_result()) is False


def test_sup_fact_extracted_params_alert_id():
    r = _sup_result()
    r["classification"]["extracted_params"] = {"alert_id": "alrt_abc123", "raw_query": "x"}
    assert check_supervisor_fact(
        "classification.extracted_params contains alert_id=alrt_abc123", r
    ) is True
    assert check_supervisor_fact(
        "classification.extracted_params contains alert_id=alrt_wrong", r
    ) is False


def test_sup_fact_plan_steps_gte():
    r = _sup_result(dispatch_path="langgraph_supervisor")
    r["result"] = {"plan": [{"agent": "scout"}, {"agent": "investigator"}], "step_results": []}
    assert check_supervisor_fact("plan.steps>=1", r) is True
    assert check_supervisor_fact("plan.steps>=2", r) is True
    assert check_supervisor_fact("plan.steps>=3", r) is False


def test_sup_fact_error_is_null():
    assert check_supervisor_fact("error is null", _sup_result()) is True
    assert check_supervisor_fact("error is null", _sup_result(error="boom")) is False


# ---------------------------------------------------------------------------
# check_briefer_fact — unit tests
# ---------------------------------------------------------------------------

def _brf_result(**overrides) -> dict:
    base = {
        "briefing_id": "brf_abc123",
        "briefing_type": "monthly_scheduled",
        "scope_key": "monthly:2026-06",
        "status": "completed",
        "was_cached": False,
        "content": {
            "executive_summary": "A solid month with no major incidents.",
            "body_markdown": "# Monthly Briefing\n\nInvestigations concluded with high confidence.",
            "citations": [{"claim": "x", "source": "investigations", "section": None, "quote": None}],
            "investigations_referenced": ["inv_001", "inv_002", "inv_003"],
            "alerts_referenced": ["alrt_001"],
            "metrics_covered": ["streaming_daily_users", "net_sales"],
        },
        "latency_seconds": 2.0,
        "total_tokens": None,
        "cost_usd": None,
        "trace_url": None,
        "error": None,
    }
    base.update(overrides)
    return base


def test_brf_fact_status_completed():
    assert check_briefer_fact("status=completed", _brf_result()) is True
    assert check_briefer_fact("status=failed", _brf_result()) is False


def test_brf_fact_was_cached_false():
    assert check_briefer_fact("was_cached=false", _brf_result(was_cached=False)) is True
    assert check_briefer_fact("was_cached=false", _brf_result(was_cached=True)) is False


def test_brf_fact_was_cached_true():
    assert check_briefer_fact("was_cached=true", _brf_result(was_cached=True)) is True


def test_brf_fact_executive_summary_non_empty():
    assert check_briefer_fact("executive_summary is non-empty", _brf_result()) is True
    r = _brf_result()
    r["content"]["executive_summary"] = ""
    assert check_briefer_fact("executive_summary is non-empty", r) is False


def test_brf_fact_investigations_referenced_length():
    assert check_briefer_fact("investigations_referenced list length >= 3", _brf_result()) is True
    assert check_briefer_fact("investigations_referenced list length >= 4", _brf_result()) is False


def test_brf_fact_investigations_referenced_empty():
    r = _brf_result()
    r["content"]["investigations_referenced"] = []
    assert check_briefer_fact("investigations_referenced list is empty", r) is True
    assert check_briefer_fact("investigations_referenced list is empty", _brf_result()) is False


def test_brf_fact_alerts_referenced_non_empty():
    assert check_briefer_fact("alerts_referenced list non-empty", _brf_result()) is True
    r = _brf_result()
    r["content"]["alerts_referenced"] = []
    assert check_briefer_fact("alerts_referenced list non-empty", r) is False


def test_brf_fact_citations_non_empty():
    assert check_briefer_fact("citations list non-empty", _brf_result()) is True


def test_brf_fact_scope_key_exact():
    assert check_briefer_fact("scope_key=monthly:2026-06", _brf_result()) is True
    assert check_briefer_fact("scope_key=monthly:2026-07", _brf_result()) is False


def test_brf_fact_scope_key_starts_with():
    r = _brf_result()
    r["scope_key"] = "incident:alrt_abc"
    assert check_briefer_fact("scope_key starts with incident:", r) is True
    assert check_briefer_fact("scope_key starts with monthly:", r) is False


def test_brf_fact_metrics_covered():
    assert check_briefer_fact("metrics_covered contains streaming_daily_users", _brf_result()) is True
    assert check_briefer_fact("metrics_covered contains matchday_ticket_revenue", _brf_result()) is False


def test_brf_fact_error_is_null():
    assert check_briefer_fact("error is null", _brf_result()) is True
    assert check_briefer_fact("error is null", _brf_result(error="LLM failed")) is False


def test_brf_fact_briefing_id_matches_prior():
    ctx = {"prior_briefing_id": "brf_abc123"}
    assert check_briefer_fact("briefing_id matches first call", _brf_result(), ctx) is True
    assert check_briefer_fact("briefing_id matches first call", _brf_result(briefing_id="brf_xyz"), ctx) is False


def test_brf_fact_briefing_id_does_not_match():
    ctx = {"prior_briefing_id": "brf_old"}
    assert check_briefer_fact("briefing_id does not match prior cached briefing_id", _brf_result(), ctx) is True
    r = _brf_result(briefing_id="brf_old")
    assert check_briefer_fact("briefing_id does not match prior cached briefing_id", r, ctx) is False


def test_brf_fact_source_citation():
    assert check_briefer_fact("source citation points to investigations", _brf_result()) is True
    r = _brf_result()
    r["content"]["citations"] = [{"claim": "x", "source": "watchdog_alerts", "section": None, "quote": None}]
    assert check_briefer_fact("source citation points to investigations", r) is False


def test_brf_fact_persistent_metric_in_body():
    r = _brf_result()
    r["content"]["body_markdown"] = "# Briefing\n\nnet_sales is a persistent concern (3+ investigations)."
    assert check_briefer_fact("persistent metric mentioned in body_markdown", r) is True
    r["content"]["body_markdown"] = "# Briefing\n\nNothing notable."
    assert check_briefer_fact("persistent metric mentioned in body_markdown", r) is False


# ---------------------------------------------------------------------------
# run_supervisor_scenario — integration-style (mocked handle_query)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_supervisor_scenario_passes_on_correct_routing():
    from clubos2.eval.supervisor_scorer import run_supervisor_scenario
    from eval.golden.schema import GoldenEntry, QuestionType, ExpectedConfidence

    entry = GoldenEntry(
        id="gq_041",
        question="What is streaming_daily_users this month?",
        question_type=QuestionType.SUPERVISOR_ROUTING,
        expected_answer_facts=[
            "dispatch_path=direct_scout",
            "classification.agent=scout",
            "classification.confidence=high",
        ],
        expected_metric_names=["streaming_daily_users"],
        required_citation_sources=[],
        expected_confidence=ExpectedConfidence.HIGH,
        author="test",
        created_at="2026-07-09",
    )

    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "query": entry.question,
        "dispatch_path": "direct_scout",
        "classification": {"agent": "scout", "confidence": "high", "rule_matched": "known_metric_referenced", "reasoning": "x", "extracted_params": {}},
        "result": {},
        "latency_seconds": 0.1,
        "trace_url": None,
        "error": None,
    }

    with patch("clubos2.supervisor.entry_point.handle_query", new=AsyncMock(return_value=mock_response)):
        result = await run_supervisor_scenario(entry)

    assert result.overall_pass is True
    assert len(result.facts_failed) == 0
    assert len(result.facts_satisfied) == 3


@pytest.mark.asyncio
async def test_run_supervisor_scenario_fails_on_wrong_dispatch():
    from clubos2.eval.supervisor_scorer import run_supervisor_scenario
    from eval.golden.schema import GoldenEntry, QuestionType, ExpectedConfidence

    entry = GoldenEntry(
        id="gq_042",
        question="Give me a monthly summary of March 2026.",
        question_type=QuestionType.SUPERVISOR_ROUTING,
        expected_answer_facts=["dispatch_path=direct_briefer"],
        expected_metric_names=[],
        required_citation_sources=[],
        expected_confidence=ExpectedConfidence.HIGH,
        author="test",
        created_at="2026-07-09",
    )

    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "query": entry.question,
        "dispatch_path": "direct_scout",  # wrong
        "classification": {"agent": "scout", "confidence": "medium", "rule_matched": None, "reasoning": "x", "extracted_params": {}},
        "result": {},
        "latency_seconds": 0.1,
        "trace_url": None,
        "error": None,
    }

    with patch("clubos2.supervisor.entry_point.handle_query", new=AsyncMock(return_value=mock_response)):
        result = await run_supervisor_scenario(entry)

    assert result.overall_pass is False
    assert "dispatch_path=direct_briefer" in result.facts_failed


# ---------------------------------------------------------------------------
# run_briefer_scenario — integration-style (mocked run_briefing)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_briefer_scenario_passes_on_correct_output():
    from clubos2.eval.briefer_scorer import run_briefer_scenario
    from eval.golden.schema import GoldenEntry, QuestionType, ExpectedConfidence
    from clubos2.briefer.agent_schemas import BriefingRunResult, BriefingType, BriefingContent
    from clubos2.agents.scout_schemas import Citation

    entry = GoldenEntry(
        id="gq_052",
        question="Generate a monthly briefing for a period with zero investigations.",
        question_type=QuestionType.BRIEFER_RUN,
        expected_answer_facts=["status=completed", "was_cached=false", "executive_summary is non-empty", "investigations_referenced list is empty"],
        expected_metric_names=[],
        required_citation_sources=[],
        expected_confidence=ExpectedConfidence.HIGH,
        author="test",
        created_at="2026-07-09",
        scenario_setup="Empty investigations table.",
    )

    fake_result = BriefingRunResult(
        briefing_id="brf_test052",
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key="monthly:2099-02",
        status="completed",
        was_cached=False,
        content=BriefingContent(
            executive_summary="No critical investigations were triggered this month.",
            body_markdown="# Briefing\n\nNo investigations concluded.",
            citations=[],
            investigations_referenced=[],
            alerts_referenced=[],
            metrics_covered=[],
        ),
        latency_seconds=1.0,
    )

    with patch("clubos2.briefer.orchestrator.run_briefing", new=AsyncMock(return_value=fake_result)):
        result = await run_briefer_scenario(entry)

    assert result.overall_pass is True
    assert len(result.facts_failed) == 0


@pytest.mark.asyncio
async def test_run_briefer_scenario_cache_hit():
    from clubos2.eval.briefer_scorer import run_briefer_scenario
    from eval.golden.schema import GoldenEntry, QuestionType, ExpectedConfidence
    from clubos2.briefer.agent_schemas import BriefingRunResult, BriefingType

    entry = GoldenEntry(
        id="gq_054",
        question="Request the same monthly briefing scope twice within freshness window.",
        question_type=QuestionType.BRIEFER_RUN,
        expected_answer_facts=["was_cached=true", "status=cached", "briefing_id matches first call"],
        expected_metric_names=[],
        required_citation_sources=[],
        expected_confidence=ExpectedConfidence.HIGH,
        author="test",
        created_at="2026-07-09",
        scenario_setup="Pre-populate a completed briefing.",
    )

    # The setup function seeds a real briefing row — we mock run_briefing to return a cached result
    # matching that row's ID. We need to capture what the setup does.
    seeded_id = "brf_seeded_054"

    async def mock_setup():
        from clubos2.briefer.agent_schemas import BriefingInput, BriefingType as BT
        inp = BriefingInput(
            briefing_type=BT.MONTHLY_SCHEDULED,
            scope_key="monthly:2099-03",
            period_start=datetime(2099, 3, 1),
            period_end=datetime(2099, 3, 31, 23, 59, 59),
            triggered_by="eval",
            freshness_days=7,
        )
        return inp, {"prior_briefing_id": seeded_id}

    cached_result = BriefingRunResult(
        briefing_id=seeded_id,
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key="monthly:2099-03",
        status="cached",
        was_cached=True,
        content=None,
        latency_seconds=0.01,
    )

    with patch("clubos2.eval.briefer_scorer.BRIEFER_SCENARIOS", {"gq_054": mock_setup}):
        with patch("clubos2.briefer.orchestrator.run_briefing", new=AsyncMock(return_value=cached_result)):
            result = await run_briefer_scenario(entry)

    assert result.overall_pass is True
    assert "was_cached=true" in result.facts_satisfied
    assert "briefing_id matches first call" in result.facts_satisfied
