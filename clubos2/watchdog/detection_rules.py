from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Callable
from uuid import uuid4

from pydantic import BaseModel

from clubos2.watchdog.alerts_schema import AlertSeverity, AlertType, WatchdogAlertCreate
from clubos2.watchdog.priority_board_reader import PriorityBoardDiff

logger = logging.getLogger("clubos.watchdog.rules")


class DetectionContext(BaseModel):
    top_n: int = 10
    rank_jump_threshold: int = 5
    score_jump_threshold: float = 0.20
    persistence_threshold_runs: int = 3
    run_id: str


class DetectionResult(BaseModel):
    fired: bool
    rule_name: str
    alert: WatchdogAlertCreate | None = None
    reason: str


def _make_alert(
    diff: PriorityBoardDiff,
    alert_type: AlertType,
    severity: AlertSeverity,
    rule_name: str,
    run_id: str,
    reason: str,
) -> WatchdogAlertCreate:
    return WatchdogAlertCreate(
        alert_id=f"alrt_{uuid4().hex[:16]}",
        metric_name=diff.metric_name,
        alert_type=alert_type,
        severity=severity,
        current_rank=diff.current_rank or 0,
        previous_rank=diff.previous_rank,
        rank_delta=diff.rank_delta,
        score_current=diff.current_score or 0.0,
        score_previous=diff.previous_score,
        triggered_by_rule=rule_name,
        context_snapshot=json.dumps(diff.model_dump(mode="json")),
        source="data/gold_snapshots/gold_priority_board.csv",
        run_id=run_id,
    )


# ── Rule 1: new_in_top_n ─────────────────────────────────────────────────────

def rule_new_in_top_n(diff: PriorityBoardDiff, ctx: DetectionContext) -> DetectionResult:
    """Fires when a metric appears in the top N for the first time (no previous snapshot)."""
    if not (diff.is_new_in_top_n and diff.current_rank is not None and diff.current_rank <= ctx.top_n):
        return DetectionResult(fired=False, rule_name="new_in_top_n", reason="not new in top n")
    severity = AlertSeverity.CRITICAL if diff.current_rank <= 5 else AlertSeverity.WARNING
    reason = f"{diff.metric_name} entered the top {ctx.top_n} at rank {diff.current_rank}"
    return DetectionResult(
        fired=True,
        rule_name="new_in_top_n",
        alert=_make_alert(diff, AlertType.NEW_IN_TOP_N, severity, "new_in_top_n", ctx.run_id, reason),
        reason=reason,
    )


# ── Rule 2: rank_jumped_into_top ─────────────────────────────────────────────

def rule_rank_jumped_into_top(diff: PriorityBoardDiff, ctx: DetectionContext) -> DetectionResult:
    """Fires when metric was ON the board outside top N, now inside top N."""
    if diff.is_new_in_top_n:
        return DetectionResult(fired=False, rule_name="rank_jumped_into_top", reason="handled by new_in_top_n")
    if not (
        diff.previous_rank is not None
        and diff.current_rank is not None
        and diff.previous_rank > ctx.top_n
        and diff.current_rank <= ctx.top_n
    ):
        return DetectionResult(fired=False, rule_name="rank_jumped_into_top", reason="not a jump into top n")
    reason = f"{diff.metric_name} moved from rank {diff.previous_rank} to {diff.current_rank}"
    return DetectionResult(
        fired=True,
        rule_name="rank_jumped_into_top",
        alert=_make_alert(diff, AlertType.RANK_JUMPED_INTO_TOP, AlertSeverity.WARNING, "rank_jumped_into_top", ctx.run_id, reason),
        reason=reason,
    )


# ── Rule 3: large_rank_change ─────────────────────────────────────────────────

def rule_large_rank_change(diff: PriorityBoardDiff, ctx: DetectionContext) -> DetectionResult:
    """Fires when both ranks are within top N but the rank shift is large."""
    if (
        diff.rank_delta is None
        or diff.current_rank is None
        or diff.previous_rank is None
        or abs(diff.rank_delta) < ctx.rank_jump_threshold
        or diff.current_rank > ctx.top_n
        or diff.previous_rank > ctx.top_n
    ):
        return DetectionResult(fired=False, rule_name="large_rank_change", reason="rank change below threshold or outside top n")
    severity = AlertSeverity.WARNING if diff.rank_delta < 0 else AlertSeverity.INFO
    reason = f"{diff.metric_name} rank shifted by {diff.rank_delta} (now {diff.current_rank}, was {diff.previous_rank})"
    return DetectionResult(
        fired=True,
        rule_name="large_rank_change",
        alert=_make_alert(diff, AlertType.RANK_DROPPED_SIGNIFICANTLY, severity, "large_rank_change", ctx.run_id, reason),
        reason=reason,
    )


