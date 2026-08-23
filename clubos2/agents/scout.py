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
        chunk_blocks.append(f'[source: {c.source}]\n"{c.text}"')

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


_ALERT_QUERY_TERMS = frozenset(
    ["alert", "alerts", "watchdog", "warning", "critical", "fired", "triggered", "anomaly detected"]
)

_SIGNAL_QUERY_TERMS = frozenset(
    ["signal", "signals", "signal engine", "correlation", "correlations", "leading indicator",
     "predicts", "predict", "lag", "downstream", "top signal", "strongest signal"]
)

_INVESTIGATION_QUERY_TERMS = frozenset(
    ["investigation", "investigations", "investigated", "investigate",
     "root cause", "cause", "finding", "findings", "what happened",
     "latest investigation", "recent investigation", "investigation result"]
)


def _is_alert_focused_query(question: str) -> bool:
    q = question.lower()
    return any(term in q for term in _ALERT_QUERY_TERMS)


def _is_signal_focused_query(question: str) -> bool:
    q = question.lower()
    return any(term in q for term in _SIGNAL_QUERY_TERMS)


def _is_investigation_focused_query(question: str) -> bool:
    q = question.lower()
    return any(term in q for term in _INVESTIGATION_QUERY_TERMS)


async def _enrich_with_alerts(
    context_parts: list[str],  # mutable list being built for LLM context
    metric_names: list[str],
    alerts_repo,
    *,
    fetch_all_recent: bool = False,
) -> None:
    """Inject recent Watchdog alerts into context.

    When fetch_all_recent=True (alert-focused query with no metric match),
    fetches the most recent alerts across all metrics instead of per-metric.
    """
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=30)

    if fetch_all_recent:
        try:
            recent_alerts = await alerts_repo.list_recent(limit=10, since=since)
            if recent_alerts:
                context_parts.append(_format_all_alerts_block(recent_alerts))
        except Exception as e:
            logger.warning("Failed to fetch recent alerts: %s", e)
        return

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


def _alert_detail_line(alert) -> str:
    """Render one alert as a dense detail line with all available fields."""
    alert_type_val = alert.alert_type.value if hasattr(alert.alert_type, "value") else str(alert.alert_type)
    severity_val = alert.severity.value if hasattr(alert.severity, "value") else str(alert.severity)
    ack = " [acknowledged]" if getattr(alert, "acknowledged_at", None) else ""

    score_curr = getattr(alert, "score_current", None)
    score_prev = getattr(alert, "score_previous", None)
    rank_curr = getattr(alert, "current_rank", None)
    rank_prev = getattr(alert, "previous_rank", None)
    rank_delta = getattr(alert, "rank_delta", None)

    score_part = ""
    if score_curr is not None and score_prev is not None:
        delta = score_curr - score_prev
        sign = "+" if delta >= 0 else ""
        score_part = f" | score: {score_prev:.2f} → {score_curr:.2f} ({sign}{delta:.2f})"

    rank_part = ""
    if rank_prev is not None and rank_curr is not None:
        rd = f" Δ{rank_delta}" if rank_delta is not None else ""
        rank_part = f" | rank: #{rank_prev} → #{rank_curr}{rd}"

    return (
        f"- [{alert.created_at.strftime('%Y-%m-%d')}] {alert.metric_name} | "
        f"severity: {severity_val} | type: {alert_type_val}{score_part}{rank_part}"
        f" | rule: {getattr(alert, 'triggered_by_rule', '?')}{ack}"
    )


def _format_alerts_block(metric_name: str, alerts) -> str:
    """Format per-metric alert context block for Scout."""
    lines = [f"=== RECENT ALERTS FOR {metric_name} ===", "[source: watchdog_alerts]"]
    for alert in alerts:
        lines.append(_alert_detail_line(alert))
    return "\n".join(lines)


def _format_all_alerts_block(alerts) -> str:
    """Format all recent alerts as a context block (for alert-focused queries)."""
    lines = ["=== RECENT WATCHDOG ALERTS (ALL METRICS) ===", "[source: watchdog_alerts]"]
    for alert in alerts:
        lines.append(_alert_detail_line(alert))
    return "\n".join(lines)


