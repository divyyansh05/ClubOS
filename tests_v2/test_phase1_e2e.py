from __future__ import annotations

import os
import re

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_E2E") != "1",
    reason="E2E tests require RUN_E2E=1 and real API keys",
)


@pytest.mark.asyncio
async def test_scout_answers_seasonal_question():
    """Real LLM + real ChromaDB + real semantic layer + real Gold CSVs."""
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput

    answer = await run_scout(
        ScoutInput(
            question=(
                "What does the seasonal Z-score correct for, " "and which metric is most affected?"
            )
        )
    )

    assert answer.answer is not None
    assert len(answer.answer) > 50

    sources = {c.source for c in answer.citations}
    assert any(
        "priority_board" in s or "signal_engine" in s for s in sources
    ), f"Expected skill-file citation, got {sources}"

    assert "net_sales" in answer.answer.lower() or "january" in answer.answer.lower()
    assert answer.confidence in ("high", "medium")


@pytest.mark.asyncio
async def test_scout_refuses_unanswerable_question():
    """No fabrication discipline check."""
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput

    answer = await run_scout(
        ScoutInput(question="Who is the highest-paid player on Real Madrid this season?")
    )

    assert answer.confidence == "low"
    # No specific monetary numbers fabricated
    assert not re.search(r"€\d|\$\d|\d+\s*million", answer.answer)


@pytest.mark.asyncio
async def test_scout_handles_ambiguity():
    """Disambiguation rule fires."""
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput

    answer = await run_scout(ScoutInput(question="how is conversion rate doing this month?"))

    assert len(answer.assumptions_made) > 0
    assumption_text = " ".join(answer.assumptions_made).lower()
    assert "ecommerce" in assumption_text or "streaming" in assumption_text


@pytest.mark.asyncio
async def test_v1_endpoints_still_work():
    """Regression: v1 endpoints still function after v2 addition."""
    import sys

    from fastapi.testclient import TestClient

    sys.path.insert(0, "BACKEND/api")
    from app.main import app

    client = TestClient(app)

    # Hit a known v1 endpoint
    response = client.get("/priorities")
    assert response.status_code == 200
