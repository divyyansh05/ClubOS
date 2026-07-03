from __future__ import annotations

from pydantic import BaseModel

from clubos2.eval.runner import EvalRun, RunResult
from eval.golden.schema import GoldenEntry, GoldenSet

VALID_SOURCE_PREFIXES = (
    "gold.",
    "skills.",
    "metric_registry",
    "watchdog_alerts",
    "investigations",
    "web_search:",
)


def _assert_canonical_source(source: str, context: str) -> None:
    """Hard-fail if a source is not in canonical form.

    Called for both expected (golden set) and actual (Scout output) sources.
    Fails loud so non-canonical sources cannot silently pass tests.
    See docs/eval_methodology.md for the canonical source policy.
    """
    if not source.startswith(VALID_SOURCE_PREFIXES):
        raise ValueError(
            f"Non-canonical source in {context}: {source!r}. "
            f"Expected prefix from {VALID_SOURCE_PREFIXES}. "
            "Fix at emission — do not add a mapping here."
        )


class BehaviouralScore(BaseModel):
    entry_id: str

    # Refusal check (UNANSWERABLE entries)
    expected_to_refuse: bool
    did_refuse: bool
    refusal_correct: bool

    # Assumption check (AMBIGUOUS entries)
    expected_to_state_assumption: bool
    did_state_assumption: bool
    assumption_correct: bool

    # Citation presence (QUANTITATIVE/NARRATIVE/MIXED entries)
    expected_citation_sources: list[str]
    actual_citation_sources: list[str]
    citation_coverage: float
    citation_correct: bool

    # Metric query check (QUANTITATIVE/MIXED entries)
    expected_metric_names: list[str]
    actual_metrics_queried: list[str]
    metric_query_correct: bool

    # Overall
    overall_pass: bool
    failures: list[str]


def score_behaviour(result: RunResult, entry: GoldenEntry) -> BehaviouralScore:
    """Apply the right checks based on entry.question_type."""
    failures: list[str] = []

    # Refusal check: expected for UNANSWERABLE entries
    expected_refuse = entry.must_refuse
    did_refuse = (
        result.scout_answer is not None
        and result.scout_answer.confidence.value == "low"
        and len(result.scout_answer.citations) == 0
    )
    refusal_correct = expected_refuse == did_refuse
    if not refusal_correct:
        failures.append(f"Refusal: expected={expected_refuse}, actual={did_refuse}")

    # Assumption check: expected for AMBIGUOUS entries
    expected_assumption = entry.must_state_assumption
    did_state = (
        result.scout_answer is not None
        and len(result.scout_answer.assumptions_made) > 0
    )
    assumption_correct = (not expected_assumption) or did_state
    if expected_assumption and not did_state:
        failures.append("Expected to state an assumption, none stated")

    # Citation check: applies when required_citation_sources is populated
    expected_sources = set(entry.required_citation_sources)
    for src in expected_sources:
        _assert_canonical_source(src, f"golden set expected_citation_sources for {entry.id}")
    actual_sources = set(
        c.source
        for c in (result.scout_answer.citations if result.scout_answer else [])
    )
    for src in actual_sources:
        _assert_canonical_source(src, f"scout_answer.citations for {result.entry_id}")
    coverage = (
        len(expected_sources & actual_sources) / len(expected_sources)
        if expected_sources
        else 1.0
    )
    citation_correct = expected_sources.issubset(actual_sources) if expected_sources else True
    if expected_sources and not citation_correct:
        missing = expected_sources - actual_sources
        failures.append(f"Missing citations: {sorted(missing)}")

    # Metric query check: applies when expected_metric_names is populated
    expected_metrics = set(entry.expected_metric_names)
    actual_metrics = set(
        result.scout_answer.metrics_queried if result.scout_answer else []
    )
    metric_correct = expected_metrics.issubset(actual_metrics) if expected_metrics else True
    if expected_metrics and not metric_correct:
        missing = expected_metrics - actual_metrics
        failures.append(f"Missing metrics queried: {sorted(missing)}")

    overall = all([refusal_correct, assumption_correct, citation_correct, metric_correct])

    return BehaviouralScore(
        entry_id=result.entry_id,
        expected_to_refuse=expected_refuse,
        did_refuse=did_refuse,
        refusal_correct=refusal_correct,
        expected_to_state_assumption=expected_assumption,
        did_state_assumption=did_state,
        assumption_correct=assumption_correct,
        expected_citation_sources=sorted(expected_sources),
        actual_citation_sources=sorted(actual_sources),
        citation_coverage=coverage,
        citation_correct=citation_correct,
        expected_metric_names=sorted(expected_metrics),
        actual_metrics_queried=sorted(actual_metrics),
        metric_query_correct=metric_correct,
        overall_pass=overall,
        failures=failures,
    )


def score_behaviour_batch(eval_run: EvalRun, golden_set: GoldenSet) -> list[BehaviouralScore]:
    entries_by_id = {e.id: e for e in golden_set.entries}
    return [
        score_behaviour(result, entries_by_id[result.entry_id])
        for result in eval_run.results
    ]


def aggregate_behaviour(scores: list[BehaviouralScore]) -> dict:
    total = len(scores)
    return {
        "total": total,
        "overall_pass_rate": sum(1 for s in scores if s.overall_pass) / max(total, 1),
        "refusal_correct_rate": sum(1 for s in scores if s.refusal_correct) / max(total, 1),
        "citation_correct_rate": sum(1 for s in scores if s.citation_correct) / max(total, 1),
        "average_citation_coverage": sum(s.citation_coverage for s in scores) / max(total, 1),
    }
