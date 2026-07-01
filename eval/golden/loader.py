from __future__ import annotations

import yaml
from pathlib import Path

from eval.golden.schema import GoldenEntry, GoldenSet


def load_golden_set(version: str = "v1") -> GoldenSet:
    """Load and validate a golden set YAML file."""
    path = Path(f"eval/golden/golden_set_{version}.yaml")
    if not path.exists():
        raise FileNotFoundError(f"Golden set not found: {path}")
    with path.open() as f:
        data = yaml.safe_load(f)
    return GoldenSet.model_validate(data)


def load_holdout_set(version: str = "v1") -> GoldenSet:
    """Load the holdout set. NEVER used during normal prompt iteration.

    A check ensures holdout IDs don't overlap with visible set IDs.
    """
    holdout_path = Path(f"eval/golden/holdout_set_{version}.yaml")
    if not holdout_path.exists():
        raise FileNotFoundError(f"Holdout set not found: {holdout_path}")

    with holdout_path.open() as f:
        data = yaml.safe_load(f)
    holdout = GoldenSet.model_validate(data)

    # Sanity check: no ID overlap
    visible = load_golden_set("v3")
    visible_ids = {e.id for e in visible.entries}
    holdout_ids = {e.id for e in holdout.entries}
    overlap = visible_ids & holdout_ids
    if overlap:
        raise ValueError(f"Holdout IDs overlap with visible set: {overlap}")

    return holdout


def get_entries_by_type(version: str, question_type: str) -> list[GoldenEntry]:
    gs = load_golden_set(version)
    from eval.golden.schema import QuestionType
    return gs.by_type(QuestionType(question_type))
