from __future__ import annotations

import asyncio
import logging
import os
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
    """Helper to locate and read the Scout system prompt.

    Version is resolved from GatewaySettings.scout_prompt_version (set via SCOUT_PROMPT_VERSION
    in .env.v2) with a fallback to the SCOUT_PROMPT_VERSION environment variable, defaulting
    to 'v1' if neither is set. The resolved filename is e.g. 'scout_v3.md'.
    """
    try:
        from clubos2.gateway.client import GatewaySettings
        _s = GatewaySettings()
        version = getattr(_s, "scout_prompt_version", None) or os.environ.get("SCOUT_PROMPT_VERSION", "v4")
    except Exception:
        logger.warning(
            "GatewaySettings failed to load. Falling back to scout_prompt_version=v4. "
            "This fallback should never fire in production — check SCOUT_PROMPT_VERSION env config."
        )
        version = os.environ.get("SCOUT_PROMPT_VERSION", "v4")

    filename = f"scout_{version}.md"
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        path = parent / "prompts" / filename
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return f.read()
    fallback_path = Path("./prompts") / filename
    if fallback_path.exists():
        with open(fallback_path, encoding="utf-8") as f:
            return f.read()
    raise FileNotFoundError(f"Could not find prompts/{filename} system prompt file.")


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
        # Include peer context if available — enables peer comparison answers
        peer_ranks = [r.peer_rank for r in rows if r.peer_rank is not None]
        peer_gaps = [r.peer_gap_to_median for r in rows if r.peer_gap_to_median is not None]
        peer_counts = [r.peer_club_count for r in rows if r.peer_club_count is not None]
        if peer_ranks and peer_gaps:
            latest_rank = peer_ranks[0]
            latest_gap = peer_gaps[0]
            latest_count = peer_counts[0] if peer_counts else "?"
            gap_sign = "+" if latest_gap >= 0 else ""
            block.append(
                f"  Peer context (most recent): rank {latest_rank} of {latest_count} clubs, "
                f"gap to peer median {gap_sign}{latest_gap:.6f}"
            )

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


async def _enrich_with_alerts(
    context_parts: list[str],  # mutable list being built for LLM context
    metric_names: list[str],
    alerts_repo,
) -> None:
    """Inject recent Watchdog alerts for queried metrics into context."""
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=7)

    for metric_name in metric_names:
        try:
            recent_alerts = await alerts_repo.list_recent(
                limit=3,
                since=since,
                metric_name=metric_name,
            )
            if recent_alerts:
                context_parts.append(_format_alerts_block(metric_name, recent_alerts))
        except Exception as e:
            logger.warning("Failed to fetch alerts for %s: %s", metric_name, e)


def _format_alerts_block(metric_name: str, alerts) -> str:
    """Format alerts as a context block for Scout."""
    lines = [f"=== RECENT ALERTS FOR {metric_name} ===", "[source: watchdog_alerts]"]
    for alert in alerts:
        alert_type_val = alert.alert_type.value if hasattr(alert.alert_type, "value") else str(alert.alert_type)
        severity_val = alert.severity.value if hasattr(alert.severity, "value") else str(alert.severity)
        lines.append(
            f"- {alert.created_at.strftime('%Y-%m-%d')} — "
            f"alert_type: {alert_type_val}, severity: {severity_val}, "
            f"rank: {alert.current_rank} (rule: {alert.triggered_by_rule})"
        )
        if hasattr(alert, 'triggered_by_rule'):
            reason = f"  Rule fired: {alert.triggered_by_rule}"
            lines.append(reason)
    return "\n".join(lines)


def format_investigations_for_context(invs: list) -> str:
    """Format completed investigation findings as a Scout context block."""
    lines = ["=== RELATED PAST INVESTIGATIONS ===\n[source: investigations]"]
    for inv in invs:
        date_str = inv.started_at.strftime("%Y-%m-%d") if hasattr(inv.started_at, "strftime") else str(inv.started_at)[:10]
        lines.append(
            f"- {date_str} (alert {inv.alert_id}, confidence: {inv.confidence}):"
        )
        lines.append(f"  Cause: {inv.cause_hypothesis}")
        if inv.evidence_summary:
            truncated = inv.evidence_summary[:200]
            if len(inv.evidence_summary) > 200:
                truncated += "..."
            lines.append(f"  Evidence: {truncated}")
    return "\n".join(lines)


async def _enrich_with_investigations(
    context_parts: list[str],
    metric_names: list[str],
    investigations_repo,
) -> None:
    """Inject completed past investigations for queried metrics into context."""
    from clubos2.investigator.schema import InvestigationStatus

    for metric_name in metric_names:
        try:
            completed_invs = await investigations_repo.list_recent(
                limit=3,
                metric_name=metric_name,
                status=InvestigationStatus.COMPLETED,
            )
            if completed_invs:
                context_parts.append(format_investigations_for_context(completed_invs))
        except Exception as e:
            logger.warning("Failed to fetch investigations for %s: %s", metric_name, e)


