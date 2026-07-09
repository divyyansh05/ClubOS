from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel

from clubos2.briefer.schema import BriefingType
from clubos2.investigator.repo import InvestigationRepository
from clubos2.investigator.schema import InvestigationRead, InvestigationStatus
from clubos2.watchdog.alerts_repo import AlertsRepository
from clubos2.watchdog.alerts_schema import AlertSeverity, WatchdogAlertRead
from clubos2.watchdog.memory_repo import AgentMemoryRepository
from clubos2.watchdog.memory_schema import AgentMemoryRead


class BriefingSourceMaterial(BaseModel):
    """Everything the Briefer LLM needs, pre-fetched. No LLM calls in this layer."""

    model_config = {"arbitrary_types_allowed": True}

    period_start: datetime
    period_end: datetime
    briefing_type: str
    scope_key: str

    # Primary source
    investigations: list[InvestigationRead]

    # Supplementary
    alerts_in_period: list[WatchdogAlertRead]
    memory_entries: list[AgentMemoryRead]

    # Deterministic aggregates — computed here, never by the LLM
    total_investigations: int
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    metrics_investigated: list[str]
    persistent_metrics: list[str]  # appeared in 3+ investigations


def _compute_aggregates(investigations: list[InvestigationRead]) -> dict:
    metric_counts: dict[str, int] = {}
    for inv in investigations:
        metric_counts[inv.metric_name] = metric_counts.get(inv.metric_name, 0) + 1

    return {
        "total_investigations": len(investigations),
        "high_confidence_count": sum(1 for i in investigations if i.confidence and i.confidence.value == "high"),
        "medium_confidence_count": sum(1 for i in investigations if i.confidence and i.confidence.value == "medium"),
        "low_confidence_count": sum(1 for i in investigations if i.confidence and i.confidence.value == "low"),
        "metrics_investigated": list(set(i.metric_name for i in investigations)),
        "persistent_metrics": [m for m, c in metric_counts.items() if c >= 3],
    }


def _parse_metric_scope_key(scope_key: str) -> tuple[str, int]:
    """Parse 'metric:{name}:last_{N}d' → (metric_name, days)."""
    m = re.match(r"^metric:(.+):last_(\d+)d$", scope_key)
    if not m:
        raise ValueError(f"Invalid METRIC_FOCUS scope_key format: {scope_key!r}. Expected 'metric:<name>:last_<N>d'")
    return m.group(1), int(m.group(2))


def _parse_incident_scope_key(scope_key: str) -> str:
    """Parse 'incident:{alert_id}' → alert_id."""
    m = re.match(r"^incident:(.+)$", scope_key)
    if not m:
        raise ValueError(f"Invalid INCIDENT_RECAP scope_key format: {scope_key!r}. Expected 'incident:<alert_id>'")
    return m.group(1)


async def assemble_source_material(
    briefing_type: str,
    scope_key: str,
    period_start: datetime,
    period_end: datetime,
    investigations_repo: InvestigationRepository,
    alerts_repo: AlertsRepository,
    memory_repo: AgentMemoryRepository,
) -> BriefingSourceMaterial:
    """Fetch all source data for a briefing. Pure retrieval — no LLM calls.

    Routing:
    - MONTHLY_SCHEDULED / AD_HOC_SUMMARY: all completed investigations + critical
      alerts in the period + memory entries for the period.
    - METRIC_FOCUS: filter investigations and alerts by metric_name; memories
      filtered to that metric's subject_key prefix.
    - INCIDENT_RECAP: single alert_id; fetch its investigation(s), the alert,
      and related memories.

    Aggregates (total count, confidence distribution, persistent metrics) are
    computed deterministically here — the LLM does not count.
    """
    btype = briefing_type.lower()

    if btype in (BriefingType.MONTHLY_SCHEDULED.value, BriefingType.AD_HOC_SUMMARY.value):
        investigations, alerts, memories = await _fetch_monthly(
            period_start, period_end, investigations_repo, alerts_repo, memory_repo
        )

    elif btype == BriefingType.METRIC_FOCUS.value:
        metric_name, days = _parse_metric_scope_key(scope_key)
        computed_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        effective_start = max(period_start, computed_start)
        investigations, alerts, memories = await _fetch_metric_focus(
            metric_name, effective_start, period_end, investigations_repo, alerts_repo, memory_repo
        )

    elif btype == BriefingType.INCIDENT_RECAP.value:
        alert_id = _parse_incident_scope_key(scope_key)
        investigations, alerts, memories = await _fetch_incident_recap(
            alert_id, investigations_repo, alerts_repo, memory_repo
        )

    else:
        raise ValueError(f"Unknown briefing_type: {briefing_type!r}")

    aggs = _compute_aggregates(investigations)

    return BriefingSourceMaterial(
        period_start=period_start,
        period_end=period_end,
        briefing_type=briefing_type,
        scope_key=scope_key,
        investigations=investigations,
        alerts_in_period=alerts,
        memory_entries=memories,
        **aggs,
    )


