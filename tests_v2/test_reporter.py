from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from clubos2.agents.scout_schemas import Citation, Confidence, ScoutAnswer
from clubos2.eval.behavioural_scorer import BehaviouralScore
from clubos2.eval.fabrication_scorer import FabricationScore
from clubos2.eval.ragas_scorer import RagasScores
from clubos2.eval.reporter import EvalReport, generate_report, render_markdown
from clubos2.eval.runner import EvalRun, RunResult
from eval.golden.loader import load_golden_set


def _make_run_result(entry_id: str, answer: str = "Answer text.") -> RunResult:
    return RunResult(
        entry_id=entry_id,
        question=f"Question for {entry_id}?",
        question_type="quantitative",
        scout_answer=ScoutAnswer(
            answer=answer,
            citations=[],
            confidence=Confidence.HIGH,
        ),
        latency_ms=300,
        trace_url=None,
    )


def _minimal_inputs(n: int = 3):
    """Build minimal scoring inputs for n results."""
    gs = load_golden_set("v1")
    entry_ids = [e.id for e in gs.entries[:n]]

    eval_run = EvalRun(
        run_id="test_run_001",
        golden_set_version="v1",
        scout_prompt_version="v1",
        timestamp="2026-06-24T12:00:00",
        results=[_make_run_result(eid) for eid in entry_ids],
        total_latency_seconds=1.5,
        total_errors=0,
    )
    ragas = [RagasScores(entry_id=eid, faithfulness=0.9, context_relevance=0.85, answer_relevance=0.88) for eid in entry_ids]
    fabrication = [
        FabricationScore(
            entry_id=eid,
            numbers_in_answer=[],
            numbers_in_context=[],
            fabricated_numbers=[],
            fabricated_rate=0.0,
            has_fabrication=False,
        )
        for eid in entry_ids
    ]
    behavioural = [
        BehaviouralScore(
            entry_id=eid,
            expected_to_refuse=False,
            did_refuse=False,
            refusal_correct=True,
            expected_to_state_assumption=False,
            did_state_assumption=False,
            assumption_correct=True,
            expected_citation_sources=[],
            actual_citation_sources=[],
            citation_coverage=1.0,
            citation_correct=True,
            expected_metric_names=[],
            actual_metrics_queried=[],
            metric_query_correct=True,
            overall_pass=True,
            failures=[],
        )
        for eid in entry_ids
    ]
    return eval_run, ragas, fabrication, behavioural, gs


def test_generate_report_produces_valid_model():
    eval_run, ragas, fabrication, behavioural, gs = _minimal_inputs(3)
    report = generate_report(eval_run, ragas, fabrication, behavioural, gs)
    assert isinstance(report, EvalReport)
    assert report.run_id == "test_run_001"
    assert report.total_questions == 3
    assert len(report.per_entry) == 3


def test_render_markdown_produces_file():
    eval_run, ragas, fabrication, behavioural, gs = _minimal_inputs(3)
    report = generate_report(eval_run, ragas, fabrication, behavioural, gs)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.md"
        render_markdown(report, output_path)
        assert output_path.exists()
        content = output_path.read_text()
        assert "# ClubOS 2.0 — Eval Report" in content
        assert "## Headline metrics" in content
        assert "## Per-question breakdown" in content
        assert "## Failure summary" in content
        assert "## Recommendations" in content


def test_report_headline_metrics_table_present():
    eval_run, ragas, fabrication, behavioural, gs = _minimal_inputs(3)
    report = generate_report(eval_run, ragas, fabrication, behavioural, gs)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.md"
        render_markdown(report, output_path)
        content = output_path.read_text()
        assert "Fabrication incidence" in content
        assert "Behavioural pass rate" in content
        assert "RAGAS faithfulness" in content