# ── Rule 4: large_score_jump ─────────────────────────────────────────────────

def rule_large_score_jump(diff: PriorityBoardDiff, ctx: DetectionContext) -> DetectionResult:
    """Fires when the score changes significantly regardless of rank."""
    if diff.score_delta is None or abs(diff.score_delta) < ctx.score_jump_threshold:
        return DetectionResult(fired=False, rule_name="large_score_jump", reason="score change below threshold")
    reason = (
        f"{diff.metric_name} score changed by {diff.score_delta:+.2f} "
        f"({diff.previous_score:.2f} → {diff.current_score:.2f})"
    )
    return DetectionResult(
        fired=True,
        rule_name="large_score_jump",
        alert=_make_alert(diff, AlertType.SCORE_JUMP, AlertSeverity.WARNING, "large_score_jump", ctx.run_id, reason),
        reason=reason,
    )


# ── Rule 5: dropped_out_of_top_n ─────────────────────────────────────────────

def rule_dropped_out_of_top_n(diff: PriorityBoardDiff, ctx: DetectionContext) -> DetectionResult:
    """Fires when a metric was in top N previously but is now gone."""
    if not (diff.is_dropped_out and diff.previous_rank is not None and diff.previous_rank <= ctx.top_n):
        return DetectionResult(fired=False, rule_name="dropped_out_of_top_n", reason="not dropped out of top n")
    reason = f"{diff.metric_name} dropped out of top {ctx.top_n} (was rank {diff.previous_rank})"
    return DetectionResult(
        fired=True,
        rule_name="dropped_out_of_top_n",
        alert=_make_alert(diff, AlertType.DROPPED_OUT, AlertSeverity.INFO, "dropped_out_of_top_n", ctx.run_id, reason),
        reason=reason,
    )


# ── Rule 6: persistent_top (LTM-aware, async) ────────────────────────────────

async def rule_persistent_top(
    diff: PriorityBoardDiff,
    ctx: DetectionContext,
    memory_repo,  # AgentMemoryRepository — typed loosely to avoid circular import
) -> DetectionResult:
    """Fires when a metric has been in top N for >= persistence_threshold_runs consecutive runs."""
    if diff.current_rank is None or diff.current_rank > ctx.top_n:
        return DetectionResult(fired=False, rule_name="persistent_top", reason="not in top n")

    subject_key = f"{diff.metric_name}::present_in_top_n"
    window = timedelta(days=ctx.persistence_threshold_runs)
    history = await memory_repo.count_within(
        agent_name="watchdog",
        subject_key=subject_key,
        within=window,
    )

    if history < ctx.persistence_threshold_runs:
        return DetectionResult(
            fired=False,
            rule_name="persistent_top",
            reason=f"present in top n only {history} times in window",
        )

    reason = f"{diff.metric_name} has been in top {ctx.top_n} for {history} consecutive runs"
    return DetectionResult(
        fired=True,
        rule_name="persistent_top",
        alert=_make_alert(diff, AlertType.PERSISTENT_TOP, AlertSeverity.WARNING, "persistent_top", ctx.run_id, reason),
        reason=reason,
    )


# ── Orchestration ─────────────────────────────────────────────────────────────

SYNC_RULES: dict[str, Callable[[PriorityBoardDiff, DetectionContext], DetectionResult]] = {
    "new_in_top_n": rule_new_in_top_n,
    "rank_jumped_into_top": rule_rank_jumped_into_top,
    "large_rank_change": rule_large_rank_change,
    "large_score_jump": rule_large_score_jump,
    "dropped_out_of_top_n": rule_dropped_out_of_top_n,
}


async def apply_all_rules(
    diffs: list[PriorityBoardDiff],
    context: DetectionContext,
    memory_repo,  # AgentMemoryRepository
) -> list[DetectionResult]:
    """Run every rule against every diff. Mixed sync+async. Returns all results."""
    results: list[DetectionResult] = []
    for diff in diffs:
        for name, rule_fn in SYNC_RULES.items():
            results.append(rule_fn(diff, context))
        results.append(await rule_persistent_top(diff, context, memory_repo))
    return results
