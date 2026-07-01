from __future__ import annotations

import re

from pydantic import BaseModel

from clubos2.eval.runner import EvalRun, RunResult


class FabricationScore(BaseModel):
    entry_id: str
    numbers_in_answer: list[str]
    numbers_in_context: list[str]
    fabricated_numbers: list[str]
    fabricated_rate: float
    has_fabrication: bool
    notes: list[str] = []


def extract_numbers(text: str) -> list[str]:
    """
    Extract every number-like token from text. Normalises to canonical strings
    so '1,234.5', '1234.5', and '1,234.50' are treated as equivalent.

    Handles: integers, decimals, percentages, currency, multipliers, ordinals (4th→4).
    """
    # Strip ordinal suffixes so "4th" → "4", "1st" → "1"
    text = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', text)

    # Remove ISO date separators and month-year hyphens BEFORE extracting numbers.
    # "December-2025" or "2025-12-01" would produce "-2025", "-12", "-01" as false negatives.
    # Strategy: strip any hyphen immediately before a 2-4 digit number in date contexts.
    text = re.sub(r'\b(19|20)\d{2}-\d{2}(-\d{2})?\b', ' ', text)  # YYYY-MM-DD, YYYY-MM
    text = re.sub(r'(?<=\w)-(?=(19|20)\d{2}\b)', ' ', text)  # word-YYYY → word YYYY

    # Apply patterns in priority order: longest/most-specific first.
    # Track matched spans so shorter fallback patterns don't re-match fragments
    # that are already part of a comma-grouped or decimal number.
    patterns = [
        r'-?\d{1,3}(?:,\d{3})+(?:\.\d+)?',  # 12,345 or 12,345.67
        r'-?\d+\.\d+',                         # 1.5
        r'-?\d+',                               # 42
    ]

    covered: list[tuple[int, int]] = []  # (start, end) of already-matched spans
    raw_matches: list[str] = []

    for p in patterns:
        for m in re.finditer(p, text):
            start, end = m.start(), m.end()
            # Skip if this span overlaps any already-covered span
            if any(start < ce and end > cs for cs, ce in covered):
                continue
            covered.append((start, end))
            raw_matches.append(m.group())

    # Normalise: remove commas, strip trailing zeros after decimal
    normalised: set[str] = set()
    for m in raw_matches:
        clean = m.replace(',', '')
        try:
            val = float(clean)
            normalised.add(str(int(val)) if val == int(val) else f'{val:g}')
        except ValueError:
            continue
    return sorted(normalised)


def score_fabrication(result: RunResult, question: str = "") -> FabricationScore:
    """
    Compare numbers in scout_answer.answer against numbers in retrieved_contexts
    and citation quotes. Numbers that appear in the question are excluded.

    A number in the answer is 'fabricated' if it does NOT appear in any retrieved context.
    """
    if result.error or result.scout_answer is None:
        return FabricationScore(
            entry_id=result.entry_id,
            numbers_in_answer=[],
            numbers_in_context=[],
            fabricated_numbers=[],
            fabricated_rate=0.0,
            has_fabrication=False,
            notes=["Skipped: result has error"],
        )

    answer_text = result.scout_answer.answer

    # Build context corpus: retrieved chunks + citation quotes
    context_texts: list[str] = list(result.scout_answer.retrieved_contexts)
    context_texts += [c.quote for c in result.scout_answer.citations if c.quote]

    answer_numbers = set(extract_numbers(answer_text))
    question_numbers = set(extract_numbers(question)) if question else set()

    context_numbers: set[str] = set()
    for ctx in context_texts:
        context_numbers.update(extract_numbers(ctx))

    # Exclude numbers that appear in the question (not fabrication to repeat them)
    raw_fabricated = answer_numbers - context_numbers - question_numbers

    # Remove false positives from rounding: if a fabricated number is within
    # 1% of any context number, it's a rounded representation, not fabrication.
    def _within_tolerance(a: str, b: str, pct: float = 0.01) -> bool:
        try:
            fa, fb = float(a), float(b)
            if fa == 0 and fb == 0:
                return True
            if fa == 0 or fb == 0:
                return abs(fa - fb) < 1.0
            return abs(fa - fb) / max(abs(fa), abs(fb)) <= pct
        except ValueError:
            return False

    confirmed_fabricated = set()
    for fn in raw_fabricated:
        # 4-digit years (1900-2099) are temporal references, never fabricated data
        if re.match(r'^(19|20)\d{2}$', fn):
            continue
        if not any(_within_tolerance(fn, cn) for cn in context_numbers):
            confirmed_fabricated.add(fn)
    fabricated = confirmed_fabricated

    fab_rate = len(fabricated) / max(len(answer_numbers), 1)

    return FabricationScore(
        entry_id=result.entry_id,
        numbers_in_answer=sorted(answer_numbers),
        numbers_in_context=sorted(context_numbers),
        fabricated_numbers=sorted(fabricated),
        fabricated_rate=fab_rate,
        has_fabrication=len(fabricated) > 0,
    )


def score_fabrication_batch(eval_run: EvalRun) -> list[FabricationScore]:
    """Score all results in an EvalRun. question is empty — question_numbers not excluded."""
    return [
        score_fabrication(r, question=r.question)
        for r in eval_run.results
    ]


def aggregate_fabrication(scores: list[FabricationScore]) -> dict:
    """Summary stats across all fabrication scores."""
    total = len(scores)
    with_fab = sum(1 for s in scores if s.has_fabrication)
    return {
        "total_entries": total,
        "entries_with_fabrication": with_fab,
        "fabrication_incidence_rate": with_fab / max(total, 1),
        "average_fab_rate_per_entry": sum(s.fabricated_rate for s in scores) / max(total, 1),
        "fabricated_numbers_total": sum(len(s.fabricated_numbers) for s in scores),
    }
