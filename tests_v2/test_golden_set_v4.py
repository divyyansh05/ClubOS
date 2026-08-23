from __future__ import annotations

import pytest

from eval.golden.loader import load_golden_set
from eval.golden.schema import GoldenSet, QuestionType


@pytest.fixture(scope="module")
def v4() -> GoldenSet:
    return load_golden_set("v4")


def test_v4_loads_successfully(v4):
    assert v4.version == "v4"


def test_v4_has_exactly_60_entries(v4):
    assert len(v4.entries) == 60


def test_v4_has_10_supervisor_routing(v4):
    sr = [e for e in v4.entries if e.question_type == QuestionType.SUPERVISOR_ROUTING]
    assert len(sr) == 10


def test_v4_has_10_briefer_run(v4):
    br = [e for e in v4.entries if e.question_type == QuestionType.BRIEFER_RUN]
    assert len(br) == 10


def test_v4_ids_are_unique(v4):
    ids = [e.id for e in v4.entries]
    assert len(ids) == len(set(ids))


def test_v4_ids_sequential_gq_041_to_gq_060(v4):
    new_ids = {e.id for e in v4.entries if e.id.startswith("gq_0") and int(e.id.split("_")[1]) >= 41}
    expected = {f"gq_0{n}" for n in range(41, 61)}
    assert new_ids == expected


def test_v4_preserves_all_40_v3_entries(v4):
    v3_ids = {f"gq_0{n:02d}" for n in range(1, 41)}
    actual_ids = {e.id for e in v4.entries}
    missing = v3_ids - actual_ids
    assert not missing, f"v3 entries missing from v4: {missing}"


def test_supervisor_routing_entries_have_expected_facts(v4):
    sr = [e for e in v4.entries if e.question_type == QuestionType.SUPERVISOR_ROUTING]
    for entry in sr:
        assert entry.expected_answer_facts, f"{entry.id} has no expected_answer_facts"
        # At least one fact must mention dispatch_path or classification
        has_routing_fact = any(
            "dispatch_path" in f or "classification" in f
            for f in entry.expected_answer_facts
        )
        assert has_routing_fact, f"{entry.id} has no dispatch_path or classification fact"


def test_briefer_run_entries_have_scenario_setup(v4):
    br = [e for e in v4.entries if e.question_type == QuestionType.BRIEFER_RUN]
    for entry in br:
        assert entry.scenario_setup, f"{entry.id} missing scenario_setup"
        assert entry.expected_answer_facts, f"{entry.id} has no expected_answer_facts"


def test_briefer_run_entries_have_status_fact(v4):
    br = [e for e in v4.entries if e.question_type == QuestionType.BRIEFER_RUN]
    for entry in br:
        has_status = any("status=" in f for f in entry.expected_answer_facts)
        assert has_status, f"{entry.id} has no status= fact in expected_answer_facts"


def test_new_question_types_in_schema():
    assert QuestionType.SUPERVISOR_ROUTING == "supervisor_routing"
    assert QuestionType.BRIEFER_RUN == "briefer_run"


def test_all_entries_have_required_fields(v4):
    for entry in v4.entries:
        assert entry.id
        assert entry.question
        assert entry.question_type
        assert entry.author
        assert entry.created_at
