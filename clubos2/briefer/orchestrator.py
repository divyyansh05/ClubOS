from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from uuid import uuid4

from clubos2.agents.scout_schemas import Citation
from clubos2.briefer.agent_schemas import BriefingContent, BriefingInput, BriefingRunResult, BriefingType
from clubos2.briefer.input_assembly import BriefingSourceMaterial, assemble_source_material
from clubos2.briefer.repo import BriefingRepository
from clubos2.gateway.client import ModelTier, call_llm
from clubos2.investigator.repo import InvestigationRepository
from clubos2.observability.tracing import get_current_langsmith_trace_url, traced
from clubos2.watchdog.alerts_repo import AlertsRepository
from clubos2.watchdog.memory_repo import AgentMemoryRepository

logger = logging.getLogger(__name__)


def _load_briefer_prompt() -> str:
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        path = parent / "prompts" / "briefer_v1.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
    raise FileNotFoundError("Could not find prompts/briefer_v1.md")


def format_source_for_llm(source: BriefingSourceMaterial) -> str:
    """Convert BriefingSourceMaterial into a well-structured prompt for the Briefer LLM."""
    parts = [
        "# Briefing Input\n",
        f"**Period:** {source.period_start.date()} to {source.period_end.date()}",
        f"**Briefing type:** {source.briefing_type}",
        f"**Scope:** {source.scope_key}\n",
        "## Aggregates (pre-computed, do not re-count)",
        f"- Total investigations: {source.total_investigations}",
        f"- High confidence: {source.high_confidence_count}",
        f"- Medium confidence: {source.medium_confidence_count}",
        f"- Low confidence: {source.low_confidence_count}",
        f"- Metrics investigated: {', '.join(source.metrics_investigated) or 'none'}",
        f"- Persistent metrics (3+ investigations): {', '.join(source.persistent_metrics) or 'none'}\n",
    ]

    if source.investigations:
        parts.append(f"## Investigations ({len(source.investigations)} completed)\n")
        for inv in source.investigations:
            parts.append(f"### Investigation {inv.investigation_id}")
            parts.append("[source: investigations]")
            parts.append(f"- Metric: {inv.metric_name}")
            parts.append(f"- Alert: {inv.alert_id}")
            confidence_val = inv.confidence.value if inv.confidence else "unknown"
            parts.append(f"- Confidence: {confidence_val}")
            parts.append(f"- Hypothesis: {inv.cause_hypothesis or 'not available'}")
            parts.append(f"- Evidence: {inv.evidence_summary or 'not available'}\n")
    else:
        parts.append("## Investigations\n\nNo investigations concluded in this period.\n")

    if source.alerts_in_period:
        parts.append(f"## Alerts in period ({len(source.alerts_in_period)})\n")
        for alert in source.alerts_in_period[:20]:
            parts.append(
                f"- {alert.metric_name} ({alert.severity.value if hasattr(alert.severity, 'value') else alert.severity}): "
                f"{alert.alert_type}, rank {alert.current_rank} (was {alert.previous_rank}) "
                f"[source: watchdog_alerts]"
            )

    if source.memory_entries:
        parts.append("\n## Recurring patterns from agent_memory\n")
        memory_by_subject: dict[str, list] = {}
        for m in source.memory_entries:
            memory_by_subject.setdefault(m.subject_key, []).append(m)
        for subject, entries in memory_by_subject.items():
            parts.append(f"- {subject}: {len(entries)} occurrences [source: agent_memory]")

    return "\n".join(parts)


