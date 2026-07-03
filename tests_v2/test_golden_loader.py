from __future__ import annotations

import pytest
from eval.golden.loader import load_golden_set
from eval.golden.schema import QuestionType


def test_golden_set_has_20_entries():
    gs = load_golden_set("v1")
    assert len(gs.entries) == 20


def test_question_type_distribution():
    gs = load_golden_set("v1")
    assert len(gs.by_type(QuestionType.QUANTITATIVE)) == 6
    assert len(gs.by_type(QuestionType.NARRATIVE)) == 5
    assert len(gs.by_type(QuestionType.MIXED)) == 4
    assert len(gs.by_type(QuestionType.AMBIGUOUS)) == 3
    assert len(gs.by_type(QuestionType.UNANSWERABLE)) == 2


def test_all_ids_unique():
    gs = load_golden_set("v1")
    ids = [e.id for e in gs.entries]
    assert len(set(ids)) == len(ids)


def test_citation_sources_format():
    VALID = ("gold.", "skills.", "metric_registry", "watchdog_alerts", "investigations", "web_search:")
    gs = load_golden_set("v1")
    for entry in gs.entries:
        for src in entry.required_citation_sources:
            assert any(src.startswith(p) for p in VALID), (
                f"Non-canonical source in {entry.id}: {src!r}"
            )


def test_unanswerable_entries_must_refuse():
    gs = load_golden_set("v1")
    for entry in gs.by_type(QuestionType.UNANSWERABLE):
        assert entry.must_refuse is True
        assert entry.tempts_fabrication is True
        assert entry.expected_answer_facts == []
