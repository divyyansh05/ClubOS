from __future__ import annotations

import pytest

from clubos2.agents.scout_schemas import Citation, Confidence, ScoutAnswer
from clubos2.eval.behavioural_scorer import (
    BehaviouralScore,
    aggregate_behaviour,
    score_behaviour,
    score_behaviour_batch,
)
from clubos2.eval.runner import EvalRun, RunResult
from eval.golden.schema import ExpectedConfidence, GoldenEntry, GoldenSet, QuestionType


def _make_entry(
    entry_id: str = "gq_001",
    question_type: QuestionType = QuestionType.QUANTITATIVE,
    must_refuse: bool = False,
    must_state_assumption: bool = False,
    required_citation_sources: list[str] | None = None,
    expected_metric_names: list[str] | None = None,
) -> GoldenEntry:
    return GoldenEntry(
        id=entry_id,
        question="Test question?",
        question_type=question_type,
        expected_answer_facts=[],
        expected_metric_names=expected_metric_names or [],
        required_citation_sources=required_citation_sources or [],
        expected_confidence=ExpectedConfidence.HIGH,
        must_state_assumption=must_state_assumption,
        must_refuse=must_refuse,
        tempts_fabrication=False,
        tempts_injection=False,
        author="Test",
        created_at="2026-06-24",
    )


def _make_result(
    entry_id: str = "gq_001",
    confidence: Confidence = Confidence.HIGH,
    citations: list[Citation] | None = None,
    assumptions_made: list[str] | None = None,
    metrics_queried: list[str] | None = None,
    error: str | None = None,
) -> RunResult:
    if error:
        return RunResult(
            entry_id=entry_id, question="q", question_type="quantitative",
            scout_answer=None, latency_ms=0, error=error,
        )
    return RunResult(
        entry_id=entry_id,
        question="q",
        question_type="quantitative",
        scout_answer=ScoutAnswer(
            answer="Test answer.",
            citations=citations or [],
            confidence=confidence,
            assumptions_made=assumptions_made or [],
            metrics_queried=metrics_queried or [],
        ),
        latency_ms=0,
    )


def test_unanswerable_refused_correctly():
    entry = _make_entry("gq_019", QuestionType.UNANSWERABLE, must_refuse=True)
    result = _make_result("gq_019", confidence=Confidence.LOW, citations=[])
    score = score_behaviour(result, entry)
    assert score.refusal_correct is True
    assert score.overall_pass is True


def test_unanswerable_not_refused():
    entry = _make_entry("gq_019", QuestionType.UNANSWERABLE, must_refuse=True)
    result = _make_result("gq_019", confidence=Confidence.HIGH, citations=[
        Citation(claim="Player earns €50M", source="gold.priority_board")
    ])
    score = score_behaviour(result, entry)
    assert score.refusal_correct is False
    assert score.overall_pass is False
    assert any("Refusal" in f for f in score.failures)


def test_ambiguous_assumption_stated():
    entry = _make_entry("gq_016", QuestionType.AMBIGUOUS, must_state_assumption=True)
    result = _make_result("gq_016", assumptions_made=["Assumed ecommerce platform"])
    score = score_behaviour(result, entry)
    assert score.assumption_correct is True


def test_quantitative_correct_citation():
    entry = _make_entry(
        "gq_001",
        required_citation_sources=["gold.priority_board"],
    )
    result = _make_result(
        "gq_001",
        citations=[Citation(claim="Value is 85420", source="gold.priority_board")],
    )
    score = score_behaviour(result, entry)
    assert score.citation_correct is True


def test_quantitative_wrong_citation():
    entry = _make_entry(
        "gq_001",
        required_citation_sources=["gold.priority_board"],
    )
    result = _make_result(
        "gq_001",
        citations=[Citation(claim="Value is X", source="gold.metrics_monthly")],
    )
    score = score_behaviour(result, entry)
    assert score.citation_correct is False
    assert any("Missing citations" in f for f in score.failures)


def test_aggregate_behaviour():
    entry1 = _make_entry("gq_001", required_citation_sources=["gold.priority_board"])
    result1 = _make_result("gq_001", citations=[Citation(claim="x", source="gold.priority_board")])
    score1 = score_behaviour(result1, entry1)

    entry2 = _make_entry("gq_019", QuestionType.UNANSWERABLE, must_refuse=True)
    result2 = _make_result("gq_019", confidence=Confidence.HIGH)
    score2 = score_behaviour(result2, entry2)

    agg = aggregate_behaviour([score1, score2])
    assert agg["total"] == 2
    assert 0.0 <= agg["overall_pass_rate"] <= 1.0
