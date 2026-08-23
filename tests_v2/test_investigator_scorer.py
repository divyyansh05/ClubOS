from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


def test_check_fact_is_seasonal_true():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result = {
        "status": "completed",
        "finding": {"is_seasonal_or_expected": True, "tools_called": [], "citations": [], "total_steps": 1},
    }
    assert check_investigation_fact("is_seasonal_or_expected=true", result) is True
    assert check_investigation_fact("is_seasonal_or_expected=false", result) is False


def test_check_fact_confidence_in():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result = {"status": "completed", "finding": {"confidence": "medium", "tools_called": [], "citations": []}}
    assert check_investigation_fact("confidence in [high, medium]", result) is True
    assert check_investigation_fact("confidence in [high]", result) is False


def test_check_fact_uses_tool():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result = {"status": "completed", "finding": {"tools_called": ["get_metric_definition", "web_search"], "citations": []}}
    assert check_investigation_fact("uses get_metric_definition tool", result) is True
    assert check_investigation_fact("uses get_peer_benchmark tool", result) is False


def test_check_fact_cites_source():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result = {
        "status": "completed",
        "finding": {
            "citations": [{"source": "metric_registry", "claim": "x", "section": "", "quote": ""}],
            "tools_called": [],
        },
    }
    assert check_investigation_fact("cites metric_registry", result) is True
    assert check_investigation_fact("cites watchdog_alerts", result) is False


def test_check_fact_total_steps():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result = {"status": "completed", "finding": {"total_steps": 4, "tools_called": [], "citations": []}}
    assert check_investigation_fact("total_steps >= 3", result) is True
    assert check_investigation_fact("total_steps >= 5", result) is False


def test_check_fact_investigation_completes():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    assert check_investigation_fact("investigation completes", {"status": "completed", "finding": {}}) is True
    assert check_investigation_fact("investigation completes", {"status": "failed", "finding": {}}) is False


def test_check_fact_investigation_completes_normally():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    assert check_investigation_fact("investigation completes normally", {"status": "completed", "finding": {}}) is True
    assert check_investigation_fact("investigation completes normally", {"status": "failed", "finding": {}}) is False


def test_check_fact_cause_hypothesis_non_empty():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result_with = {"status": "completed", "finding": {"cause_hypothesis": "Some hypothesis"}}
    result_without = {"status": "completed", "finding": {"cause_hypothesis": ""}}
    assert check_investigation_fact("cause_hypothesis is non-empty", result_with) is True
    assert check_investigation_fact("cause_hypothesis is non-empty", result_without) is False


def test_check_fact_evidence_summary_non_empty():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result_with = {"status": "completed", "finding": {"evidence_summary": "- Some evidence"}}
    result_without = {"status": "completed", "finding": {"evidence_summary": ""}}
    assert check_investigation_fact("evidence_summary is non-empty", result_with) is True
    assert check_investigation_fact("evidence_summary is non-empty", result_without) is False


def test_check_fact_citations_non_empty():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result_with = {"status": "completed", "finding": {"citations": [{"source": "x", "claim": "y"}]}}
    result_without = {"status": "completed", "finding": {"citations": []}}
    assert check_investigation_fact("citations list non-empty", result_with) is True
    assert check_investigation_fact("citations list non-empty", result_without) is False


def test_check_fact_data_gaps_non_empty():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result_with = {"status": "completed", "finding": {"data_gaps": ["gap1"]}}
    result_without = {"status": "completed", "finding": {"data_gaps": []}}
    assert check_investigation_fact("data_gaps list non-empty", result_with) is True
    assert check_investigation_fact("data_gaps list non-empty", result_without) is False


def test_check_fact_cause_hypothesis_references():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result = {"status": "completed", "finding": {"cause_hypothesis": "This is about metric definition patterns"}}
    assert check_investigation_fact("cause_hypothesis references metric definition", result) is True
    assert check_investigation_fact("cause_hypothesis references seasonal", result) is False


def test_check_fact_no_fabricated_numbers():
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result_good = {"status": "completed", "finding": {"cause_hypothesis": "Some hypothesis"}}
    result_bad = {"status": "failed", "finding": {}}
    assert check_investigation_fact("no fabricated numbers", result_good) is True
    assert check_investigation_fact("no fabricated numbers", result_bad) is False


def test_check_fact_unparseable_returns_true():
    """Unparseable facts should pass by default."""
    from clubos2.eval.investigator_scorer import check_investigation_fact
    result = {"status": "completed", "finding": {}}
    # This pattern won't match any known pattern
    assert check_investigation_fact("some completely unknown fact xyz", result) is True


def test_all_setup_functions_registered():
    from clubos2.eval.investigator_scorer import INVESTIGATION_SCENARIOS
    expected = [f"gq_0{i:02d}" for i in range(31, 41)]
    for gq_id in expected:
        assert gq_id in INVESTIGATION_SCENARIOS, f"Missing setup for {gq_id}"


@pytest.mark.asyncio
async def test_scenario_with_no_setup_function_returns_not_recreated():
    from clubos2.eval.investigator_scorer import run_investigation_scenario
    from eval.golden.schema import GoldenEntry, QuestionType, ExpectedConfidence
    entry = GoldenEntry(
        id="gq_999_fake",
        question="fake question?",
        question_type=QuestionType.INVESTIGATION,
        expected_answer_facts=["investigation completes"],
        expected_metric_names=[],
        required_citation_sources=[],
        expected_confidence=ExpectedConfidence.MEDIUM,
        author="test",
        created_at="2026-07-01",
    )
    result = await run_investigation_scenario(entry)
    assert result.scenario_recreated is False
    assert result.overall_pass is False


