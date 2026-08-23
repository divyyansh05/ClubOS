from __future__ import annotations

import logging

from pydantic import BaseModel

from clubos2.agents.scout_schemas import Confidence, ScoutAnswer
from clubos2.eval.fabrication_scorer import extract_numbers
from clubos2.observability.tracing import traced

logger = logging.getLogger("clubos.guardrails.no_fabricated_numbers")


class GuardrailViolation(BaseModel):
    rule: str = "no_fabricated_numbers"
    severity: str  # "block" | "warn"
    fabricated_numbers: list[str]
    repair_action: str  # "removed_numbers" | "lowered_confidence" | "blocked"


class GuardedScoutAnswer(BaseModel):
    answer: ScoutAnswer
    violations: list[GuardrailViolation]
    was_modified: bool


@traced(name="guardrail:no_fabricated_numbers", run_type="chain")
async def check_no_fabricated_numbers(
    scout_answer: ScoutAnswer,
    question: str,
    mode: str = "warn",  # "warn" (Phase 2) or "block" (Phase 3+)
) -> GuardedScoutAnswer:
    """
    Extract numbers from the answer. Compare against retrieved_contexts and citation quotes.
    Fabricated numbers (in answer but not in context) trigger a violation.

    Behaviour by mode:
    - 'warn': log the violation, lower confidence to LOW, append to assumptions_made
    - 'block': replace the answer with a refusal message

    Phase 2 default: 'warn'. Flip to 'block' once a week of evals shows zero violations.
    """
    answer_text = scout_answer.answer
    question_numbers = set(extract_numbers(question))

    context_texts: list[str] = list(scout_answer.retrieved_contexts)
    context_texts += [c.quote for c in scout_answer.citations if c.quote]

    answer_numbers = set(extract_numbers(answer_text))
    context_numbers: set[str] = set()
    for ctx in context_texts:
        context_numbers.update(extract_numbers(ctx))

    import re as _re

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

    raw_fabricated = answer_numbers - context_numbers - question_numbers
    fabricated_set: set[str] = set()
    for fn in raw_fabricated:
        if _re.match(r'^(19|20)\d{2}$', fn):  # 4-digit years are temporal refs, not data
            continue
        if not any(_within_tolerance(fn, cn) for cn in context_numbers):
            fabricated_set.add(fn)
    fabricated = sorted(fabricated_set)

    if not fabricated:
        return GuardedScoutAnswer(
            answer=scout_answer,
            violations=[],
            was_modified=False,
        )

    violation = GuardrailViolation(
        severity=mode,
        fabricated_numbers=fabricated,
        repair_action="blocked" if mode == "block" else "lowered_confidence",
    )

    logger.warning(
        "Guardrail triggered: fabricated numbers detected",
        extra={"fabricated": fabricated, "mode": mode, "entry_question": question[:100]},
    )

    if mode == "block":
        # Replace answer with a refusal
        blocked_answer = scout_answer.model_copy(update={
            "answer": (
                "I detected numbers in my draft answer that I cannot verify against "
                "retrieved sources. Refusing to return potentially fabricated data."
            ),
            "confidence": Confidence.LOW,
            "citations": [],
            "retrieved_contexts": [],
        })
        return GuardedScoutAnswer(
            answer=blocked_answer,
            violations=[violation],
            was_modified=True,
        )
    else:
        # warn mode: lower confidence + add note to assumptions_made
        note = (
            f"Guardrail flagged numbers without traceable source: {fabricated}. "
            "Confidence lowered."
        )
        warned_answer = scout_answer.model_copy(update={
            "confidence": Confidence.LOW,
            "assumptions_made": list(scout_answer.assumptions_made) + [note],
        })
        return GuardedScoutAnswer(
            answer=warned_answer,
            violations=[violation],
            was_modified=True,
        )
