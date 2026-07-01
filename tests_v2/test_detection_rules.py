from __future__ import annotations
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

from clubos2.watchdog.detection_rules import (
    DetectionContext,
    rule_new_in_top_n,
    rule_rank_jumped_into_top,
    rule_large_rank_change,
    rule_large_score_jump,
    rule_dropped_out_of_top_n,
    rule_persistent_top,
    apply_all_rules,
)
from clubos2.watchdog.priority_board_reader import PriorityBoardDiff
from clubos2.watchdog.alerts_schema import AlertSeverity, AlertType


def make_ctx(**kwargs) -> DetectionContext:
    defaults = {
        "run_id": f"run_{uuid4().hex[:8]}",
        "top_n": 10,
        "rank_jump_threshold": 5,
        "score_jump_threshold": 0.20,
    }
    return DetectionContext(**{**defaults, **kwargs})


def make_diff(**kwargs) -> PriorityBoardDiff:
    defaults = {
        "metric_name": "test_metric",
        "business_name": "Test Metric",
        "current_rank": 5,
        "current_score": 0.8,
        "previous_rank": 6,
        "previous_score": 0.6,
        "rank_delta": 1,
        "score_delta": 0.2,
        "is_new_in_top_n": False,
        "is_dropped_out": False,
        "is_persistent": False,
    }
    return PriorityBoardDiff(**{**defaults, **kwargs})


# ── rule_new_in_top_n ─────────────────────────────────────────────────────────

class TestRuleNewInTopN:
    def test_fires_critical_when_rank_in_top5(self):
        diff = make_diff(is_new_in_top_n=True, current_rank=3, previous_rank=None, rank_delta=None, score_delta=None, previous_score=None)
        result = rule_new_in_top_n(diff, make_ctx())
        assert result.fired is True
        assert result.rule_name == "new_in_top_n"
        assert result.alert is not None
        assert result.alert.severity == AlertSeverity.CRITICAL
        assert result.alert.alert_type == AlertType.NEW_IN_TOP_N

    def test_fires_warning_when_rank_between_6_and_10(self):
        diff = make_diff(is_new_in_top_n=True, current_rank=8, previous_rank=None, rank_delta=None, score_delta=None, previous_score=None)
        result = rule_new_in_top_n(diff, make_ctx())
        assert result.fired is True
        assert result.alert is not None
        assert result.alert.severity == AlertSeverity.WARNING

    def test_does_not_fire_when_rank_outside_top_n(self):
        diff = make_diff(is_new_in_top_n=True, current_rank=15, previous_rank=None, rank_delta=None, score_delta=None, previous_score=None)
        result = rule_new_in_top_n(diff, make_ctx(top_n=10))
        assert result.fired is False
        assert result.alert is None

    def test_does_not_fire_when_not_new(self):
        diff = make_diff(is_new_in_top_n=False, current_rank=3)
        result = rule_new_in_top_n(diff, make_ctx())
        assert result.fired is False
        assert result.alert is None

    def test_alert_contains_metric_name(self):
        diff = make_diff(is_new_in_top_n=True, current_rank=2, previous_rank=None, rank_delta=None, score_delta=None, previous_score=None, metric_name="churn_rate")
        result = rule_new_in_top_n(diff, make_ctx())
        assert result.alert.metric_name == "churn_rate"

    def test_boundary_rank_5_is_critical(self):
        diff = make_diff(is_new_in_top_n=True, current_rank=5, previous_rank=None, rank_delta=None, score_delta=None, previous_score=None)
        result = rule_new_in_top_n(diff, make_ctx())
        assert result.alert.severity == AlertSeverity.CRITICAL

    def test_boundary_rank_6_is_warning(self):
        diff = make_diff(is_new_in_top_n=True, current_rank=6, previous_rank=None, rank_delta=None, score_delta=None, previous_score=None)
        result = rule_new_in_top_n(diff, make_ctx())
        assert result.alert.severity == AlertSeverity.WARNING


# ── rule_rank_jumped_into_top ─────────────────────────────────────────────────

