from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from clubos2.agents.scout import run_scout
from clubos2.agents.scout_schemas import ScoutAnswer, ScoutInput
from eval.golden.loader import load_golden_set
from eval.golden.schema import GoldenEntry, GoldenSet

logger = logging.getLogger("clubos.eval.runner")


class RunResult(BaseModel):
    entry_id: str
    question: str
    question_type: str
    scout_answer: ScoutAnswer | None  # None if Scout threw an error
    latency_ms: int
    trace_url: str | None = None
    error: str | None = None


class EvalRun(BaseModel):
    run_id: str
    golden_set_version: str
    scout_prompt_version: str
    timestamp: str
    results: list[RunResult]
    total_latency_seconds: float
    total_errors: int


def get_current_langsmith_trace_url() -> str | None:
    """Get LangSmith trace URL for the current run context."""
    try:
        from langsmith import get_current_run_tree
        run_tree = get_current_run_tree()
        if run_tree is not None:
            return f"https://smith.langchain.com/public/{run_tree.id}/r"
    except Exception:
        pass
    return None


async def run_eval(
    golden_set_version: str = "v1",
    scout_prompt_version: str = "v1",
    parallel: int = 3,
    save_to: str | None = None,
) -> EvalRun:
    gs = load_golden_set(golden_set_version)
    run_id = f"eval_{datetime.utcnow().isoformat().replace(':', '-')}"
    semaphore = asyncio.Semaphore(parallel)

    async def run_one(entry: GoldenEntry) -> RunResult:
        async with semaphore:
            start = time.perf_counter()
            try:
                answer = await run_scout(ScoutInput(question=entry.question))
                latency_ms = int((time.perf_counter() - start) * 1000)
                return RunResult(
                    entry_id=entry.id,
                    question=entry.question,
                    question_type=entry.question_type.value,
                    scout_answer=answer,
                    latency_ms=latency_ms,
                    trace_url=get_current_langsmith_trace_url(),
                )
            except Exception as e:
                latency_ms = int((time.perf_counter() - start) * 1000)
                logger.exception(f"Eval entry {entry.id} failed: {e}")
                return RunResult(
                    entry_id=entry.id,
                    question=entry.question,
                    question_type=entry.question_type.value,
                    scout_answer=None,
                    latency_ms=latency_ms,
                    trace_url=None,
                    error=str(e),
                )

    results = list(await asyncio.gather(*[run_one(e) for e in gs.entries]))

    eval_run = EvalRun(
        run_id=run_id,
        golden_set_version=golden_set_version,
        scout_prompt_version=scout_prompt_version,
        timestamp=datetime.utcnow().isoformat(),
        results=results,
        total_latency_seconds=sum(r.latency_ms for r in results) / 1000.0,
        total_errors=sum(1 for r in results if r.error),
    )

    if save_to is None:
        save_to = f"eval/runs/{run_id}.json"
    out = Path(save_to)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(eval_run.model_dump_json(indent=2))
    logger.info(f"Eval run saved to {out}")

    return eval_run


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run ClubOS 2.0 eval against golden set")
    parser.add_argument("--golden", default="v1")
    parser.add_argument("--prompt-version", default="v1")
    parser.add_argument("--parallel", type=int, default=3)
    args = parser.parse_args()

    result = asyncio.run(
        run_eval(
            golden_set_version=args.golden,
            scout_prompt_version=args.prompt_version,
            parallel=args.parallel,
        )
    )
    print(f"Run complete: {result.run_id}")
    print(f"Total: {len(result.results)} entries, {result.total_errors} errors")
    print(f"Total latency: {result.total_latency_seconds:.1f}s")
