from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from clubos2.eval.watchdog_scorer import check_fact, WatchdogScenarioResult
from clubos2.watchdog.orchestrator import WatchdogRunResult


def make_result(**kwargs) -> WatchdogRunResult:
    defaults = {
        "run_id": "wdog_test",
        "started_at": datetime.now(timezone.utc),
        "finished_at": datetime.now(timezone.utc),
        "duration_seconds": 1.0,
        "metrics_evaluated": 10,
        "rules_evaluated": 60,
        "rules_fired": 5,
        "alerts_created": 3,
        "alerts_deduped": 0,
        "snapshot_id": "snap_test",
        "alert_ids": ["alrt_a", "alrt_b", "alrt_c"],
        "errors": [],
    }
    return WatchdogRunResult(**{**defaults, **kwargs})


class TestCheckFact:
    def test_alerts_created_equal(self):
        result = make_result(alerts_created=3)
        assert check_fact("alerts_created == 3", result) == "satisfied"
        assert check_fact("alerts_created == 5", result) == "failed"

    def test_alerts_created_greater(self):
        result = make_result(alerts_created=3)
        assert check_fact("alerts_created > 0", result) == "satisfied"
        assert check_fact("alerts_created > 3", result) == "failed"

    def test_alerts_created_gte(self):
        result = make_result(alerts_created=1)
        assert check_fact("alerts_created >= 1", result) == "satisfied"
        result_zero = make_result(alerts_created=0)
        assert check_fact("alerts_created >= 1", result_zero) == "failed"

    def test_alerts_deduped_equal(self):
        result = make_result(alerts_deduped=0)
        assert check_fact("alerts_deduped == 0", result) == "satisfied"
        result_nonzero = make_result(alerts_deduped=2)
        assert check_fact("alerts_deduped == 0", result_nonzero) == "failed"

    def test_alerts_deduped_greater(self):
        result = make_result(alerts_deduped=5)
        assert check_fact("alerts_deduped > 0", result) == "satisfied"
        result_zero = make_result(alerts_deduped=0)
        assert check_fact("alerts_deduped > 0", result_zero) == "failed"

    def test_alerts_deduped_gte(self):
        result = make_result(alerts_deduped=3)
        assert check_fact("alerts_deduped >= 1", result) == "satisfied"
        result_zero = make_result(alerts_deduped=0)
        assert check_fact("alerts_deduped >= 1", result_zero) == "failed"

    def test_errors_is_empty(self):
        result = make_result(errors=[])
        assert check_fact("errors is empty", result) == "satisfied"
        result_err = make_result(errors=["boom"])
        assert check_fact("errors is empty", result_err) == "failed"

    def test_errors_non_empty(self):
        result = make_result(errors=["crash"])
        assert check_fact("errors list is non-empty", result) == "satisfied"
        result_ok = make_result(errors=[])
        assert check_fact("errors list is non-empty", result_ok) == "failed"

    def test_errors_nonempty_variant(self):
        result = make_result(errors=["err1", "err2"])
        assert check_fact("errors list is nonempty", result) == "satisfied"

    def test_snapshot_id_non_empty(self):
        result = make_result(snapshot_id="snap_abc")
        assert check_fact("snapshot_id is non-empty", result) == "satisfied"
        result_empty = make_result(snapshot_id="")
        assert check_fact("snapshot_id is non-empty", result_empty) == "failed"

    def test_watchdog_result_returned(self):
        result = make_result()
        assert check_fact("WatchdogRunResult is returned (not exception)", result) == "satisfied"

    def test_uncheckable_rule_fires(self):
        result = make_result()
        verdict = check_fact("persistent_top rule fires", result)
        assert verdict == "uncheckable"

    def test_uncheckable_large_rank_change_rule(self):
        result = make_result()
        verdict = check_fact("large_rank_change rule fires", result)
        assert verdict == "uncheckable"

    def test_uncheckable_rank_delta(self):
        result = make_result()
        verdict = check_fact("rank_delta is non-zero", result)
        assert verdict == "uncheckable"

    def test_uncheckable_triggered_by_rule(self):
        result = make_result()
        verdict = check_fact("triggered_by_rule is persistent_top for at least one alert", result)
        assert verdict == "uncheckable"

    def test_unknown_fact_is_uncheckable(self):
        result = make_result()
        verdict = check_fact("some totally unknown fact", result)
        assert verdict == "uncheckable"

    def test_alerts_created_equal_zero(self):
        result = make_result(alerts_created=0)
        assert check_fact("alerts_created == 0", result) == "satisfied"
        result_nonzero = make_result(alerts_created=1)
        assert check_fact("alerts_created == 0", result_nonzero) == "failed"


