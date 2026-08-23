from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from clubos2.agents.scout_schemas import Confidence, ScoutAnswer
from clubos2.eval.runner import EvalRun, RunResult, run_eval


def _make_mock_answer() -> ScoutAnswer:
    return ScoutAnswer(
        answer="Mock answer for testing.",
        citations=[],
        confidence=Confidence.HIGH,
        assumptions_made=[],
        metrics_queried=[],
        chunks_retrieved=0,
    )


@pytest.mark.asyncio
async def test_run_eval_returns_20_results(tmp_path):
    mock_answer = _make_mock_answer()
    save_path = str(tmp_path / "test_run.json")

    with patch("clubos2.eval.runner.run_scout", new_callable=AsyncMock) as mock_scout:
        mock_scout.return_value = mock_answer
        result = await run_eval(golden_set_version="v1", save_to=save_path)

    assert isinstance(result, EvalRun)
    assert len(result.results) == 20


@pytest.mark.asyncio
async def test_run_eval_captures_errors_per_entry(tmp_path):
    save_path = str(tmp_path / "test_run_err.json")
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Simulated Scout failure")
        return _make_mock_answer()

    with patch("clubos2.eval.runner.run_scout", side_effect=side_effect):
        result = await run_eval(golden_set_version="v1", save_to=save_path)

    assert result.total_errors == 1
    assert len(result.results) == 20
    failed = [r for r in result.results if r.error is not None]
    assert len(failed) == 1
    assert failed[0].scout_answer is None


@pytest.mark.asyncio
async def test_run_eval_saves_json(tmp_path):
    save_path = str(tmp_path / "saved_run.json")
    mock_answer = _make_mock_answer()

    with patch("clubos2.eval.runner.run_scout", new_callable=AsyncMock) as mock_scout:
        mock_scout.return_value = mock_answer
        result = await run_eval(golden_set_version="v1", save_to=save_path)

    assert Path(save_path).exists()
    loaded = EvalRun.model_validate_json(Path(save_path).read_text())
    assert loaded.run_id == result.run_id
    assert len(loaded.results) == 20