class TestRuleRankJumpedIntoTop:
    def test_fires_when_jumped_from_outside_to_inside_top_n(self):
        diff = make_diff(is_new_in_top_n=False, previous_rank=15, current_rank=8, rank_delta=7)
        result = rule_rank_jumped_into_top(diff, make_ctx())
        assert result.fired is True
        assert result.rule_name == "rank_jumped_into_top"
        assert result.alert is not None
        assert result.alert.alert_type == AlertType.RANK_JUMPED_INTO_TOP
        assert result.alert.severity == AlertSeverity.WARNING

    def test_does_not_fire_when_both_already_in_top_n(self):
        diff = make_diff(is_new_in_top_n=False, previous_rank=5, current_rank=3, rank_delta=2)
        result = rule_rank_jumped_into_top(diff, make_ctx())
        assert result.fired is False

    def test_does_not_fire_when_is_new_in_top_n(self):
        diff = make_diff(is_new_in_top_n=True, previous_rank=None, current_rank=5, rank_delta=None)
        result = rule_rank_jumped_into_top(diff, make_ctx())
        assert result.fired is False
        assert "new_in_top_n" in result.reason

    def test_does_not_fire_when_still_outside_top_n(self):
        diff = make_diff(is_new_in_top_n=False, previous_rank=20, current_rank=15, rank_delta=5)
        result = rule_rank_jumped_into_top(diff, make_ctx())
        assert result.fired is False

    def test_does_not_fire_when_moved_out_of_top_n(self):
        diff = make_diff(is_new_in_top_n=False, previous_rank=5, current_rank=15, rank_delta=-10)
        result = rule_rank_jumped_into_top(diff, make_ctx())
        assert result.fired is False

    def test_alert_has_correct_ranks(self):
        diff = make_diff(is_new_in_top_n=False, previous_rank=15, current_rank=8, rank_delta=7)
        result = rule_rank_jumped_into_top(diff, make_ctx())
        assert result.alert.previous_rank == 15
        assert result.alert.current_rank == 8


# ── rule_large_rank_change ────────────────────────────────────────────────────

class TestRuleLargeRankChange:
    def test_fires_when_large_rank_delta_within_top_n(self):
        diff = make_diff(rank_delta=7, current_rank=3, previous_rank=10)
        result = rule_large_rank_change(diff, make_ctx())
        assert result.fired is True
        assert result.rule_name == "large_rank_change"
        assert result.alert is not None
        assert result.alert.alert_type == AlertType.RANK_DROPPED_SIGNIFICANTLY

    def test_does_not_fire_when_delta_below_threshold(self):
        diff = make_diff(rank_delta=2, current_rank=5, previous_rank=7)
        result = rule_large_rank_change(diff, make_ctx())
        assert result.fired is False

    def test_does_not_fire_when_current_rank_outside_top_n(self):
        diff = make_diff(rank_delta=7, current_rank=15, previous_rank=8)
        result = rule_large_rank_change(diff, make_ctx())
        assert result.fired is False

    def test_does_not_fire_when_previous_rank_outside_top_n(self):
        diff = make_diff(rank_delta=7, current_rank=5, previous_rank=12)
        result = rule_large_rank_change(diff, make_ctx())
        assert result.fired is False

    def test_severity_warning_when_rank_delta_negative(self):
        # negative rank_delta means moved down (worse)
        diff = make_diff(rank_delta=-6, current_rank=9, previous_rank=3)
        result = rule_large_rank_change(diff, make_ctx())
        assert result.fired is True
        assert result.alert.severity == AlertSeverity.WARNING

    def test_severity_info_when_rank_delta_positive(self):
        # positive rank_delta means moved up (better)
        diff = make_diff(rank_delta=6, current_rank=3, previous_rank=9)
        result = rule_large_rank_change(diff, make_ctx())
        assert result.fired is True
        assert result.alert.severity == AlertSeverity.INFO

    def test_does_not_fire_when_rank_delta_none(self):
        diff = make_diff(rank_delta=None, current_rank=5, previous_rank=3)
        result = rule_large_rank_change(diff, make_ctx())
        assert result.fired is False

    def test_boundary_exactly_at_threshold_does_not_fire(self):
        # abs(4) < 5, should not fire
        diff = make_diff(rank_delta=4, current_rank=5, previous_rank=9)
        result = rule_large_rank_change(diff, make_ctx(rank_jump_threshold=5))
        assert result.fired is False

    def test_boundary_one_above_threshold_fires(self):
        diff = make_diff(rank_delta=5, current_rank=5, previous_rank=10)
        result = rule_large_rank_change(diff, make_ctx(rank_jump_threshold=5))
        assert result.fired is True


# ── rule_large_score_jump ─────────────────────────────────────────────────────