# ---------------------------------------------------------------------------
# Private fetch helpers — one per briefing type
# ---------------------------------------------------------------------------

async def _fetch_monthly(
    period_start: datetime,
    period_end: datetime,
    investigations_repo: InvestigationRepository,
    alerts_repo: AlertsRepository,
    memory_repo: AgentMemoryRepository,
) -> tuple[list[InvestigationRead], list[WatchdogAlertRead], list[AgentMemoryRead]]:
    all_invs = await investigations_repo.list_recent(
        limit=100,
        status=InvestigationStatus.COMPLETED,
        since=period_start,
    )
    investigations = [i for i in all_invs if i.started_at <= period_end]

    all_alerts = await alerts_repo.list_recent(
        limit=200,
        since=period_start,
        severity=AlertSeverity.CRITICAL,
    )
    alerts = [a for a in all_alerts if a.created_at <= period_end]

    memories = await memory_repo.list_in_period(period_start, period_end)

    return investigations, alerts, memories


async def _fetch_metric_focus(
    metric_name: str,
    period_start: datetime,
    period_end: datetime,
    investigations_repo: InvestigationRepository,
    alerts_repo: AlertsRepository,
    memory_repo: AgentMemoryRepository,
) -> tuple[list[InvestigationRead], list[WatchdogAlertRead], list[AgentMemoryRead]]:
    all_invs = await investigations_repo.list_recent(
        limit=100,
        metric_name=metric_name,
        status=InvestigationStatus.COMPLETED,
        since=period_start,
    )
    investigations = [i for i in all_invs if i.started_at <= period_end]

    all_alerts = await alerts_repo.list_recent(
        limit=100,
        metric_name=metric_name,
        since=period_start,
    )
    alerts = [a for a in all_alerts if a.created_at <= period_end]

    memories = await memory_repo.list_in_period(
        period_start,
        period_end,
        subject_key_prefix=f"{metric_name}::",
    )

    return investigations, alerts, memories


async def _fetch_incident_recap(
    alert_id: str,
    investigations_repo: InvestigationRepository,
    alerts_repo: AlertsRepository,
    memory_repo: AgentMemoryRepository,
) -> tuple[list[InvestigationRead], list[WatchdogAlertRead], list[AgentMemoryRead]]:
    # Get the specific alert
    alert = await alerts_repo.get_by_id(alert_id)
    alerts = [alert] if alert else []

    # Get all investigations linked to this alert
    investigations = await investigations_repo.get_by_alert(alert_id)
    investigations = [i for i in investigations if i.status == InvestigationStatus.COMPLETED]

    # Memories where subject_metadata contains the alert_id
    # Use a broad lookback (90 days) and filter in Python
    lookback = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=90)
    all_memories = await memory_repo.list_in_period(lookback, datetime.now(timezone.utc).replace(tzinfo=None))
    memories = [
        m for m in all_memories
        if m.subject_metadata and alert_id in m.subject_metadata
    ]

    return investigations, alerts, memories
