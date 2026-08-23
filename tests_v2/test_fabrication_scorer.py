from __future__ import annotations

import pytest

from clubos2.agents.scout_schemas import Citation, Confidence, ScoutAnswer
from clubos2.eval.fabrication_scorer import (
    FabricationScore,
    aggregate_fabrication,
    extract_numbers,
    score_fabrication,
    score_fabrication_batch,
)
from clubos2.eval.runner import EvalRun, RunResult


def _make_result(
    entry_id: str = "gq_001",
    answer: str = "",
    retrieved_contexts: list[str] | None = None,
    citation_quotes: list[str] | None = None,
    error: str | None = None,
) -> RunResult:
    if error:
        return RunResult(
            entry_id=entry_id, question="q", question_type="quantitative",
            scout_answer=None, latency_ms=0, error=error,
        )
    citations = [
        Citation(claim="c", source="s", quote=q)
        for q in (citation_quotes or [])
    ]
    return RunResult(
        entry_id=entry_id,
        question="q",
        question_type="quantitative",
        scout_answer=ScoutAnswer(
            answer=answer,
            citations=citations,
            confidence=Confidence.HIGH,
            retrieved_contexts=retrieved_contexts or [],
        ),
        latency_ms=0,
    )


def test_extract_numbers_mixed_formats():
    nums = extract_numbers("Real Madrid ranks 4th with €1,234.5 revenue and 2.1x growth")
    assert "4" in nums
    assert "1234.5" in nums
    assert "2.1" in nums


def test_extract_numbers_ordinals():
    nums = extract_numbers("Ranked 1st and 3rd this season")
    assert "1" in nums
    assert "3" in nums


def test_extract_numbers_normalisation():
    # "1,234" and "1234" should normalise to same canonical form
    n1 = extract_numbers("1,234")
    n2 = extract_numbers("1234")
    assert set(n1) == set(n2)


def test_clean_answer_no_fabrication():
    result = _make_result(
        answer="Streaming users were 85420 in November.",
        retrieved_contexts=["Daily users reached 85420 in November 2025."],
    )
    score = score_fabrication(result)
    assert score.fabricated_numbers == []
    assert score.has_fabrication is False


def test_fabricated_number_detected():
    result = _make_result(
        answer="Revenue was €100M this quarter.",
        retrieved_contexts=["The quarter had no specific revenue numbers."],
    )
    score = score_fabrication(result)
    assert score.has_fabrication is True
    assert "100" in score.fabricated_numbers


def test_question_numbers_excluded():
    result = _make_result(
        answer="January 2026 streaming was 85420 users.",
        retrieved_contexts=["85420 users in January."],
    )
    score = score_fabrication(result, question="What was streaming in January 2026?")
    # 2026 appears in both question and answer — should NOT be fabricated
    assert "2026" not in score.fabricated_numbers


def test_error_result_skipped():
    result = _make_result(error="timeout")
    score = score_fabrication(result)
    assert score.has_fabrication is False
    assert "Skipped" in score.notes[0]


def test_aggregate_fabrication():
    scores = [
        FabricationScore(
            entry_id="gq_001", numbers_in_answer=["85420"], numbers_in_context=["85420"],
            fabricated_numbers=[], fabricated_rate=0.0, has_fabrication=False,
        ),
        FabricationScore(
            entry_id="gq_002", numbers_in_answer=["999"], numbers_in_context=[],
            fabricated_numbers=["999"], fabricated_rate=1.0, has_fabrication=True,
        ),
    ]
    agg = aggregate_fabrication(scores)
    assert agg["total_entries"] == 2
    assert agg["entries_with_fabrication"] == 1
    assert agg["fabrication_incidence_rate"] == 0.5
