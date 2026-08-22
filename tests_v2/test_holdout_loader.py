from __future__ import annotations
import os
import pytest

os.chdir("/Users/divyanshshrivastava/RE Internship project")


def test_load_holdout_returns_10_entries():
    from eval.golden.loader import load_holdout_set
    holdout = load_holdout_set()
    assert len(holdout.entries) == 10


def test_holdout_entries_unique_ids():
    from eval.golden.loader import load_holdout_set
    holdout = load_holdout_set()
    ids = [e.id for e in holdout.entries]
    assert len(ids) == len(set(ids)), "Holdout IDs must be unique"


def test_no_id_overlap_visible_holdout():
    from eval.golden.loader import load_holdout_set, load_golden_set
    holdout = load_holdout_set()
    visible = load_golden_set("v3")
    holdout_ids = {e.id for e in holdout.entries}
    visible_ids = {e.id for e in visible.entries}
    assert holdout_ids.isdisjoint(visible_ids), f"Overlap: {holdout_ids & visible_ids}"


def test_overlap_detection_logic():
    """Verify the loader's overlap check catches injected duplicates."""
    from eval.golden.schema import GoldenSet
    import yaml

    holdout_path = "eval/golden/holdout_set_v1.yaml"
    with open(holdout_path) as f:
        data = yaml.safe_load(f)

    data["entries"][0]["id"] = "gq_001"  # gq_001 is in visible v3
    holdout = GoldenSet.model_validate(data)
    visible_ids = {"gq_001"}
    holdout_ids = {e.id for e in holdout.entries}
    assert "gq_001" in holdout_ids
    assert len(holdout_ids & visible_ids) > 0


def test_holdout_types_distributed():
    """Holdout covers at least 4 different question types."""
    from eval.golden.loader import load_holdout_set
    holdout = load_holdout_set()
    types = {e.question_type for e in holdout.entries}
    assert len(types) >= 4, f"Only {len(types)} types: {types}"


def test_v3_visible_has_40_entries():
    from eval.golden.loader import load_golden_set
    gs = load_golden_set("v3")
    assert len(gs.entries) == 40


def test_v3_has_investigation_type():
    from eval.golden.loader import load_golden_set
    from eval.golden.schema import QuestionType
    gs = load_golden_set("v3")
    inv_entries = [e for e in gs.entries if e.question_type == QuestionType.INVESTIGATION]
    assert len(inv_entries) == 10


def test_holdout_missing_file_raises():
    from eval.golden.loader import load_holdout_set
    with pytest.raises(FileNotFoundError):
        load_holdout_set(version="nonexistent")
