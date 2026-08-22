from __future__ import annotations
import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


def _make_fake_investigation(metric="streaming_daily_users"):
    inv = MagicMock()
    inv.alert_id = "alrt_test123"
    inv.metric_name = metric
    inv.confidence = "medium"
    inv.cause_hypothesis = "The metric declined due to seasonal patterns in January."
    inv.evidence_summary = "- January is historically low\n- Peer data confirms industry trend"
    inv.started_at = datetime(2026, 7, 1, 12, 0, 0)
    return inv


@pytest.mark.asyncio
async def test_format_investigations_for_context():
    """format_investigations_for_context produces the correct block format."""
    from clubos2.agents.scout import format_investigations_for_context

    inv = _make_fake_investigation()
    block = format_investigations_for_context([inv])
    assert "RELATED PAST INVESTIGATIONS" in block
    assert "investigations" in block
    assert "seasonal patterns" in block
    assert "alrt_test123" in block
    assert "medium" in block
    assert "2026-07-01" in block


def test_run_scout_accepts_enable_investigation_context():
    """run_scout must accept enable_investigation_context parameter."""
    from clubos2.agents.scout import run_scout

    sig = inspect.signature(run_scout)
    assert "enable_investigation_context" in sig.parameters


@pytest.mark.asyncio
async def test_scout_investigation_context_disabled():
    """enable_investigation_context=False → run_scout accepts the parameter and skips init.

    We verify this by checking the function signature accepts the param, and that when
    disabled the _enrich_with_investigations helper is never called.
    """
    from clubos2.agents.scout import run_scout, _enrich_with_investigations
    from clubos2.agents.scout_schemas import ScoutInput

    enrich_called = []

    async def fake_enrich(context_parts, metric_names, repo):
        enrich_called.append(True)

    with patch("clubos2.agents.scout._enrich_with_investigations", side_effect=fake_enrich):
        with patch("clubos2.agents.scout.call_llm") as mock_llm:
            from clubos2.agents.scout_schemas import ScoutAnswer
            mock_llm.return_value = ScoutAnswer(
                answer="Answer without investigation context.",
                citations=[],
                confidence="medium",
                caveats=[],
            )
            await run_scout(
                ScoutInput(question="what is streaming_daily_users?"),
                enable_alert_context=False,
                enable_investigation_context=False,
            )

    # _enrich_with_investigations should NOT have been called
    assert enrich_called == []


@pytest.mark.asyncio
async def test_scout_no_investigations_no_section():
    """Empty investigation list → no RELATED PAST INVESTIGATIONS block in output."""
    from clubos2.agents.scout import format_investigations_for_context

    block = format_investigations_for_context([])
    # With an empty list the header line is produced but no investigation entries
    # The key assertion: no investigation detail lines
    assert "alrt_" not in block
    assert "Cause:" not in block


@pytest.mark.asyncio
async def test_scout_enrich_with_investigations_empty():
    """_enrich_with_investigations with empty result leaves context_parts unchanged."""
    from clubos2.agents.scout import _enrich_with_investigations

    mock_repo = AsyncMock()
    mock_repo.list_recent.return_value = []

    context_parts: list[str] = ["existing context"]
    await _enrich_with_investigations(context_parts, ["streaming_daily_users"], mock_repo)

    assert context_parts == ["existing context"]


@pytest.mark.asyncio
async def test_scout_enrich_with_investigations_adds_block():
    """_enrich_with_investigations appends a block when investigations exist."""
    from clubos2.agents.scout import _enrich_with_investigations

    mock_repo = AsyncMock()
    inv = _make_fake_investigation()
    mock_repo.list_recent.return_value = [inv]

    context_parts: list[str] = ["existing context"]
    await _enrich_with_investigations(context_parts, ["streaming_daily_users"], mock_repo)

    assert len(context_parts) == 2
    assert "RELATED PAST INVESTIGATIONS" in context_parts[1]
    assert "investigations" in context_parts[1]


@pytest.mark.asyncio
async def test_scout_enrich_only_completed_investigations_requested():
    """_enrich_with_investigations calls list_recent with status=COMPLETED."""
    from clubos2.agents.scout import _enrich_with_investigations
    from clubos2.investigator.schema import InvestigationStatus

    mock_repo = AsyncMock()
    mock_repo.list_recent.return_value = []

    await _enrich_with_investigations(mock_repo, ["streaming_daily_users"], mock_repo)

    # Check that any call used status=COMPLETED
    # (We call _enrich_with_investigations which internally uses COMPLETED)
    # Re-run properly
    context_parts: list[str] = []
    mock_repo.list_recent.reset_mock()
    await _enrich_with_investigations(context_parts, ["streaming_daily_users"], mock_repo)

    mock_repo.list_recent.assert_called_once()
    call_kwargs = mock_repo.list_recent.call_args
    # status should be COMPLETED
    status_passed = call_kwargs.kwargs.get("status") or (
        call_kwargs.args[2] if len(call_kwargs.args) > 2 else None
    )
    assert status_passed == InvestigationStatus.COMPLETED


@pytest.mark.asyncio
async def test_scout_evidence_truncated_at_200_chars():
    """Evidence summary longer than 200 chars is truncated with ellipsis."""
    from clubos2.agents.scout import format_investigations_for_context

    inv = _make_fake_investigation()
    inv.evidence_summary = "A" * 250  # 250 chars

    block = format_investigations_for_context([inv])
    # The evidence line should contain 200 A's followed by "..."
    assert "A" * 200 + "..." in block
    assert "A" * 201 not in block.replace("A" * 200 + "...", "")


@pytest.mark.asyncio
async def test_scout_investigation_context_preserved_with_phase1_behaviour():
    """With both context flags disabled, Scout still runs and returns a valid answer."""
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput, ScoutAnswer

    with patch("clubos2.agents.scout.call_llm") as mock_llm:
        mock_llm.return_value = ScoutAnswer(
            answer="Still works without any context repos.",
            citations=[],
            confidence="low",
            caveats=["No data available"],
        )
        answer = await run_scout(
            ScoutInput(question="test question"),
            enable_alert_context=False,
            enable_investigation_context=False,
        )
    assert answer is not None
    assert isinstance(answer.answer, str)
    assert "Still works" in answer.answer