@pytest.mark.asyncio
async def test_run_watchdog_scenario_setup_failure():
    """If scenario setup fails, result has scenario_recreated=False."""
    from clubos2.eval.watchdog_scorer import run_watchdog_scenario
    from eval.golden.schema import GoldenEntry, QuestionType

    entry = GoldenEntry(
        id="gq_026",
        question="First Watchdog run, no previous snapshots.",
        question_type=QuestionType.WATCHDOG_RUN,
        expected_answer_facts=["alerts_created > 0", "alerts_deduped == 0"],
        expected_confidence="high",
        author="test",
        created_at="2026-07-01",
        scenario_setup="Clear all watchdog state.",
    )

    with patch("clubos2.eval.watchdog_scorer._setup_eval_db", side_effect=RuntimeError("DB fail")):
        result = await run_watchdog_scenario(entry)

    assert result.entry_id == "gq_026"
    assert result.scenario_recreated is False
    assert len(result.notes) > 0
    assert "Scenario setup failed" in result.notes[0]


@pytest.mark.asyncio
async def test_run_watchdog_scenario_all_facts_satisfied():
    """If all facts pass, overall_pass=True."""
    from clubos2.eval.watchdog_scorer import run_watchdog_scenario
    from eval.golden.schema import GoldenEntry, QuestionType

    entry = GoldenEntry(
        id="gq_026",
        question="First Watchdog run, no previous snapshots.",
        question_type=QuestionType.WATCHDOG_RUN,
        expected_answer_facts=["alerts_deduped == 0", "errors is empty"],
        expected_confidence="high",
        author="test",
        created_at="2026-07-01",
        scenario_setup="Clear all watchdog state.",
    )

    mock_result = make_result(alerts_created=5, alerts_deduped=0, errors=[])

    with patch("clubos2.eval.watchdog_scorer._setup_eval_db"), \
         patch("clubos2.eval.watchdog_scorer.setup_gq_026", new_callable=AsyncMock), \
         patch("clubos2.eval.watchdog_scorer._run_with_eval_db", new_callable=AsyncMock, return_value=mock_result):
        result = await run_watchdog_scenario(entry)

    assert result.overall_pass is True
    assert len(result.facts_failed) == 0
    assert "alerts_deduped == 0" in result.facts_satisfied
    assert "errors is empty" in result.facts_satisfied


@pytest.mark.asyncio
async def test_run_watchdog_scenario_some_facts_failed():
    """If some facts fail, overall_pass=False and failed list is populated."""
    from clubos2.eval.watchdog_scorer import run_watchdog_scenario
    from eval.golden.schema import GoldenEntry, QuestionType

    entry = GoldenEntry(
        id="gq_026",
        question="First Watchdog run, no previous snapshots.",
        question_type=QuestionType.WATCHDOG_RUN,
        expected_answer_facts=["alerts_created > 0", "alerts_deduped == 0", "errors is empty"],
        expected_confidence="high",
        author="test",
        created_at="2026-07-01",
        scenario_setup="Clear all watchdog state.",
    )

    # alerts_created == 0 will cause "alerts_created > 0" to fail
    mock_result = make_result(alerts_created=0, alerts_deduped=0, errors=[])

    with patch("clubos2.eval.watchdog_scorer._setup_eval_db"), \
         patch("clubos2.eval.watchdog_scorer.setup_gq_026", new_callable=AsyncMock), \
         patch("clubos2.eval.watchdog_scorer._run_with_eval_db", new_callable=AsyncMock, return_value=mock_result):
        result = await run_watchdog_scenario(entry)

    assert result.overall_pass is False
    assert "alerts_created > 0" in result.facts_failed
    assert "alerts_deduped == 0" in result.facts_satisfied


