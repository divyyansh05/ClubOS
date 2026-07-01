from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from clubos2.eval.runner import EvalRun, RunResult

logger = logging.getLogger("clubos.eval.ragas_scorer")


class RagasScores(BaseModel):
    entry_id: str
    faithfulness: float | None = None
    context_relevance: float | None = None
    answer_relevance: float | None = None
    error: str | None = None


async def score_with_ragas(eval_run: EvalRun) -> list[RagasScores]:
    """Score every result using RAGAS LLM-as-judge. UNANSWERABLE entries get None scores."""
    try:
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, faithfulness, context_utilization
        from datasets import Dataset
        from langchain_openai import ChatOpenAI
        from ragas.llms import LangchainLLMWrapper
    except ImportError as e:
        logger.warning(f"RAGAS/dependencies not available: {e}. Returning None scores.")
        return [
            RagasScores(entry_id=r.entry_id, error=f"RAGAS not available: {e}")
            for r in eval_run.results
        ]

    # Using gpt-4o-mini as RAGAS judge — cheap, accurate enough for eval scoring.
    # RAGAS and langchain read OPENAI_API_KEY from os.environ directly, so we set it here
    # from GatewaySettings (.env.v2) to ensure it's available without manual export.
    import os as _os
    from clubos2.gateway.client import GatewaySettings as _GS
    _openai_key = _GS().openai_api_key or _os.environ.get("OPENAI_API_KEY", "")
    if _openai_key:
        _os.environ["OPENAI_API_KEY"] = _openai_key
    ragas_llm = LangchainLLMWrapper(
        ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=_openai_key)
    )

    scores: list[RagasScores] = []

    for result in eval_run.results:
        # RAGAS faithfulness is meaningless for UNANSWERABLE entries — the correct answer
        # is a refusal, which RAGAS interprets as "answer doesn't address the question"
        # (low answer_relevance). For UNANSWERABLE entries, we score via the fabricated-number
        # rate (fabrication_scorer) and the must_refuse check (behavioural_scorer), not RAGAS.
        if result.scout_answer is None or result.error:
            scores.append(RagasScores(entry_id=result.entry_id, error=result.error or "No answer"))
            continue

        # Detect UNANSWERABLE by checking confidence=LOW + no citations (heuristic)
        # The golden set knows, but we don't have it here — skip if answer starts with refusal patterns
        answer_lower = result.scout_answer.answer.lower()
        is_likely_unanswerable = any(
            kw in answer_lower
            for kw in ["cannot answer", "don't have", "not available", "outside my", "no data"]
        ) and result.scout_answer.confidence.value == "low"

        if is_likely_unanswerable:
            # None (not zero) for UNANSWERABLE — different semantically
            scores.append(RagasScores(entry_id=result.entry_id))
            continue

        try:
            contexts = result.scout_answer.retrieved_contexts or [
                c.quote for c in result.scout_answer.citations if c.quote
            ]
            if not contexts:
                contexts = [result.scout_answer.answer]  # fallback

            data = {
                "question": [result.question],
                "answer": [result.scout_answer.answer],
                "contexts": [contexts],
            }
            dataset = Dataset.from_dict(data)

            # context_utilization: measures how well retrieved context is used in the answer
            # (does not require ground_truth, unlike context_precision)
            metrics_list = [faithfulness, answer_relevancy, context_utilization]
            for m in metrics_list:
                m.llm = ragas_llm

            result_ds = evaluate(dataset, metrics=metrics_list)
            row = result_ds.to_pandas().iloc[0]

            cp_raw = row.get("context_utilization")
            context_relevance_val: float | None = None
            try:
                if cp_raw is not None:
                    import math
                    fval = float(cp_raw)
                    context_relevance_val = None if math.isnan(fval) else fval
            except (TypeError, ValueError):
                context_relevance_val = None

            scores.append(
                RagasScores(
                    entry_id=result.entry_id,
                    faithfulness=float(row.get("faithfulness", 0.0)),
                    context_relevance=context_relevance_val,
                    answer_relevance=float(row.get("answer_relevancy", row.get("answer_relevance", 0.0))),
                )
            )
        except Exception as e:
            logger.exception(f"RAGAS scoring failed for {result.entry_id}: {e}")
            scores.append(RagasScores(entry_id=result.entry_id, error=str(e)))

    return scores