class TestRuleLargeScoreJump:
    def test_fires_on_positive_large_score_change(self):
        diff = make_diff(score_delta=0.25, current_score=0.85, previous_score=0.60)
        result = rule_large_score_jump(diff, make_ctx())
        assert result.fired is True
        assert result.rule_name == "large_score_jump"
        assert result.alert is not None
        assert result.alert.alert_type == AlertType.SCORE_JUMP
        assert result.alert.severity == AlertSeverity.WARNING

    def test_does_not_fire_when_score_change_small(self):
        diff = make_diff(score_delta=0.05, current_score=0.65, previous_score=0.60)
        result = rule_large_score_jump(diff, make_ctx())
        assert result.fired is False
        assert result.alert is None

    def test_fires_on_negative_large_score_change(self):
        diff = make_diff(score_delta=-0.30, current_score=0.50, previous_score=0.80)
        result = rule_large_score_jump(diff, make_ctx())
        assert result.fired is True
        assert result.alert is not None

    def test_does_not_fire_when_score_delta_none(self):
        diff = make_diff(score_delta=None, current_score=0.80, previous_score=None)
        result = rule_large_score_jump(diff, make_ctx())
        assert result.fired is False

    def test_boundary_exactly_at_threshold_does_not_fire(self):
        # abs(0.19) < 0.20
        diff = make_diff(score_delta=0.19, current_score=0.79, previous_score=0.60)
        result = rule_large_score_jump(diff, make_ctx(score_jump_threshold=0.20))
        assert result.fired is False

    def test_boundary_exactly_at_threshold_fires(self):
        diff = make_diff(score_delta=0.20, current_score=0.80, previous_score=0.60)
        result = rule_large_score_jump(diff, make_ctx(score_jump_threshold=0.20))
        assert result.fired is True

    def test_reason_includes_score_values(self):
        diff = make_diff(score_delta=0.25, current_score=0.85, previous_score=0.60)
        result = rule_large_score_jump(diff, make_ctx())
        assert "0.85" in result.reason or "0.60" in result.reason


# ── rule_dropped_out_of_top_n ─────────────────────────────────────────────────

class TestRuleDroppedOutOfTopN:
    def test_fires_when_dropped_out_from_top_n(self):
        diff = make_diff(
            is_dropped_out=True,
            previous_rank=5,
            current_rank=None,
            current_score=None,
            rank_delta=None,
            score_delta=None,
        )
        result = rule_dropped_out_of_top_n(diff, make_ctx())
        assert result.fired is True
        assert result.rule_name == "dropped_out_of_top_n"
        assert result.alert is not None
        assert result.alert.severity == AlertSeverity.INFO
        assert result.alert.alert_type == AlertType.DROPPED_OUT

    def test_does_not_fire_when_previous_rank_outside_top_n(self):
        diff = make_diff(
            is_dropped_out=True,
            previous_rank=15,
            current_rank=None,
            current_score=None,
            rank_delta=None,
            score_delta=None,
        )
        result = rule_dropped_out_of_top_n(diff, make_ctx())
        assert result.fired is False

    def test_does_not_fire_when_not_dropped_out(self):
        diff = make_diff(is_dropped_out=False, previous_rank=5, current_rank=5)
        result = rule_dropped_out_of_top_n(diff, make_ctx())
        assert result.fired is False

    def test_reason_mentions_previous_rank(self):
        diff = make_diff(
            is_dropped_out=True,
            previous_rank=3,
            current_rank=None,
            current_score=None,
            rank_delta=None,
            score_delta=None,
        )
        result = rule_dropped_out_of_top_n(diff, make_ctx())
        assert "3" in result.reason

    def test_does_not_fire_when_previous_rank_none(self):
        diff = make_diff(
            is_dropped_out=True,
            previous_rank=None,
            current_rank=None,
            current_score=None,
            rank_delta=None,
            score_delta=None,
        )
        result = rule_dropped_out_of_top_n(diff, make_ctx())
        assert result.fired is False


# ── rule_persistent_top (async) ───────────────────────────────────────────────