@pytest.mark.asyncio
async def test_run_watchdog_scenario_uncheckable_facts_still_pass():
    """Uncheckable facts do not count as failures; overall_pass=True if no failures."""
    from clubos2.eval.watchdog_scorer import run_watchdog_scenario
    from eval.golden.schema import GoldenEntry, QuestionType

    entry = GoldenEntry(
        id="gq_028",
        question="Metric X rank change scenario.",
        question_type=QuestionType.WATCHDOG_RUN,
        expected_answer_facts=["large_rank_change rule fires", "rank_delta is non-zero", "alerts_created >= 1"],
        expected_confidence="high",
        author="test",
        created_at="2026-07-01",
        scenario_setup="Inject previous snapshot.",
    )

    mock_result = make_result(alerts_created=2, alerts_deduped=0, errors=[])

    with patch("clubos2.eval.watchdog_scorer._setup_eval_db"), \
         patch("clubos2.eval.watchdog_scorer.setup_gq_028", new_callable=AsyncMock), \
         patch("clubos2.eval.watchdog_scorer._run_with_eval_db", new_callable=AsyncMock, return_value=mock_result):
        result = await run_watchdog_scenario(entry)

    assert result.overall_pass is True
    assert len(result.facts_failed) == 0
    assert "large_rank_change rule fires" in result.facts_uncheckable
    assert "rank_delta is non-zero" in result.facts_uncheckable
    assert "alerts_created >= 1" in result.facts_satisfied


@pytest.mark.asyncio
async def test_run_watchdog_scenario_watchdog_run_fails():
    """If watchdog run itself throws, result has watchdog_result=None and overall_pass=False."""
    from clubos2.eval.watchdog_scorer import run_watchdog_scenario
    from eval.golden.schema import GoldenEntry, QuestionType

    entry = GoldenEntry(
        id="gq_026",
        question="First Watchdog run, no previous snapshots.",
        question_type=QuestionType.WATCHDOG_RUN,
        expected_answer_facts=["alerts_created > 0"],
        expected_confidence="high",
        author="test",
        created_at="2026-07-01",
        scenario_setup="Clear all watchdog state.",
    )

    with patch("clubos2.eval.watchdog_scorer._setup_eval_db"), \
         patch("clubos2.eval.watchdog_scorer.setup_gq_026", new_callable=AsyncMock), \
         patch("clubos2.eval.watchdog_scorer._run_with_eval_db", new_callable=AsyncMock, side_effect=RuntimeError("run crash")):
        result = await run_watchdog_scenario(entry)

    assert result.watchdog_result is None
    assert result.overall_pass is False
    assert any("Watchdog run failed" in note for note in result.notes)


@pytest.mark.asyncio
async def test_score_watchdog_batch():
    """score_watchdog_batch returns one result per entry."""
    from clubos2.eval.watchdog_scorer import score_watchdog_batch
    from eval.golden.schema import GoldenEntry, QuestionType

    entries = [
        GoldenEntry(
            id=f"gq_02{i}",
            question=f"Test question {i} for scenario.",
            question_type=QuestionType.WATCHDOG_RUN,
            expected_answer_facts=["errors is empty"],
            expected_confidence="high",
            author="test",
            created_at="2026-07-01",
            scenario_setup="test setup",
        )
        for i in range(6, 8)
    ]

    mock_result = make_result(alerts_created=1, alerts_deduped=0, errors=[])

    with patch("clubos2.eval.watchdog_scorer._setup_eval_db"), \
         patch("clubos2.eval.watchdog_scorer.setup_gq_026", new_callable=AsyncMock), \
         patch("clubos2.eval.watchdog_scorer.setup_gq_027", new_callable=AsyncMock), \
         patch("clubos2.eval.watchdog_scorer._run_with_eval_db", new_callable=AsyncMock, return_value=mock_result):
        results = await score_watchdog_batch(entries)

    assert len(results) == 2
    assert results[0].entry_id == "gq_026"
    assert results[1].entry_id == "gq_027"


def test_watchdog_scenario_result_model():
    """WatchdogScenarioResult can be instantiated and serialized."""
    from clubos2.eval.watchdog_scorer import WatchdogScenarioResult

    result = WatchdogScenarioResult(
        entry_id="gq_026",
        scenario_recreated=True,
        watchdog_result=None,
        expected_facts=["alerts_created > 0"],
        facts_satisfied=[],
        facts_failed=["alerts_created > 0"],
        facts_uncheckable=[],
        overall_pass=False,
        notes=["some note"],
    )
    d = result.model_dump()
    assert d["entry_id"] == "gq_026"
    assert d["overall_pass"] is False
    assert d["watchdog_result"] is None
