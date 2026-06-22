from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from clubos2.agents.scout_schemas import ScoutAnswer, ScoutInput
from clubos2.gateway.client import GatewayValidationError, ModelTier, call_llm
from clubos2.observability.tracing import traced
from clubos2.semantic_layer.lookup import (
    detect_ambiguity,
    lookup_metric,
    lookup_metrics_by_terms,
)
from clubos2.tools.registry import KnowledgeChunk, MetricRow, query_metrics, search_knowledge

logger = logging.getLogger("clubos.agents.scout")


def _load_scout_prompt() -> str:
    """Helper to locate and read prompts/scout_v1.md system prompt."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        path = parent / "prompts" / "scout_v1.md"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return f.read()
    fallback_path = Path("./prompts/scout_v1.md")
    if fallback_path.exists():
        with open(fallback_path, encoding="utf-8") as f:
            return f.read()
    raise FileNotFoundError("Could not find prompts/scout_v1.md system prompt file.")


def extract_terms(question: str) -> list[str]:
    """Extract noun-phrase candidates from the question.

    Phase 1: simple — lowercase, remove stopwords, return 2+ word phrases.
    NO LLM call here — this is fast classification.
    """
    # Clean and lowercase the question
    clean = "".join(c if c.isalnum() or c.isspace() or c == "_" else " " for c in question)
    words = [w.lower() for w in clean.split() if len(w) > 1]

    stopwords = {
        "what",
        "is",
        "the",
        "of",
        "in",
        "on",
        "for",
        "this",
        "month",
        "to",
        "and",
        "does",
        "how",
        "we",
        "our",
        "are",
        "do",
        "you",
        "about",
        "me",
        "show",
        "get",
        "find",
        "query",
        "run",
        "metric",
        "metrics",
        "data",
        "value",
        "values",
        "did",
        "has",
        "have",
        "would",
        "could",
        "should",
        "can",
        "if",
        "at",
        "by",
        "from",
        "or",
        "an",
        "as",
        "but",
        "with",
        "which",
        "whose",
        "who",
        "whom",
    }
    filtered = [w for w in words if w not in stopwords]

    # Generate 2-word phrases (bigrams)
    phrases = []
    for i in range(len(filtered) - 1):
        phrases.append(f"{filtered[i]} {filtered[i+1]}")

    return filtered + phrases


async def assemble_context(
    metrics: list[MetricRow],
    chunks: list[KnowledgeChunk],
    ambiguities: list[Any],
) -> str:
    """Format retrieved data into the grounded context block for the LLM."""
    metric_blocks = []
    # Group metrics by metric_name to display cleanly
    grouped_metrics: dict[str, list[MetricRow]] = {}
    for m in metrics:
        grouped_metrics.setdefault(m.metric_name, []).append(m)

    for name, rows in grouped_metrics.items():
        reg = lookup_metric(name)
        business_name = reg.business_name if reg else name.replace("_", " ").title()
        definition = reg.definition if reg else ""
        polarity = reg.polarity if reg else "positive"
        seasonal_note = reg.seasonal_note if reg else ""

        source = rows[0].source if rows else "unknown"

        block = []
        block.append(f"[source: {source}]")
        block.append(f"{name} ({business_name})")
        # Sort months chronologically descending
        for r in sorted(rows, key=lambda x: x.month, reverse=True):
            val = r.value
            if val.is_integer():
                val_str = f"{int(val):,}"
            else:
                val_str = f"{val:,}"
            block.append(f"  - {r.month}: {val_str}")
        if definition:
            block.append(f"  Definition: {definition}")
        if polarity:
            block.append(f"  Polarity: {polarity}")
        if seasonal_note:
            block.append(f"  Seasonal note: {seasonal_note}")

        metric_blocks.append("\n".join(block))

    chunk_blocks = []
    for c in chunks:
        chunk_blocks.append(f'[source: {c.source}::{c.section}]\n"{c.text}"')

    ambiguity_blocks = []
    for a in ambiguities:
        ambiguity_blocks.append(
            f'- "{a.detected_term}" detected: defaulting to {a.default} per rule. '
            f"State this assumption in your answer. Rule: {a.rule_text}"
        )

    context_parts = []
    if metric_blocks:
        context_parts.append("=== STRUCTURED METRIC DATA ===\n" + "\n\n".join(metric_blocks))
    if chunk_blocks:
        context_parts.append("=== NARRATIVE CONTEXT ===\n" + "\n\n".join(chunk_blocks))
    if ambiguity_blocks:
        context_parts.append("=== AMBIGUITY NOTES ===\n" + "\n".join(ambiguity_blocks))

    return "\n\n".join(context_parts)


@traced(name="scout:run", run_type="chain")
async def run_scout(input: ScoutInput) -> ScoutAnswer:
    """Main entry point. Implements the Scout pipeline."""
    # 1. Semantic layer pre-check
    terms = extract_terms(input.question)
    matched_metrics = lookup_metrics_by_terms(terms)
    ambiguities = detect_ambiguity(input.question)

    # 2 & 3. Tool plan & Parallel Execution
    metric_tasks = [query_metrics(m.metric_name) for m in matched_metrics]
    knowledge_task = search_knowledge(input.question, k=5)

    # Execute all tools in parallel
    results = await asyncio.gather(*metric_tasks, knowledge_task)

    metrics_results: list[MetricRow] = []
    for res_list in results[:-1]:
        metrics_results.extend(res_list)

    knowledge_results: list[KnowledgeChunk] = results[-1]

    # 4. Assemble context
    context_block = await assemble_context(metrics_results, knowledge_results, ambiguities)

    # 5. Call LLM via gateway with Pydantic validation and retry
    system_prompt = _load_scout_prompt()
    messages = [
        {
            "role": "user",
            "content": (
                f"=== GROUNDED CONTEXT ===\n{context_block}\n\n"
                f"=== USER QUESTION ===\n{input.question}"
            ),
        }
    ]

    try:
        ans = await call_llm(
            messages=messages,
            tier=ModelTier.REASONING,
            response_model=ScoutAnswer,
            system=system_prompt,
            temperature=0.0,
        )
    except GatewayValidationError as e:
        logger.warning("First attempt failed schema validation: %s. Retrying...", e)
        strict_system = (
            system_prompt + "\n\nCRITICAL: You MUST output ONLY a valid JSON object matching "
            "the ScoutAnswer schema. No markdown, no fences, no other text."
        )
        ans = await call_llm(
            messages=messages,
            tier=ModelTier.REASONING,
            response_model=ScoutAnswer,
            system=strict_system,
            temperature=0.0,
        )

    # Ensure Pydantic answer type is correct
    if not isinstance(ans, ScoutAnswer):
        raise TypeError("LLM Gateway returned invalid answer type.")

    # 6. Override metrics_queried and chunks_retrieved with real counts
    ans.metrics_queried = list({m.metric_name for m in matched_metrics})
    ans.chunks_retrieved = len(knowledge_results)

    return ans
