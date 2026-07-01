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


def get_entries_by_type(version: str, question_type: str) -> list[GoldenEntry]:
    gs = load_golden_set(version)
    from eval.golden.schema import QuestionType
    return gs.by_type(QuestionType(question_type))