def format_investigations_for_context(invs: list) -> str:
    """Format investigations as a Scout context block with full detail."""
    lines = ["=== RECENT INVESTIGATIONS ===", "[source: investigations]"]
    for inv in invs:
        started = str(getattr(inv, "started_at", ""))[:10]
        completed = str(getattr(inv, "completed_at", "") or "")[:10]
        status = getattr(inv, "status", "unknown")
        status_val = status.value if hasattr(status, "value") else str(status)
        metric = getattr(inv, "metric_name", "?")
        inv_id = getattr(inv, "investigation_id", "?")
        confidence = getattr(inv, "confidence", None)
        confidence_val = confidence.value if hasattr(confidence, "value") else str(confidence) if confidence else "—"

        lines.append(f"")
        lines.append(f"Investigation {inv_id} | metric: {metric} | status: {status_val}")
        lines.append(f"  Started: {started} | Completed: {completed or 'n/a'}")

        if status_val == "completed":
            lines.append(f"  Confidence: {confidence_val}")
            cause = getattr(inv, "cause_hypothesis", None)
            if cause:
                lines.append(f"  Cause hypothesis: {cause}")
            evidence = getattr(inv, "evidence_summary", None)
            if evidence:
                truncated = evidence[:400] + ("..." if len(evidence) > 400 else "")
                lines.append(f"  Evidence: {truncated}")
        elif status_val == "failed":
            err = getattr(inv, "error_message", None) or ""
            short_err = err[:150] + ("..." if len(err) > 150 else "") if err else "unknown error"
            lines.append(f"  Failed: {short_err}")
        elif status_val == "running":
            steps = getattr(inv, "total_steps", None)
            lines.append(f"  In progress — {steps or '?'} steps so far")

    return "\n".join(lines)


async def _enrich_with_investigations(
    context_parts: list[str],
    metric_names: list[str],
    investigations_repo,
    *,
    fetch_all_recent: bool = False,
) -> None:
    """Inject past investigations into context.

    When fetch_all_recent=True (investigation-focused query with no metric match),
    fetches the most recent investigations across all metrics and statuses.
    """
    from clubos2.investigator.schema import InvestigationStatus

    if fetch_all_recent:
        try:
            recent_invs = await investigations_repo.list_recent(limit=5)
            if recent_invs:
                context_parts.append(format_investigations_for_context(recent_invs))
        except Exception as e:
            logger.warning("Failed to fetch recent investigations: %s", e)
        return

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
    alert_focused = _is_alert_focused_query(input.question)
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
                await _enrich_with_alerts(
                    alert_context_parts,
                    metric_names_queried,
                    alerts_repo,
                    fetch_all_recent=alert_focused and not metric_names_queried,
                )
                if alert_context_parts:
                    context_block = context_block + "\n\n" + "\n\n".join(alert_context_parts)
                    alerts_were_used = True
            except Exception as e:
                logger.warning("Alert context enrichment failed, continuing: %s", e)

    # Phase 3b: Signal context enrichment for signal-focused queries
    if _is_signal_focused_query(input.question):
        try:
            from clubos2.tools.registry import query_signals
            signals = await query_signals(limit=10)
            if signals:
                lines = ["=== SIGNAL ENGINE — TOP SIGNALS BY CORRELATION ===", "[source: gold.signal_relationships]"]
                for s in signals:
                    lines.append(
                        f"#{s['rank']} | {s['source_asset']}.{s['source_metric']} → "
                        f"{s['target_asset']}.{s['target_metric']} | "
                        f"strength: {s['strength_score']:.3f} | lag: {s['lag_months']}m | "
                        f"direction: {s['relationship_direction']} | status: {s['validation_status']}"
                    )
                    if s.get("business_interpretation"):
                        lines.append(f"   interpretation: {s['business_interpretation']}")
                context_block = context_block + "\n\n" + "\n".join(lines)
        except Exception as e:
            logger.warning("Signal context enrichment failed, continuing: %s", e)

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
                investigation_focused = _is_investigation_focused_query(input.question)
                await _enrich_with_investigations(
                    inv_context_parts,
                    metric_names_queried,
                    investigations_repo,
                    fetch_all_recent=investigation_focused and not metric_names_queried,
                )
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