@pytest.mark.asyncio
async def test_scenario_happy_path_with_mocked_orchestrator():
    from clubos2.eval.investigator_scorer import run_investigation_scenario
    from eval.golden.schema import GoldenEntry, QuestionType, ExpectedConfidence

    entry = GoldenEntry(
        id="gq_031",
        question="Investigate the alert on net_sales?",
        question_type=QuestionType.INVESTIGATION,
        expected_answer_facts=[
            "is_seasonal_or_expected=true",
            "confidence in [high, medium]",
        ],
        expected_metric_names=["net_sales"],
        required_citation_sources=[],
        expected_confidence=ExpectedConfidence.HIGH,
        author="test",
        created_at="2026-07-01",
    )

    mock_result = MagicMock()
    mock_result.status = "completed"
    mock_result.model_dump.return_value = {
        "status": "completed",
        "finding": {
            "is_seasonal_or_expected": True,
            "confidence": "high",
            "tools_called": ["get_metric_definition"],
            "citations": [],
            "total_steps": 2,
            "cause_hypothesis": "Seasonal pattern.",
            "evidence_summary": "- Evidence",
            "data_gaps": [],
        },
    }

    import clubos2.eval.investigator_scorer as scorer_mod
    original = scorer_mod.INVESTIGATION_SCENARIOS["gq_031"]
    scorer_mod.INVESTIGATION_SCENARIOS["gq_031"] = AsyncMock(return_value="alrt_eval_abc")

    # Patch the orchestrator module so the lazy import inside run_investigation_scenario resolves
    mock_orchestrator = MagicMock()
    mock_orchestrator.run_investigation = AsyncMock(return_value=mock_result)

    mock_input_cls = MagicMock(return_value=MagicMock())

    try:
        with patch.dict(
            "sys.modules",
            {
                "clubos2.investigator.orchestrator": mock_orchestrator,
                "clubos2.investigator.agent_schemas": MagicMock(InvestigatorInput=mock_input_cls),
            },
        ):
            result = await run_investigation_scenario(entry)
    finally:
        scorer_mod.INVESTIGATION_SCENARIOS["gq_031"] = original

    # The scenario should be recreated (setup ran) and facts checked
    assert result.scenario_recreated is True


@pytest.mark.asyncio
async def test_scenario_setup_failure_returns_not_recreated():
    """When setup function raises, scenario_recreated should be False."""
    from clubos2.eval.investigator_scorer import run_investigation_scenario
    from eval.golden.schema import GoldenEntry, QuestionType, ExpectedConfidence

    entry = GoldenEntry(
        id="gq_032",
        question="Investigate the alert on streaming_daily_users?",
        question_type=QuestionType.INVESTIGATION,
        expected_answer_facts=["investigation completes"],
        expected_metric_names=["streaming_daily_users"],
        required_citation_sources=[],
        expected_confidence=ExpectedConfidence.MEDIUM,
        author="test",
        created_at="2026-07-01",
    )

    import clubos2.eval.investigator_scorer as scorer_mod
    original = scorer_mod.INVESTIGATION_SCENARIOS["gq_032"]
    failing_setup = AsyncMock(side_effect=RuntimeError("DB unavailable"))
    scorer_mod.INVESTIGATION_SCENARIOS["gq_032"] = failing_setup

    try:
        result = await run_investigation_scenario(entry)
    finally:
        scorer_mod.INVESTIGATION_SCENARIOS["gq_032"] = original

    assert result.scenario_recreated is False
    assert result.overall_pass is False
    assert any("Scenario setup failed" in note for note in result.notes)


@pytest.mark.asyncio
async def test_scenario_run_investigation_called_with_correct_args():
    """run_investigation is called with the alert_id from setup and correct metric."""
    from clubos2.eval.investigator_scorer import run_investigation_scenario
    from eval.golden.schema import GoldenEntry, QuestionType, ExpectedConfidence

    entry = GoldenEntry(
        id="gq_034",
        question="Investigate the alert on digital_merchandise_revenue?",
        question_type=QuestionType.INVESTIGATION,
        expected_answer_facts=["investigation completes"],
        expected_metric_names=["digital_merchandise_revenue"],
        required_citation_sources=[],
        expected_confidence=ExpectedConfidence.LOW,
        author="test",
        created_at="2026-07-01",
    )

    mock_result = MagicMock()
    mock_result.status = "completed"
    mock_result.model_dump.return_value = {
        "status": "completed",
        "finding": {
            "is_seasonal_or_expected": False,
            "confidence": "low",
            "tools_called": ["web_search"],
            "citations": [],
            "total_steps": 2,
            "cause_hypothesis": "External trend.",
            "evidence_summary": "- Web evidence",
            "data_gaps": ["internal_data"],
        },
    }

    import clubos2.eval.investigator_scorer as scorer_mod
    original = scorer_mod.INVESTIGATION_SCENARIOS["gq_034"]
    scorer_mod.INVESTIGATION_SCENARIOS["gq_034"] = AsyncMock(return_value="alrt_eval_test_034")

    try:
        with patch("clubos2.eval.investigator_scorer.run_investigation", new_callable=AsyncMock, return_value=mock_result) as mock_run:
            result = await run_investigation_scenario(entry)
            # Verify run_investigation was called once
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args.alert_id == "alrt_eval_test_034"
            assert call_args.metric_name == "digital_merchandise_revenue"
    finally:
        scorer_mod.INVESTIGATION_SCENARIOS["gq_034"] = original

    assert result.scenario_recreated is True