@traced(name="briefer:run", run_type="chain")
async def run_briefing(input: BriefingInput) -> BriefingRunResult:
    """Run one briefing end-to-end.

    Pipeline:
    0. DEDUP CHECK — return cached briefing if fresh match exists and force_regenerate=False.
    1. Assemble source material from investigations, alerts, memory.
    2. Start briefings row with status='generating'.
    3. Load briefer_v1.md prompt.
    4. Format source material into LLM input.
    5. Call LLM with structured output (BriefingContent).
    6. Persist to briefings table.
    7. Return BriefingRunResult.
    """
    started_at = time.perf_counter()

    briefings_repo = BriefingRepository()
    investigations_repo = InvestigationRepository()
    alerts_repo = AlertsRepository()
    memory_repo = AgentMemoryRepository()

    # STEP 0 — Dedup cache check
    if not input.force_regenerate:
        cached = await briefings_repo.find_fresh(
            scope_key=input.scope_key,
            max_age_days=input.freshness_days,
        )
        if cached is not None:
            logger.info(f"Returning cached briefing {cached.briefing_id} for scope {input.scope_key}")
            try:
                raw_cit = cached.citations
                cit_list = raw_cit if isinstance(raw_cit, list) else json.loads(raw_cit or "[]")
                citations = [Citation.model_validate(c) for c in cit_list]
            except Exception:
                citations = []

            def _parse_list(val) -> list:
                if val is None:
                    return []
                if isinstance(val, list):
                    return val
                return json.loads(val)

            return BriefingRunResult(
                briefing_id=cached.briefing_id,
                briefing_type=BriefingType(cached.briefing_type),
                scope_key=cached.scope_key,
                status="cached",
                was_cached=True,
                content=BriefingContent(
                    executive_summary=cached.executive_summary or "",
                    body_markdown=cached.body_markdown or "",
                    citations=citations,
                    investigations_referenced=_parse_list(cached.investigations_referenced),
                    alerts_referenced=_parse_list(cached.alerts_referenced),
                    metrics_covered=_parse_list(cached.metrics_covered),
                ),
                latency_seconds=time.perf_counter() - started_at,
                trace_url=cached.trace_url,
            )

    # STEP 1 — Assemble source material
    try:
        source = await assemble_source_material(
            briefing_type=input.briefing_type.value,
            scope_key=input.scope_key,
            period_start=input.period_start,
            period_end=input.period_end,
            investigations_repo=investigations_repo,
            alerts_repo=alerts_repo,
            memory_repo=memory_repo,
        )
    except Exception as e:
        logger.exception("Source material assembly failed")
        return BriefingRunResult(
            briefing_id=f"brf_{uuid4().hex[:16]}",
            briefing_type=input.briefing_type,
            scope_key=input.scope_key,
            status="failed",
            was_cached=False,
            content=None,
            latency_seconds=time.perf_counter() - started_at,
            error=f"Source assembly failed: {e}",
        )

    # STEP 2 — Start briefings row
    briefing_row = await briefings_repo.start(
        briefing_type=input.briefing_type.value,
        scope_key=input.scope_key,
        period_start=input.period_start,
        period_end=input.period_end,
        triggered_by=input.triggered_by,
        freshness_days=input.freshness_days,
    )
    briefing_id = briefing_row.briefing_id

    # STEP 3 — Load system prompt
    try:
        system_prompt = _load_briefer_prompt()
    except FileNotFoundError as e:
        latency = time.perf_counter() - started_at
        await briefings_repo.fail(briefing_id=briefing_id, error_message=str(e), latency_seconds=latency)
        return BriefingRunResult(
            briefing_id=briefing_id,
            briefing_type=input.briefing_type,
            scope_key=input.scope_key,
            status="failed",
            was_cached=False,
            content=None,
            latency_seconds=latency,
            error=str(e),
        )

    # STEP 4 — Format source material
    user_input = format_source_for_llm(source)

    # STEP 5 — LLM call with structured output
    try:
        content: BriefingContent = await call_llm(  # type: ignore[assignment]
            messages=[{"role": "user", "content": user_input}],
            tier=ModelTier.REASONING,
            response_model=BriefingContent,
            temperature=0.0,
            max_tokens=4096,
            system=system_prompt,
        )

        # STEP 6 — Persist
        latency = time.perf_counter() - started_at
        await briefings_repo.complete(
            briefing_id=briefing_id,
            executive_summary=content.executive_summary,
            body_markdown=content.body_markdown,
            citations=content.citations,
            investigations_referenced=content.investigations_referenced,
            alerts_referenced=content.alerts_referenced,
            metrics_covered=content.metrics_covered,
            total_tokens=None,
            cost_usd=None,
            latency_seconds=latency,
            trace_url=get_current_langsmith_trace_url(),
        )

        return BriefingRunResult(
            briefing_id=briefing_id,
            briefing_type=input.briefing_type,
            scope_key=input.scope_key,
            status="completed",
            was_cached=False,
            content=content,
            latency_seconds=latency,
            trace_url=get_current_langsmith_trace_url(),
        )

    except Exception as e:
        latency = time.perf_counter() - started_at
        logger.exception(f"Briefing composition failed for {briefing_id}")
        await briefings_repo.fail(
            briefing_id=briefing_id,
            error_message=str(e),
            latency_seconds=latency,
        )
        return BriefingRunResult(
            briefing_id=briefing_id,
            briefing_type=input.briefing_type,
            scope_key=input.scope_key,
            status="failed",
            was_cached=False,
            content=None,
            latency_seconds=latency,
            error=str(e),
        )