@traced(name="scout:run", run_type="chain")
async def run_scout(
    input: ScoutInput,
    *,
    enable_alert_context: bool = True,
    enable_investigation_context: bool = True,
) -> ScoutAnswer:
    """Main entry point. Implements the Scout pipeline."""
    # 1. Semantic layer pre-check
    terms = extract_terms(input.question)
    matched_metrics = lookup_metrics_by_terms(terms)
    ambiguities = detect_ambiguity(input.question)

    # 2 & 3. Tool plan & Parallel Execution
    async def _safe_query(metric_name: str) -> list[MetricRow]:
        try:
            return await query_metrics(metric_name)
        except Exception as e:
            logger.warning(f"Metric query skipped for '{metric_name}': {e}")
            return []

    metric_tasks = [_safe_query(m.metric_name) for m in matched_metrics]
    knowledge_task = search_knowledge(input.question, k=5)

    # Execute all tools in parallel
    results = await asyncio.gather(*metric_tasks, knowledge_task)

    metrics_results: list[MetricRow] = []
    for res_list in results[:-1]:
        metrics_results.extend(res_list)

    knowledge_results: list[KnowledgeChunk] = results[-1]

    # Sanitise retrieved chunks for prompt injection patterns
    from clubos2.guardrails.injection_defence import sanitise_for_injection
    _, knowledge_results, injection_detections = sanitise_for_injection(knowledge_results)
    if injection_detections:
        logger.warning(
            "Injection patterns detected in retrieved content",
            extra={"detections": [d.model_dump() for d in injection_detections]},
        )

    # 4. Assemble context
    context_block = await assemble_context(metrics_results, knowledge_results, ambiguities)

    # Phase 3: Alert context enrichment (non-breaking, skipped silently on any failure)
    alerts_were_used = False
    metric_names_queried = list({m.metric_name for m in matched_metrics})
    if enable_alert_context:
        alerts_repo = None
        try:
            from clubos2.watchdog.alerts_repo import AlertsRepository
            alerts_repo = AlertsRepository()
        except Exception as e:
            logger.warning("Could not init alerts_repo, skipping alert context: %s", e)

        if alerts_repo:
            try:
                alert_context_parts: list[str] = []
                await _enrich_with_alerts(alert_context_parts, metric_names_queried, alerts_repo)
                if alert_context_parts:
                    context_block = context_block + "\n\n" + "\n\n".join(alert_context_parts)
                    alerts_were_used = True
            except Exception as e:
                logger.warning("Alert context enrichment failed, continuing: %s", e)

    # Phase 4: Investigation context enrichment (non-breaking, skipped silently on any failure)
    investigations_were_used = False
    if enable_investigation_context:
        investigations_repo = None
        try:
            from clubos2.investigator.repo import InvestigationRepository
            investigations_repo = InvestigationRepository()
        except Exception as e:
            logger.warning("Could not init investigations_repo, skipping investigation context: %s", e)

        if investigations_repo:
            try:
                inv_context_parts: list[str] = []
                await _enrich_with_investigations(inv_context_parts, metric_names_queried, investigations_repo)
                if inv_context_parts:
                    context_block = context_block + "\n\n" + "\n\n".join(inv_context_parts)
                    investigations_were_used = True
            except Exception as e:
                logger.warning("Investigation context enrichment failed, continuing: %s", e)

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
    ans.metrics_queried = metric_names_queried

    # Add watchdog_alerts citation if alert context was injected
    if alerts_were_used:
        from clubos2.agents.scout_schemas import Citation
        ans.citations.append(
            Citation(
                claim="Recent Watchdog alerts surfaced in context",
                source="watchdog_alerts",
            )
        )
    # Add investigations citation if investigation context was injected
    if investigations_were_used:
        from clubos2.agents.scout_schemas import Citation
        ans.citations.append(
            Citation(
                claim="Past completed investigations surfaced in context",
                source="investigations",
            )
        )
    ans.chunks_retrieved = len(knowledge_results)
    # retrieved_contexts = metric values + peer data + knowledge chunks + full context block
    # The full context_block is included so the fabrication scorer can verify ALL numbers
    # the LLM had access to (including peer gaps, seasonal notes, etc.)
    metric_context_texts = [
        f"{m.metric_name} {m.month}: {m.value} "
        + (f"peer_rank={m.peer_rank} peer_gap={m.peer_gap_to_median} " if m.peer_rank is not None else "")
        + f"[{m.source}]"
        for m in metrics_results
    ]
    ans.retrieved_contexts = metric_context_texts + [chunk.text for chunk in knowledge_results] + [context_block]

    # Post-LLM guardrail: block ungrounded numbers
    from clubos2.guardrails.no_fabricated_numbers import check_no_fabricated_numbers
    _guardrail_mode = os.getenv("GUARDRAIL_FABRICATION_MODE", "warn")
    guarded = await check_no_fabricated_numbers(
        ans,
        question=input.question,
        mode=_guardrail_mode,
    )
    if guarded.violations:
        logger.warning(
            "Scout output guardrail triggered",
            extra={"violations": [v.model_dump() for v in guarded.violations]},
        )
    ans = guarded.answer

    return ans
