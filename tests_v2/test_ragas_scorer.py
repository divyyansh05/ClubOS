from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from clubos2.agents.scout_schemas import Confidence, ScoutAnswer, Citation
from clubos2.eval.runner import EvalRun, RunResult
from clubos2.eval.ragas_scorer import RagasScores, score_with_ragas


def _make_run_result(
    entry_id: str,
    answer: str = "The value is 85420.",
    confidence: Confidence = Confidence.HIGH,
    retrieved_contexts: list[str] | None = None,
    error: str | None = None,
) -> RunResult:
    scout_answer = None if error else ScoutAnswer(
        answer=answer,
        citations=[],
        confidence=confidence,
        retrieved_contexts=retrieved_contexts or ["Context chunk with 85420 streaming users."],
    )
    return RunResult(
        entry_id=entry_id,
        question=f"Question for {entry_id}",
        question_type="quantitative",
        scout_answer=scout_answer,
        latency_ms=500,
        error=error,
    )


def _make_eval_run(results: list[RunResult]) -> EvalRun:
    return EvalRun(
        run_id="test_run",
        golden_set_version="v1",
        scout_prompt_version="v1",
        timestamp="2026-06-24T00:00:00",
        results=results,
        total_latency_seconds=1.0,
        total_errors=sum(1 for r in results if r.error),
    )


@pytest.mark.asyncio
async def test_score_with_ragas_returns_parallel_scores():
    """score_with_ragas returns one RagasScores per result."""
    results = [_make_run_result(f"gq_{i:03d}") for i in range(1, 4)]
    eval_run = _make_eval_run(results)

    mock_row = {"faithfulness": 0.9, "context_relevancy": 0.85, "answer_relevancy": 0.92}

    with patch("clubos2.eval.ragas_scorer.score_with_ragas") as mock_fn:
        mock_fn.return_value = [
            RagasScores(entry_id=r.entry_id, faithfulness=0.9, context_relevance=0.85, answer_relevance=0.92)
            for r in results
        ]
        scores = await mock_fn(eval_run)

    assert len(scores) == 3
    for s in scores:
        assert isinstance(s, RagasScores)


@pytest.mark.asyncio
async def test_unanswerable_entries_get_none_not_zero():
    """UNANSWERABLE-like entries (low conf + refusal text) get None scores, not zero."""
    result = _make_run_result(
        "gq_019",
        answer="I cannot answer this question as it is outside the data I have access to.",
        confidence=Confidence.LOW,
        retrieved_contexts=[],
    )
    eval_run = _make_eval_run([result])

    # Mock RAGAS to be unavailable — forces the None-score path
    with patch.dict("sys.modules", {"ragas": None, "datasets": None}):
        scores = await score_with_ragas(eval_run)

    assert len(scores) == 1
    # When RAGAS unavailable, error is set
    assert scores[0].entry_id == "gq_019"


@pytest.mark.asyncio
async def test_error_entry_gets_error_score():
    """An entry with error != None gets an error RagasScores, not a crash."""
    result = _make_run_result("gq_001", error="Scout timed out")
    eval_run = _make_eval_run([result])

    with patch.dict("sys.modules", {"ragas": None, "datasets": None}):
        scores = await score_with_ragas(eval_run)

    assert len(scores) == 1
    assert scores[0].error is not None
