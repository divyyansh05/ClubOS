from __future__ import annotations
import pytest
from eval.golden.loader import load_golden_set
from eval.golden.schema import QuestionType


def test_load_v2_returns_30_entries():
    gs = load_golden_set("v2")
    assert len(gs.entries) == 30


def test_v2_contains_v1_entries():
    """v1 entries must be unchanged in v2."""
    gs_v1 = load_golden_set("v1")
    gs_v2 = load_golden_set("v2")
    v1_ids = {e.id for e in gs_v1.entries}
    v2_ids = {e.id for e in gs_v2.entries}
    assert v1_ids.issubset(v2_ids), "All v1 entries must be in v2"


def test_v2_has_watchdog_run_entries():
    gs = load_golden_set("v2")
    watchdog_entries = [e for e in gs.entries if e.question_type == QuestionType.WATCHDOG_RUN]
    assert len(watchdog_entries) == 5


def test_v2_watchdog_entries_have_scenario_setup():
    gs = load_golden_set("v2")
    for e in gs.entries:
        if e.question_type == QuestionType.WATCHDOG_RUN:
            assert e.scenario_setup is not None, f"{e.id} missing scenario_setup"


def test_v2_new_entries_have_author():
    gs = load_golden_set("v2")
    new_entries = [e for e in gs.entries if e.id in {f"gq_0{i:02d}" for i in range(21, 31)}]
    for e in new_entries:
        assert e.author is not None
        assert e.created_at is not None


def test_question_type_enum_has_watchdog_run():
    assert QuestionType.WATCHDOG_RUN == "watchdog_run"
