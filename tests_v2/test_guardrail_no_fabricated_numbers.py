from __future__ import annotations

import pytest
from unittest.mock import patch

from clubos2.agents.scout_schemas import Citation, Confidence, ScoutAnswer
from clubos2.guardrails.no_fabricated_numbers import (
    GuardedScoutAnswer,
    check_no_fabricated_numbers,
)


def _make_answer(
    answer: str,
    retrieved_contexts: list[str] | None = None,
    citation_quotes: list[str] | None = None,
    confidence: Confidence = Confidence.HIGH,
    assumptions_made: list[str] | None = None,
) -> ScoutAnswer:
    citations = [
        Citation(claim="c", source="s", quote=q)
        for q in (citation_quotes or [])
    ]
    return ScoutAnswer(
        answer=answer,
        citations=citations,
        confidence=confidence,
        retrieved_contexts=retrieved_contexts or [],
        assumptions_made=assumptions_made or [],
    )


@pytest.mark.asyncio
async def test_clean_answer_no_violation():
    answer = _make_answer(
        answer="Streaming users were 85420 in November.",
        retrieved_contexts=["Daily users reached 85420 in November 2025."],
    )
    result = await check_no_fabricated_numbers(answer, question="streaming users?")
    assert result.violations == []
    assert result.was_modified is False


@pytest.mark.asyncio
async def test_fabricated_number_warn_mode():
    answer = _make_answer(
        answer="Revenue was €999999 this quarter.",
        retrieved_contexts=["No specific revenue figure is available."],
    )
    result = await check_no_fabricated_numbers(answer, question="revenue?", mode="warn")
    assert len(result.violations) == 1
    assert result.was_modified is True
    assert result.answer.confidence == Confidence.LOW
    assert any("Guardrail" in a for a in result.answer.assumptions_made)


@pytest.mark.asyncio
async def test_fabricated_number_block_mode():
    answer = _make_answer(
        answer="Revenue was €999999 this quarter.",
        retrieved_contexts=["No specific revenue figure is available."],
    )
    result = await check_no_fabricated_numbers(answer, question="revenue?", mode="block")
    assert len(result.violations) == 1
    assert result.was_modified is True
    assert "Refusing" in result.answer.answer
    assert result.answer.citations == []


@pytest.mark.asyncio
async def test_question_numbers_not_flagged():
    answer = _make_answer(
        answer="In January 2026, streaming had 85420 users.",
        retrieved_contexts=["85420 users streaming in January."],
    )
    result = await check_no_fabricated_numbers(
        answer,
        question="What was streaming in January 2026?",
        mode="warn",
    )
    # 2026 is in question — should not trigger even if not in context explicitly
    assert result.violations == [] or "2026" not in result.violations[0].fabricated_numbers