class TestRulePersistentTop:
    @pytest.mark.asyncio
    async def test_fires_when_history_meets_threshold(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=3)
        diff = make_diff(current_rank=5)
        ctx = make_ctx(persistence_threshold_runs=3)
        result = await rule_persistent_top(diff, ctx, memory_repo)
        assert result.fired is True
        assert result.rule_name == "persistent_top"
        assert result.alert is not None
        assert result.alert.alert_type == AlertType.PERSISTENT_TOP
        assert result.alert.severity == AlertSeverity.WARNING

    @pytest.mark.asyncio
    async def test_does_not_fire_when_history_below_threshold(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=1)
        diff = make_diff(current_rank=5)
        ctx = make_ctx(persistence_threshold_runs=3)
        result = await rule_persistent_top(diff, ctx, memory_repo)
        assert result.fired is False
        assert result.alert is None

    @pytest.mark.asyncio
    async def test_does_not_fire_when_outside_top_n(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=10)
        diff = make_diff(current_rank=15)
        ctx = make_ctx(top_n=10)
        result = await rule_persistent_top(diff, ctx, memory_repo)
        assert result.fired is False
        # Memory should NOT be queried when rank is outside top N
        memory_repo.count_within.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_fire_when_current_rank_none(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=10)
        diff = make_diff(current_rank=None, current_score=None, is_dropped_out=True, rank_delta=None, score_delta=None)
        ctx = make_ctx(top_n=10)
        result = await rule_persistent_top(diff, ctx, memory_repo)
        assert result.fired is False
        memory_repo.count_within.assert_not_called()

    @pytest.mark.asyncio
    async def test_fires_when_history_exceeds_threshold(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=7)
        diff = make_diff(current_rank=2)
        ctx = make_ctx(persistence_threshold_runs=3)
        result = await rule_persistent_top(diff, ctx, memory_repo)
        assert result.fired is True

    @pytest.mark.asyncio
    async def test_memory_queried_with_correct_subject_key(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=3)
        diff = make_diff(metric_name="churn_rate", current_rank=3)
        ctx = make_ctx(persistence_threshold_runs=3)
        await rule_persistent_top(diff, ctx, memory_repo)
        call_kwargs = memory_repo.count_within.call_args
        assert call_kwargs.kwargs["subject_key"] == "churn_rate::present_in_top_n"
        assert call_kwargs.kwargs["agent_name"] == "watchdog"


# ── apply_all_rules ───────────────────────────────────────────────────────────

class TestApplyAllRules:
    @pytest.mark.asyncio
    async def test_returns_6_results_per_diff(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=0)
        diffs = [make_diff(metric_name=f"metric_{i}") for i in range(3)]
        ctx = make_ctx()
        results = await apply_all_rules(diffs, ctx, memory_repo)
        # 3 diffs × 6 rules = 18 results
        assert len(results) == 18

    @pytest.mark.asyncio
    async def test_all_fired_false_for_no_change_diffs(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=0)
        # Diffs with no changes large enough to fire
        diffs = [
            make_diff(
                metric_name=f"metric_{i}",
                is_new_in_top_n=False,
                is_dropped_out=False,
                current_rank=5,
                previous_rank=6,
                rank_delta=1,
                score_delta=0.01,
                current_score=0.80,
                previous_score=0.79,
            )
            for i in range(3)
        ]
        ctx = make_ctx()
        results = await apply_all_rules(diffs, ctx, memory_repo)
        fired_alerts = [r for r in results if r.fired]
        assert len(fired_alerts) == 0

    @pytest.mark.asyncio
    async def test_returns_results_for_all_rule_names(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=0)
        diff = make_diff()
        ctx = make_ctx()
        results = await apply_all_rules([diff], ctx, memory_repo)
        rule_names = {r.rule_name for r in results}
        expected = {
            "new_in_top_n",
            "rank_jumped_into_top",
            "large_rank_change",
            "large_score_jump",
            "dropped_out_of_top_n",
            "persistent_top",
        }
        assert rule_names == expected

    @pytest.mark.asyncio
    async def test_new_metric_fires_new_in_top_n(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=0)
        diff = make_diff(
            is_new_in_top_n=True,
            current_rank=3,
            previous_rank=None,
            rank_delta=None,
            score_delta=None,
            previous_score=None,
        )
        ctx = make_ctx()
        results = await apply_all_rules([diff], ctx, memory_repo)
        fired = [r for r in results if r.fired]
        assert any(r.rule_name == "new_in_top_n" for r in fired)

    @pytest.mark.asyncio
    async def test_single_diff_produces_6_results(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=0)
        diff = make_diff()
        ctx = make_ctx()
        results = await apply_all_rules([diff], ctx, memory_repo)
        assert len(results) == 6

    @pytest.mark.asyncio
    async def test_empty_diffs_returns_empty_list(self):
        memory_repo = AsyncMock()
        memory_repo.count_within = AsyncMock(return_value=0)
        results = await apply_all_rules([], make_ctx(), memory_repo)
        assert results == []
