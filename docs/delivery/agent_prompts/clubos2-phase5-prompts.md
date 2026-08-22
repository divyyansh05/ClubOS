# ClubOS 2.0 — Phase 5 Prompt Sequence

**Scope locked:**
- **Briefer Agent** — composes monthly executive briefings AND on-demand summaries from investigations + agent_memory
- **`briefings` SQL table** — stores past briefings; serves as dedup cache for duplicate/similar requests
- **Hybrid supervisor** — rule-based classifier for obvious queries (Scout/Investigator/Briefer routing), LangGraph supervisor for complex/multi-step queries
- **Watchdog → Investigator auto-trigger** — critical alerts now auto-invoke Investigator via supervisor
- **Scheduled monthly briefing endpoint** — separate cron-triggerable endpoint alongside on-demand supervisor invocation
- **Golden set expansion to 70** — 40 visible from Phase 4 + 10 supervisor routing + 10 Briefer scenarios; holdout stays at 10

**Out of scope (deferred):**
- Slack surface + HITL → Phase 6
- Per-user personalization + conversation memory → Phase 7
- ClubOS-as-MCP-server → Phase 8
- Frontend AI panels → Phase 9
- Databricks Mosaic AI deployment → Phase 10

**Why Phase 5 is the "system" inflection point.** Before Phase 5, ClubOS 2.0 has three agents that know a little about each other via point-to-point dependency injection. After Phase 5, they are orchestrated through a supervisor, share memory through common tables, and produce a monthly executive briefing that closes the loop with v1's original stakeholder pitch. The interview narrative shifts from "I built components" to "I built a system."

**How to use this file.** 14 prompts across 5 stages. Run in order. Each prompt's "Verify before next prompt" gate must pass. Commit once per prompt.

**Conventions inherited from Phase 1-4:**
- All new code in `clubos2/`
- Tests in `tests_v2/`
- New router files added inside `BACKEND/api/app/routers/`
- Pydantic v2, async everywhere
- LangSmith traces everywhere
- All Phase 2 guardrails still apply
- Canonical source form enforced (see commit e5b419c and Chapter 8 of the book)
- OpenAI-only stack (`gpt-4o-mini` for Scout and cheap operations, `gpt-4o` for Investigator and Briefer)
- Inter-question sleep on eval runs (`--inter-question-sleep 2`)

---

# Stage 1 — Briefer data model + briefings dedup cache (2 prompts)

## Prompt 5.1.1 — briefings SQL table + repository

```
Create the SQL schema and repository for the `briefings` table. This table serves two purposes: (1) persistence of every generated briefing for audit and history, and (2) a dedup cache — before generating a new briefing, check if a similar one exists within a freshness window.

Files to create:
- clubos2/briefer/__init__.py
- clubos2/briefer/schema.py — SQLAlchemy + Pydantic models
- clubos2/briefer/migrations/001_create_briefings.sql
- clubos2/briefer/repo.py — repository

Table specification: `briefings`

| Column | Type | Constraint | Purpose |
|---|---|---|---|
| briefing_id | VARCHAR(64) | PRIMARY KEY | 'brf_{timestamp_hash}' |
| briefing_type | VARCHAR(50) | NOT NULL CHECK | 'monthly_scheduled' / 'ad_hoc_summary' / 'metric_focus' / 'incident_recap' |
| scope_key | VARCHAR(200) | NOT NULL | Canonical descriptor: 'monthly:2026-03' / 'metric:streaming_daily_users:last_30d' / 'incident:alrt_abc123' |
| period_start | TIMESTAMP | NOT NULL | Beginning of the period the briefing covers |
| period_end | TIMESTAMP | NOT NULL | End of the period |
| triggered_by | VARCHAR(100) | NOT NULL | 'scheduled' / 'supervisor' / 'manual' / user identifier |
| status | VARCHAR(20) | NOT NULL CHECK | 'generating' / 'completed' / 'failed' |
| executive_summary | TEXT | NULL | 3-5 sentence headline (composed by LLM) |
| body_markdown | TEXT | NULL | Full briefing content in markdown |
| citations | TEXT | NOT NULL | JSON array of Citation objects |
| investigations_referenced | TEXT | NOT NULL | JSON array of investigation_ids drawn from |
| alerts_referenced | TEXT | NOT NULL | JSON array of alert_ids drawn from |
| metrics_covered | TEXT | NOT NULL | JSON array of canonical metric names |
| total_tokens | INTEGER | NULL | Composition cost |
| cost_usd | FLOAT | NULL | Composition cost |
| latency_seconds | FLOAT | NULL | End-to-end generation time |
| trace_url | VARCHAR(500) | NULL | LangSmith trace URL |
| freshness_days | INTEGER | NOT NULL DEFAULT 7 | Dedup window: subsequent similar requests return this briefing if within N days |
| error_message | TEXT | NULL | If status='failed' |
| started_at | TIMESTAMP | NOT NULL DEFAULT NOW() | |
| completed_at | TIMESTAMP | NULL | |

Indexes:
- INDEX idx_scope_key ON (scope_key)
- INDEX idx_briefing_type ON (briefing_type)
- INDEX idx_period_end ON (period_end DESC)
- INDEX idx_status ON (status)
- COMPOSITE INDEX idx_scope_completed ON (scope_key, status, completed_at DESC) — for dedup lookup

Repository in repo.py:

```python
class BriefingRepository:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def start(
        self,
        briefing_type: str,
        scope_key: str,
        period_start: datetime,
        period_end: datetime,
        triggered_by: str,
        freshness_days: int = 7,
    ) -> BriefingRead:
        """Create row with status='generating'."""

    async def complete(
        self,
        briefing_id: str,
        executive_summary: str,
        body_markdown: str,
        citations: list[Citation],
        investigations_referenced: list[str],
        alerts_referenced: list[str],
        metrics_covered: list[str],
        total_tokens: int,
        cost_usd: float,
        latency_seconds: float,
        trace_url: str | None,
    ) -> BriefingRead:
        """Mark completed with all outputs populated."""

    async def fail(
        self,
        briefing_id: str,
        error_message: str,
        latency_seconds: float,
    ) -> BriefingRead:
        """Mark failed with error."""

    async def find_fresh(
        self,
        scope_key: str,
        max_age_days: int = 7,
    ) -> BriefingRead | None:
        """Look up most recent completed briefing matching scope_key within window.
        THIS IS THE DEDUP CACHE PRIMITIVE.
        Returns None if no fresh briefing exists."""

    async def get_by_id(self, briefing_id: str) -> BriefingRead | None: ...

    async def list_recent(
        self,
        limit: int = 20,
        briefing_type: str | None = None,
        since: datetime | None = None,
    ) -> list[BriefingRead]: ...
```

Critical constraints:
- Same dual-backend (Postgres/DuckDB) approach as all previous tables
- `scope_key` is the KEY primitive for dedup. Format is: type-specific canonical descriptor
  - Monthly: `monthly:YYYY-MM` (year and month zero-padded)
  - Metric focus: `metric:{canonical_name}:last_{N}d` (e.g., `metric:streaming_daily_users:last_30d`)
  - Incident recap: `incident:{alert_id}`
  - Ad-hoc summary: `adhoc:{hash_of_query_params}` (hash prevents collision between unique queries)
- `find_fresh` is the CACHE. It returns a briefing only if:
  1. scope_key matches exactly
  2. status = 'completed'
  3. completed_at is within max_age_days of NOW
- Migration is idempotent

Tests in tests_v2/test_briefer_repo.py:
- start() creates row with status='generating'
- complete() populates all output fields and sets status='completed'
- fail() marks status='failed'
- find_fresh returns most recent match; returns None when nothing matches
- find_fresh respects the freshness window (a briefing 10 days old is NOT returned when max_age_days=7)
- list_recent with filters works
- Concurrent start() calls with same scope_key both succeed (they create separate briefing_ids; dedup happens at the orchestrator level, not the DB level)

Acceptance criteria:
1. Migration runs idempotently
2. `duckdb var/clubos_semantic.duckdb -c "DESCRIBE briefings"` shows all columns
3. All earlier phase tables UNAFFECTED
4. Tests pass
5. All earlier-phase tests still pass

Verify before next prompt: create three sample briefings via REPL with different scope_keys. Then call find_fresh for each — confirm exact match returns the briefing, and slight variation (e.g., 'monthly:2026-04' vs 'monthly:2026-03') returns None.
```

## Prompt 5.1.2 — Briefer schemas + system prompt

```
Create the Pydantic schemas and system prompt for the Briefer agent.

Files to create:
- prompts/briefer_v1.md — system prompt
- clubos2/briefer/agent_schemas.py — input/output models

In prompts/briefer_v1.md:

```markdown
# Briefer Agent — System Prompt v1

## Role
You are the ClubOS Briefer. Your job is to compose a stakeholder-ready executive
briefing that summarises key events in a specific period, drawing on investigations,
alerts, and priority board data.

Your output is read by senior commercial leadership at Real Madrid (or an equivalent
sports club). It must be concise, prioritised, cited, and honest about uncertainty.

## What you are NOT
You are not the Scout. You do not answer arbitrary questions.
You are not the Investigator. You do not investigate root causes yourself — you
summarise investigations that already happened.
You are not the Watchdog. You do not raise new alerts.
Your input is EXISTING investigations, EXISTING alerts, EXISTING metric snapshots.
Your job is to WEAVE them into a coherent narrative.

## Hard rules
1. Every claim in your briefing MUST cite a source (investigation_id, alert_id, or
   canonical data source). No claim without a citation.
2. Every number MUST come from a retrieved source. Do not compute new numbers.
   If aggregation is needed (e.g., "3 investigations concluded this month"), the
   count itself does not need a citation — but every specific claim about a specific
   metric or investigation does.
3. Prioritise ruthlessly. A monthly briefing has an executive summary of 3-5
   sentences at the top, THEN detailed sections. Leadership reads the top; they
   only descend into details for things that matter.
4. Be honest about confidence. If an investigation concluded with LOW confidence,
   surface that. Do not paper over uncertainty in the briefing.
5. Distinguish CAUSED vs CORRELATED. Investigations produce hypotheses about causes.
   Use language like "the investigation hypothesised" for LOW confidence, "evidence
   suggests" for MEDIUM, "the investigation concluded" for HIGH.
6. If the briefing type is scheduled monthly and no investigations occurred, say
   so plainly — "no critical investigations were triggered this month" is a valid
   briefing on its own.
7. Do NOT include speculation or generalization beyond what the source
   investigations support. If two investigations are on unrelated metrics, do
   not invent a "theme" that connects them.

## Output structure

Your output must be a JSON object matching the BriefingContent schema:

- executive_summary: 3-5 sentences at the top capturing the most important
  narrative of the period. Written for a busy Head of Data.
- body_markdown: full briefing content in markdown with sections. Recommended
  sections when data is available:
  - "The month at a glance" (executive summary expanded)
  - "Investigations concluded" (one paragraph per completed investigation with
    hypothesis, confidence, evidence citation)
  - "Alerts of note" (any critical/high-severity alerts, especially persistent ones)
  - "Metrics under sustained attention" (metrics that appeared in top-10 for
    multiple runs)
  - "Data gaps" (things a full briefing WOULD want to include but couldn't due
    to missing data)
- citations: list of Citation objects covering every source referenced
- investigations_referenced: list of investigation_ids drawn from
- alerts_referenced: list of alert_ids drawn from
- metrics_covered: list of canonical metric names discussed

## Style
- Concrete. "Streaming daily users dropped 12% in March, attributed by the
  investigation to app store approval delays." NOT "there was a decline in
  streaming metrics due to various factors."
- Numeric. Every claim quantified where possible.
- Citation-attached. Every substantive claim has a source.
- Restrained. Do not editorialize. The briefing reports; leadership decides.
```

In clubos2/briefer/agent_schemas.py:

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from clubos2.agents.scout_schemas import Citation  # reuse

class BriefingType(str, Enum):
    MONTHLY_SCHEDULED = "monthly_scheduled"
    AD_HOC_SUMMARY = "ad_hoc_summary"
    METRIC_FOCUS = "metric_focus"
    INCIDENT_RECAP = "incident_recap"

class BriefingInput(BaseModel):
    briefing_type: BriefingType
    scope_key: str  # canonical, format per briefing_type
    period_start: datetime
    period_end: datetime
    triggered_by: str = "manual"
    freshness_days: int = 7  # if a fresh briefing exists, dedup returns it
    force_regenerate: bool = False  # bypass dedup cache

class BriefingContent(BaseModel):
    """The LLM's structured output."""
    executive_summary: str = Field(..., description="3-5 sentence headline")
    body_markdown: str = Field(..., description="Full briefing as markdown")
    citations: list[Citation]
    investigations_referenced: list[str]
    alerts_referenced: list[str]
    metrics_covered: list[str]

class BriefingRunResult(BaseModel):
    briefing_id: str
    briefing_type: BriefingType
    scope_key: str
    status: str  # 'completed' / 'failed' / 'cached'
    was_cached: bool
    content: BriefingContent | None
    latency_seconds: float
    total_tokens: int | None = None
    cost_usd: float | None = None
    trace_url: str | None = None
    error: str | None = None
```

No tests required for this prompt — pure schema + prompt definition.

Acceptance criteria:
1. All schemas importable from clubos2.briefer.agent_schemas
2. BriefingContent.model_json_schema() produces clean output usable as structured output target
3. prompts/briefer_v1.md is fully written with all sections above

Verify before next prompt: read briefer_v1.md aloud. Does the "How to distinguish CAUSED vs CORRELATED" rule sound like something a senior data analyst would say? If yes, ship. If it sounds vague, tighten with more explicit language.
```

---

# Stage 2 — Briefer orchestrator (2 prompts)

## Prompt 5.2.1 — Briefer input assembly (reading from investigations + agent_memory)

```
Build the input-assembly layer that fetches all the source data the Briefer LLM will need to compose a briefing. This is pure retrieval — no LLM calls here.

File: clubos2/briefer/input_assembly.py

The Briefer reads from three sources depending on briefing_type:

1. investigations table — the primary source (rich context: cause hypothesis, evidence, citations, reasoning trace)
2. agent_memory table — supplementary LTM (past alert patterns, recurring themes)
3. watchdog_alerts table — for alerts that occurred in the period but never got investigated (info-level alerts, deduped alerts)

```python
from pydantic import BaseModel
from datetime import datetime
from clubos2.investigator.repo import InvestigationRepository
from clubos2.investigator.schema import InvestigationRead
from clubos2.watchdog.alerts_repo import AlertsRepository
from clubos2.watchdog.alerts_schema import WatchdogAlertRead
from clubos2.watchdog.memory_repo import AgentMemoryRepository, AgentMemoryRead

class BriefingSourceMaterial(BaseModel):
    """Everything the Briefer LLM needs, pre-fetched."""
    period_start: datetime
    period_end: datetime
    briefing_type: str
    scope_key: str

    # Primary source
    investigations: list[InvestigationRead]

    # Supplementary
    alerts_in_period: list[WatchdogAlertRead]
    memory_entries: list[AgentMemoryRead]

    # Aggregates (computed here, not by LLM)
    total_investigations: int
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    metrics_investigated: list[str]  # unique metric names
    persistent_metrics: list[str]    # metrics that appeared multiple times

async def assemble_source_material(
    briefing_type: str,
    scope_key: str,
    period_start: datetime,
    period_end: datetime,
    investigations_repo: InvestigationRepository,
    alerts_repo: AlertsRepository,
    memory_repo: AgentMemoryRepository,
) -> BriefingSourceMaterial:
    """
    Fetch all source data needed for a briefing. Pure retrieval, no LLM.

    Routing:
    - MONTHLY_SCHEDULED: fetch all completed investigations + all critical alerts
      in the period; agent_memory entries for the period
    - AD_HOC_SUMMARY: same as monthly but respecting user-specified filters
      (encoded in scope_key)
    - METRIC_FOCUS: filter investigations by metric_name; only alerts/memories
      for that metric
    - INCIDENT_RECAP: single alert_id; fetch its investigation(s), the alert
      itself, and related memories

    Aggregates are computed here (not by the LLM):
    - Total investigation count
    - Confidence distribution
    - Unique metrics investigated
    - Persistent metrics (appearing in 3+ investigations)
    """
```

Implementation details:

For MONTHLY_SCHEDULED:
1. Investigations: `investigations_repo.list_recent(limit=100, since=period_start, status=COMPLETED)` filtered to `<= period_end`
2. Alerts: `alerts_repo.list_recent(limit=200, since=period_start, severity=CRITICAL)` filtered to `<= period_end`
3. Memory entries: query `agent_memory` for entries where `occurred_at` between period_start and period_end

For METRIC_FOCUS (scope_key = `metric:{name}:last_{N}d`):
1. Parse scope_key to extract metric_name and window
2. Fetch investigations filtered by metric_name in the last N days
3. Fetch alerts filtered by metric_name
4. Fetch memory entries with subject_key starting with `{metric_name}::`

For INCIDENT_RECAP (scope_key = `incident:{alert_id}`):
1. Fetch the specific alert
2. Fetch all investigations linked to that alert_id
3. Fetch memory entries with that alert_id in subject_metadata

Aggregate computation:
```python
def compute_aggregates(investigations: list[InvestigationRead]) -> dict:
    metric_counts = {}
    for inv in investigations:
        metric_counts[inv.metric_name] = metric_counts.get(inv.metric_name, 0) + 1

    return {
        "total_investigations": len(investigations),
        "high_confidence_count": sum(1 for i in investigations if i.confidence == "high"),
        "medium_confidence_count": sum(1 for i in investigations if i.confidence == "medium"),
        "low_confidence_count": sum(1 for i in investigations if i.confidence == "low"),
        "metrics_investigated": list(set(i.metric_name for i in investigations)),
        "persistent_metrics": [m for m, c in metric_counts.items() if c >= 3],
    }
```

Tests in tests_v2/test_briefer_input_assembly.py:
- MONTHLY_SCHEDULED scope: fetches investigations + alerts + memories in period
- METRIC_FOCUS scope: filters correctly by metric_name
- INCIDENT_RECAP scope: fetches only investigations linked to the alert_id
- Aggregates computed correctly (test with 5 investigations covering 3 metrics with counts 3/1/1 → persistent_metrics=[metric_1])
- Empty period returns valid BriefingSourceMaterial with zero counts (not an error)

Critical constraints:
- No LLM calls in this file. Pure retrieval and aggregation.
- Every retrieval respects the period boundaries. A briefing for March 2026 must not include April data.
- If a source (investigations, alerts, memory) is empty for the period, that's valid — the Briefer LLM will handle "no investigations occurred" cases.
- Aggregates are computed deterministically. The LLM does not count. This is the deterministic-first principle applied to briefing composition.

Acceptance criteria:
1. `assemble_source_material` runs against real Phase 4 investigations and returns BriefingSourceMaterial
2. Aggregate counts match direct SQL queries
3. Filter logic works for all four briefing_types
4. Tests pass

Verify before next prompt: manually run assembly for a monthly scope covering the last 30 days. Print the summary. Does the aggregate metric count make sense given what you know is in the DB?
```

## Prompt 5.2.2 — Briefer orchestrator with dedup cache

```
Build the Briefer orchestrator: the top-level function that composes a briefing end-to-end. Includes the dedup cache check as the FIRST step — before any LLM call.

File: clubos2/briefer/orchestrator.py

The critical design point: dedup FIRST, generate SECOND. If a fresh briefing exists for the scope, return it without any LLM call. This is what makes the dedup cache economical — repeated queries about the same period are near-free.

```python
import json
import logging
import time
from uuid import uuid4
from datetime import datetime, timedelta
from pydantic import BaseModel

from clubos2.briefer.agent_schemas import BriefingInput, BriefingContent, BriefingRunResult, BriefingType
from clubos2.briefer.repo import BriefingRepository
from clubos2.briefer.input_assembly import assemble_source_material, BriefingSourceMaterial
from clubos2.investigator.repo import InvestigationRepository
from clubos2.watchdog.alerts_repo import AlertsRepository
from clubos2.watchdog.memory_repo import AgentMemoryRepository
from clubos2.gateway.client import GatewaySettings
from clubos2.observability.tracing import traced, get_current_langsmith_trace_url
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

@traced(name="briefer:run", run_type="chain")
async def run_briefing(input: BriefingInput) -> BriefingRunResult:
    """
    Run one briefing end-to-end.

    Pipeline:
    0. DEDUP CHECK — look for a fresh briefing matching scope_key. If found and
       force_regenerate is False, return it as cached.
    1. Assemble source material from investigations, alerts, memory
    2. Start briefings row with status='generating'
    3. Load briefer_v1.md prompt
    4. Format the source material into an LLM-consumable input
    5. Call the LLM with structured output (BriefingContent schema)
    6. Persist the briefing to the briefings table
    7. Return BriefingRunResult
    """
    started_at = time.perf_counter()

    briefings_repo = BriefingRepository(session_factory=...)
    investigations_repo = InvestigationRepository(session_factory=...)
    alerts_repo = AlertsRepository(session_factory=...)
    memory_repo = AgentMemoryRepository(session_factory=...)

    # STEP 0 — Dedup cache check
    if not input.force_regenerate:
        cached = await briefings_repo.find_fresh(
            scope_key=input.scope_key,
            max_age_days=input.freshness_days,
        )
        if cached is not None:
            logger.info(f"Returning cached briefing {cached.briefing_id} for scope {input.scope_key}")
            return BriefingRunResult(
                briefing_id=cached.briefing_id,
                briefing_type=BriefingType(cached.briefing_type),
                scope_key=cached.scope_key,
                status="cached",
                was_cached=True,
                content=BriefingContent(
                    executive_summary=cached.executive_summary,
                    body_markdown=cached.body_markdown,
                    citations=[Citation.model_validate(c) for c in json.loads(cached.citations)],
                    investigations_referenced=json.loads(cached.investigations_referenced),
                    alerts_referenced=json.loads(cached.alerts_referenced),
                    metrics_covered=json.loads(cached.metrics_covered),
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
        # Don't even start the briefings row if we can't assemble source
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
    from pathlib import Path
    system_prompt = Path("prompts/briefer_v1.md").read_text()

    # STEP 4 — Format source material into LLM input
    user_input = format_source_for_llm(source)

    # STEP 5 — LLM call with structured output
    try:
        llm = ChatOpenAI(
            model=GatewaySettings().briefer_model if hasattr(GatewaySettings(), 'briefer_model') else 'gpt-4o',
            temperature=0,
            max_tokens=4096,
        )
        structured_llm = llm.with_structured_output(BriefingContent)

        response = await structured_llm.ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ])

        content: BriefingContent = response

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
            total_tokens=None,  # TODO: extract from response metadata
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

def format_source_for_llm(source: BriefingSourceMaterial) -> str:
    """Convert BriefingSourceMaterial into a well-structured prompt for the Briefer LLM.

    Structure:
    - Period metadata (start, end, type)
    - Aggregates (deterministic counts)
    - Investigations block (each investigation as a formatted section with citations)
    - Alerts block (any alerts not linked to an investigation)
    - Memory block (recurring patterns from agent_memory)
    """
    parts = [
        f"# Briefing Input\n",
        f"**Period:** {source.period_start.date()} to {source.period_end.date()}",
        f"**Briefing type:** {source.briefing_type}",
        f"**Scope:** {source.scope_key}\n",
        f"## Aggregates (pre-computed, do not re-count)",
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
            parts.append(f"[source: investigations]")
            parts.append(f"- Metric: {inv.metric_name}")
            parts.append(f"- Alert: {inv.alert_id}")
            parts.append(f"- Confidence: {inv.confidence}")
            parts.append(f"- Hypothesis: {inv.cause_hypothesis}")
            parts.append(f"- Evidence: {inv.evidence_summary}\n")
    else:
        parts.append("## Investigations\n\nNo investigations concluded in this period.\n")

    if source.alerts_in_period:
        parts.append(f"## Alerts in period ({len(source.alerts_in_period)})\n")
        for alert in source.alerts_in_period[:20]:  # cap to avoid prompt bloat
            parts.append(
                f"- {alert.metric_name} ({alert.severity}): {alert.alert_type}, "
                f"rank {alert.current_rank} (was {alert.previous_rank}) "
                f"[source: watchdog_alerts]"
            )

    if source.memory_entries:
        parts.append(f"\n## Recurring patterns from agent_memory\n")
        # Summarise memories by subject_key
        memory_by_subject = {}
        for m in source.memory_entries:
            memory_by_subject.setdefault(m.subject_key, []).append(m)
        for subject, entries in memory_by_subject.items():
            parts.append(f"- {subject}: {len(entries)} occurrences [source: agent_memory]")

    return "\n".join(parts)
```

Critical constraints:
- Dedup check is STEP 0. Nothing before it. If cache hits, no LLM call happens.
- The dedup returned briefing has `status="cached"` and `was_cached=True` — this is how callers know they got a cache hit.
- `force_regenerate=True` bypasses cache. Used for testing and for explicit user "regenerate" requests.
- Errors at any stage produce a BriefingRunResult with status='failed', never an unhandled exception.
- The user_input to the LLM contains canonical source tags (`[source: investigations]`, `[source: watchdog_alerts]`, `[source: agent_memory]`) so citations in the LLM output can reference them cleanly.

Tests in tests_v2/test_briefer_orchestrator.py:
- Dedup cache hit: pre-populate a fresh briefing, call run_briefing with same scope → returns cached briefing without LLM call
- Dedup cache miss (fresh briefing exists but > freshness_days old): LLM is called, new briefing generated
- force_regenerate=True bypasses cache even when fresh exists
- Empty period (no investigations): briefing generates successfully with "no investigations" content
- LLM call failure: status='failed', error captured
- Source assembly failure: status='failed', briefing row NOT created

Acceptance criteria:
1. run_briefing works end-to-end against real Phase 4 investigations
2. Cache hit path returns without any OpenAI API call (verify no cost incurred)
3. LangSmith trace shows source assembly, LLM call, persistence as sub-spans
4. Tests pass

Verify before next prompt: run a MONTHLY_SCHEDULED briefing for the current month, then run it again immediately. Second call should return cached briefing with was_cached=True. Cost: one LLM call total for both. Then set force_regenerate=True and run a third time — should generate anew.
```

---

# Stage 3 — Hybrid supervisor (3 prompts)

## Prompt 5.3.1 — Rule-based classifier (the deterministic router)

```
Build the rule-based classifier that handles the 80% of queries that are obvious. This runs BEFORE any LLM-based supervisor decision. If the classifier confidently identifies the agent, it dispatches directly. If not, it falls through to the LangGraph supervisor (built in Prompt 5.3.2).

File: clubos2/supervisor/classifier.py

Principle: reach for the LLM last. If we can decide the agent with regex and semantic-layer lookups, we do that.

```python
import re
from pydantic import BaseModel
from enum import Enum

class AgentType(str, Enum):
    SCOUT = "scout"
    INVESTIGATOR = "investigator"
    BRIEFER = "briefer"
    UNKNOWN = "unknown"  # falls through to LangGraph supervisor

class ClassificationResult(BaseModel):
    agent: AgentType
    confidence: str  # 'high' / 'medium' / 'low'
    rule_matched: str | None
    reasoning: str
    extracted_params: dict = {}

def classify_query(query: str) -> ClassificationResult:
    """
    Classify a user query to route to the right agent using deterministic rules.

    Returns UNKNOWN if no rule matches with high confidence — caller then
    falls through to LangGraph supervisor.
    """
    q = query.strip().lower()

    # RULE 1 — Briefing requests
    briefing_patterns = [
        (r'\b(monthly briefing|monthly summary|month.{0,5} report)\b', 'monthly_briefing_keyword'),
        (r'\b(summar(y|ise|ize).{0,20}(month|week|period))\b', 'summary_of_period'),
        (r'\b(what happened.{0,20}(this month|last month|march|april))\b', 'what_happened_period'),
        (r'\b(brief(ing)?.{0,20}(me|us)?)\b', 'brief_keyword'),
    ]
    for pattern, name in briefing_patterns:
        if re.search(pattern, q):
            return ClassificationResult(
                agent=AgentType.BRIEFER,
                confidence="high",
                rule_matched=name,
                reasoning=f"Query matched briefing pattern: {name}",
                extracted_params={"raw_query": query},
            )

    # RULE 2 — Investigation requests
    investigation_patterns = [
        (r'\b(investigate|why did|why is|what caused)\b', 'why_causal_keyword'),
        (r'\b(root cause|explain.{0,20}alert)\b', 'root_cause_keyword'),
        (r'\balert.{0,10}(alrt_[a-f0-9]+)', 'explicit_alert_id'),
    ]
    for pattern, name in investigation_patterns:
        match = re.search(pattern, q)
        if match:
            params = {"raw_query": query}
            # Extract alert_id if present
            alert_match = re.search(r'alrt_[a-f0-9]+', query)
            if alert_match:
                params["alert_id"] = alert_match.group(0)
            return ClassificationResult(
                agent=AgentType.INVESTIGATOR,
                confidence="high" if params.get("alert_id") else "medium",
                rule_matched=name,
                reasoning=f"Query matched investigation pattern: {name}",
                extracted_params=params,
            )

    # RULE 3 — Metric questions (Scout)
    # If the query mentions a known metric from the registry, high confidence Scout
    known_metrics = _load_known_metric_names()  # cached
    for metric in known_metrics:
        # Match canonical name or common variations
        if metric.replace('_', ' ') in q or metric in q:
            return ClassificationResult(
                agent=AgentType.SCOUT,
                confidence="high",
                rule_matched="known_metric_referenced",
                reasoning=f"Query references known metric '{metric}'",
                extracted_params={"raw_query": query, "referenced_metric": metric},
            )

    # RULE 4 — Question shape suggesting Scout even without explicit metric
    scout_shape_patterns = [
        (r'\b(what is|what was|what are|how much|how many)\b', 'value_question_shape'),
        (r'\b(current|latest|most recent|this month)\b', 'current_value_shape'),
    ]
    for pattern, name in scout_shape_patterns:
        if re.search(pattern, q):
            return ClassificationResult(
                agent=AgentType.SCOUT,
                confidence="medium",
                rule_matched=name,
                reasoning=f"Query shape suggests Scout: {name}",
                extracted_params={"raw_query": query},
            )

    # RULE 5 — Fall through: no confident rule match
    return ClassificationResult(
        agent=AgentType.UNKNOWN,
        confidence="low",
        rule_matched=None,
        reasoning="No deterministic rule matched with confidence — deferring to LangGraph supervisor",
        extracted_params={"raw_query": query},
    )

def _load_known_metric_names() -> list[str]:
    """Load canonical metric names from metric_registry. Cached at module load."""
    import duckdb
    conn = duckdb.connect('var/clubos_semantic.duckdb', read_only=True)
    rows = conn.execute("SELECT canonical_name FROM metric_registry").fetchall()
    conn.close()
    return [r[0] for r in rows]
```

Tests in tests_v2/test_supervisor_classifier.py:
- "give me a monthly summary" → Briefer, high confidence
- "why did streaming_daily_users drop last week" → Investigator, medium confidence
- "why did alert alrt_abc123 fire" → Investigator, high confidence, alert_id extracted
- "what is streaming_daily_users this month" → Scout, high confidence
- "how is our conversion rate looking" → Scout, medium confidence
- "help me understand our business" → UNKNOWN (falls through)
- "compare last quarter to this quarter and tell me what changed and why" → UNKNOWN (complex multi-step, needs supervisor)

Critical constraints:
- Zero LLM calls in this classifier. All regex + database lookups.
- Order matters: briefing patterns first (they're most specific), then investigation, then metric, then question shape.
- Return UNKNOWN generously — better to defer to LangGraph supervisor than route wrong. False positives are worse than false negatives.
- Load metric names at module load (cache in memory). Don't hit DB on every classification.

Acceptance criteria:
1. classify_query returns in <10ms on average (measure over 100 sample queries)
2. All 7 test cases pass
3. Extracting alert_id from "why did alert alrt_abc123 fire" works
4. Metric name matching handles both `streaming_daily_users` and `streaming daily users` (underscore or space)

Verify before next prompt: hand-craft 20 sample queries covering all four categories. Classify each. Read the results. Are the confidence levels intuitive? If you disagree with any classification, tune the rules before continuing.
```

## Prompt 5.3.2 — LangGraph supervisor for complex queries

```
Build the LangGraph supervisor that handles queries the deterministic classifier couldn't route confidently. This is where LLM-based routing lives — for complex, multi-step, or ambiguous queries.

File: clubos2/supervisor/graph.py

The supervisor is itself an agent — a LangGraph state machine that routes to Scout, Investigator, and/or Briefer, potentially in sequence, then optionally synthesises the results.

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from clubos2.gateway.client import GatewaySettings

class SupervisorState(TypedDict):
    """State for the supervisor graph."""
    user_query: str
    messages: Annotated[list[BaseMessage], add_messages]
    plan: list[dict] | None  # list of {agent, params} steps
    step_index: int
    step_results: list[dict]  # accumulated results from each step
    final_synthesis: str | None
    finished: bool

class SupervisorPlan(BaseModel):
    """Structured output from the planner LLM."""
    reasoning: str
    steps: list["SupervisorStep"]

class SupervisorStep(BaseModel):
    agent: Literal["scout", "investigator", "briefer"]
    purpose: str  # human-readable description of why this step
    params: dict  # parameters to pass to the agent

SupervisorPlan.model_rebuild()

SUPERVISOR_SYSTEM_PROMPT = """You are the ClubOS Supervisor. A user has asked a complex query
that requires coordination between multiple specialist agents. Your job is to plan the sequence
of agent invocations needed to answer.

Available agents:
- SCOUT: answers factual questions about specific metrics. Use for "what is X", "how much is Y".
- INVESTIGATOR: investigates root causes of alerts. Use for "why did X happen", "root cause of Y".
- BRIEFER: composes summaries and briefings. Use for "summarise last month", "brief me on Q1".

Rules:
1. Prefer FEWER steps. Simple queries need one step. Only add steps if genuinely required.
2. If a query is truly simple (just a Scout question), plan just one Scout step. Do not
   over-orchestrate.
3. If a query needs both facts and explanation, plan Scout FIRST, then Investigator (which
   can consume the Scout's findings via context).
4. If a query asks for a period summary, plan a single Briefer step. Do NOT combine with
   Scout/Investigator — Briefer already reads investigations directly.
5. Maximum 3 steps. If you need more, the query is too complex — reject with reasoning.

Output must be a JSON object matching the SupervisorPlan schema."""

def planner_node(state: SupervisorState) -> dict:
    """Ask an LLM to produce a plan for handling the query."""
    llm = ChatOpenAI(model=GatewaySettings().supervisor_model if hasattr(GatewaySettings(), 'supervisor_model') else 'gpt-4o-mini', temperature=0)
    structured = llm.with_structured_output(SupervisorPlan)
    plan_result: SupervisorPlan = structured.invoke([
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=f"User query: {state['user_query']}\n\nProduce a plan."),
    ])
    return {
        "plan": [step.model_dump() for step in plan_result.steps],
        "step_index": 0,
    }

async def executor_node(state: SupervisorState) -> dict:
    """Execute the next step in the plan."""
    if state["plan"] is None or state["step_index"] >= len(state["plan"]):
        return {"finished": True}

    step = state["plan"][state["step_index"]]
    agent = step["agent"]
    params = step["params"]

    result = None
    try:
        if agent == "scout":
            from clubos2.agents.scout import run_scout
            from clubos2.agents.scout_schemas import ScoutInput
            answer = await run_scout(ScoutInput(question=params.get("question", state["user_query"])))
            result = {"agent": "scout", "output": answer.model_dump()}
        elif agent == "investigator":
            from clubos2.investigator.orchestrator import run_investigation
            from clubos2.investigator.agent_schemas import InvestigatorInput
            alert_id = params.get("alert_id")
            if not alert_id:
                # Cannot investigate without an alert_id; report and skip
                result = {"agent": "investigator", "error": "no alert_id provided", "output": None}
            else:
                inv_result = await run_investigation(InvestigatorInput(
                    alert_id=alert_id,
                    metric_name=params.get("metric_name", ""),
                    triggered_by="supervisor",
                ))
                result = {"agent": "investigator", "output": inv_result.model_dump()}
        elif agent == "briefer":
            from clubos2.briefer.orchestrator import run_briefing
            from clubos2.briefer.agent_schemas import BriefingInput, BriefingType
            brf_input = BriefingInput(
                briefing_type=BriefingType(params.get("briefing_type", "ad_hoc_summary")),
                scope_key=params.get("scope_key", f"adhoc:{state['user_query'][:100]}"),
                period_start=datetime.fromisoformat(params["period_start"]),
                period_end=datetime.fromisoformat(params["period_end"]),
                triggered_by="supervisor",
            )
            brf_result = await run_briefing(brf_input)
            result = {"agent": "briefer", "output": brf_result.model_dump()}
    except Exception as e:
        result = {"agent": agent, "error": str(e), "output": None}

    new_results = list(state["step_results"]) + [result]
    return {
        "step_results": new_results,
        "step_index": state["step_index"] + 1,
    }

def synthesis_node(state: SupervisorState) -> dict:
    """If multiple steps ran, synthesise into a coherent final answer.
    If only one step ran, skip synthesis (return the single result as-is)."""
    if len(state["step_results"]) <= 1:
        # Single step: no synthesis needed
        return {"finished": True, "final_synthesis": None}

    # Multi-step: synthesise
    llm = ChatOpenAI(model=GatewaySettings().supervisor_model if hasattr(GatewaySettings(), 'supervisor_model') else 'gpt-4o-mini', temperature=0)
    prompt = f"""The user asked: {state['user_query']}

The following specialist agents were invoked:
{json.dumps(state['step_results'], indent=2)}

Synthesise a coherent, cited answer for the user. Preserve all citations from the underlying
agents. Do not invent new facts. Keep response concise."""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_synthesis": response.content, "finished": True}

def should_continue(state: SupervisorState) -> str:
    if state.get("finished"):
        return "end"
    if state["plan"] is None:
        return "plan"
    if state["step_index"] >= len(state["plan"]):
        return "synthesise"
    return "execute"

def build_supervisor_graph():
    graph = StateGraph(SupervisorState)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("synthesis", synthesis_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_conditional_edges(
        "executor",
        lambda s: "executor" if s["step_index"] < len(s["plan"] or []) else "synthesis",
        {"executor": "executor", "synthesis": "synthesis"},
    )
    graph.add_edge("synthesis", END)

    return graph.compile()
```

Tests in tests_v2/test_supervisor_graph.py:
- Single Scout step plan: executes Scout, no synthesis
- Multi-step Scout+Investigator plan: executes both, synthesises
- Empty plan (LLM decides no steps needed): handles gracefully
- Executor failure on one step: continues to next step, error captured

Critical constraints:
- The supervisor is only invoked when the classifier returns UNKNOWN. Simple queries never reach here.
- Synthesis node is SKIPPED when only one step ran (that step's result is returned directly).
- Max plan length enforced in the planner prompt (3 steps).
- Every agent invocation preserves the underlying agent's citations and error handling.

Acceptance criteria:
1. build_supervisor_graph returns a compiled graph
2. Graph runs against a complex query (e.g., "compare last month's streaming performance to this month's and explain any big changes") and produces a coherent synthesised answer
3. Tests pass
4. LangSmith trace shows planner → executor(s) → synthesis as connected spans

Verify before next prompt: hand-craft 5 complex queries. Run each through the graph. Do the plans make sense? If the planner is producing dumb plans (e.g., using Briefer for a simple metric question), the planner prompt needs tightening.
```

## Prompt 5.3.3 — Unified supervisor entry point + Watchdog auto-trigger

```
Wire everything together: a single entry point that runs the classifier first, dispatches directly if confident, falls through to the LangGraph supervisor if not. Also add the Watchdog → Investigator auto-trigger for critical alerts.

Files to create:
- clubos2/supervisor/entry_point.py — unified dispatch
- Modify clubos2/watchdog/orchestrator.py — add auto-trigger hook

In clubos2/supervisor/entry_point.py:

```python
from pydantic import BaseModel
from datetime import datetime, timedelta
from clubos2.supervisor.classifier import classify_query, AgentType, ClassificationResult
from clubos2.supervisor.graph import build_supervisor_graph, SupervisorState
from clubos2.observability.tracing import traced, get_current_langsmith_trace_url

class SupervisorRequest(BaseModel):
    query: str
    user_id: str | None = None

class SupervisorResponse(BaseModel):
    query: str
    classification: dict  # ClassificationResult as dict
    dispatch_path: str  # 'direct_scout' / 'direct_investigator' / 'direct_briefer' / 'langgraph_supervisor'
    result: dict  # agent output
    latency_seconds: float
    trace_url: str | None
    error: str | None

@traced(name="supervisor:handle_query", run_type="chain")
async def handle_query(request: SupervisorRequest) -> SupervisorResponse:
    """
    Unified entry point. Classifies query, dispatches directly if confident,
    or invokes LangGraph supervisor for complex cases.
    """
    import time
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput
    from clubos2.briefer.orchestrator import run_briefing
    from clubos2.briefer.agent_schemas import BriefingInput, BriefingType

    started_at = time.perf_counter()

    # Step 1: Deterministic classification
    classification = classify_query(request.query)

    try:
        # Step 2: Direct dispatch if high-confidence classification
        if classification.agent == AgentType.SCOUT and classification.confidence in ("high", "medium"):
            answer = await run_scout(ScoutInput(question=request.query))
            return SupervisorResponse(
                query=request.query,
                classification=classification.model_dump(),
                dispatch_path="direct_scout",
                result=answer.model_dump(mode="json"),
                latency_seconds=time.perf_counter() - started_at,
                trace_url=get_current_langsmith_trace_url(),
                error=None,
            )

        if classification.agent == AgentType.INVESTIGATOR and classification.confidence == "high":
            alert_id = classification.extracted_params.get("alert_id")
            if alert_id:
                from clubos2.investigator.orchestrator import run_investigation
                from clubos2.investigator.agent_schemas import InvestigatorInput
                from clubos2.watchdog.alerts_repo import AlertsRepository
                alerts_repo = AlertsRepository(session_factory=...)
                alert = await alerts_repo.get_by_id(alert_id)
                if alert:
                    inv_result = await run_investigation(InvestigatorInput(
                        alert_id=alert_id,
                        metric_name=alert.metric_name,
                        triggered_by=f"supervisor:{request.user_id or 'unknown'}",
                    ))
                    return SupervisorResponse(
                        query=request.query,
                        classification=classification.model_dump(),
                        dispatch_path="direct_investigator",
                        result=inv_result.model_dump(mode="json"),
                        latency_seconds=time.perf_counter() - started_at,
                        trace_url=get_current_langsmith_trace_url(),
                        error=None,
                    )
            # No explicit alert_id and only medium confidence → fall through to LangGraph

        if classification.agent == AgentType.BRIEFER and classification.confidence == "high":
            # Direct briefing invocation with scope inferred from query
            brf_input = _infer_briefing_input_from_query(request.query, classification)
            brf_result = await run_briefing(brf_input)
            return SupervisorResponse(
                query=request.query,
                classification=classification.model_dump(),
                dispatch_path="direct_briefer",
                result=brf_result.model_dump(mode="json"),
                latency_seconds=time.perf_counter() - started_at,
                trace_url=get_current_langsmith_trace_url(),
                error=None,
            )

        # Step 3: Fall through to LangGraph supervisor
        graph = build_supervisor_graph()
        initial_state: SupervisorState = {
            "user_query": request.query,
            "messages": [],
            "plan": None,
            "step_index": 0,
            "step_results": [],
            "final_synthesis": None,
            "finished": False,
        }
        final_state = await graph.ainvoke(initial_state)
        return SupervisorResponse(
            query=request.query,
            classification=classification.model_dump(),
            dispatch_path="langgraph_supervisor",
            result={
                "plan": final_state.get("plan"),
                "step_results": final_state.get("step_results"),
                "final_synthesis": final_state.get("final_synthesis"),
            },
            latency_seconds=time.perf_counter() - started_at,
            trace_url=get_current_langsmith_trace_url(),
            error=None,
        )
    except Exception as e:
        return SupervisorResponse(
            query=request.query,
            classification=classification.model_dump(),
            dispatch_path="error",
            result={},
            latency_seconds=time.perf_counter() - started_at,
            trace_url=get_current_langsmith_trace_url(),
            error=str(e),
        )

def _infer_briefing_input_from_query(query: str, classification: ClassificationResult) -> BriefingInput:
    """Best-effort inference of briefing scope from the query text."""
    import re
    now = datetime.utcnow()

    # Check for "last month" / "this month" / specific months
    if re.search(r'last month', query, re.I):
        # Previous calendar month
        first_of_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_of_prev = first_of_this - timedelta(seconds=1)
        first_of_prev = last_of_prev.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return BriefingInput(
            briefing_type=BriefingType.MONTHLY_SCHEDULED,
            scope_key=f"monthly:{first_of_prev.strftime('%Y-%m')}",
            period_start=first_of_prev,
            period_end=last_of_prev,
            triggered_by="supervisor:query_inferred",
        )
    else:
        # Default: this month so far
        first_of_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return BriefingInput(
            briefing_type=BriefingType.MONTHLY_SCHEDULED,
            scope_key=f"monthly:{first_of_this.strftime('%Y-%m')}",
            period_start=first_of_this,
            period_end=now,
            triggered_by="supervisor:query_inferred",
        )
```

Modify clubos2/watchdog/orchestrator.py — add auto-trigger for critical alerts:

Find the section AFTER alerts are persisted (step 7 in the original pipeline). Add:

```python
# NEW: Auto-trigger Investigator on critical alerts
from clubos2.investigator.orchestrator import run_investigation
from clubos2.investigator.agent_schemas import InvestigatorInput

for alert in persisted:
    if alert.severity == AlertSeverity.CRITICAL:
        try:
            # Fire-and-forget: don't block the Watchdog on Investigator completion
            import asyncio
            asyncio.create_task(run_investigation(InvestigatorInput(
                alert_id=alert.alert_id,
                metric_name=alert.metric_name,
                triggered_by="watchdog:auto_trigger",
            )))
            logger.info(f"Auto-triggered Investigator for critical alert {alert.alert_id}")
        except Exception as e:
            # Auto-trigger failure must not fail the Watchdog run
            logger.warning(f"Failed to auto-trigger Investigator for {alert.alert_id}: {e}")
```

The auto-trigger is fire-and-forget. The Watchdog run completes normally. The Investigator runs in the background. If Investigator fails, only the Watchdog logs a warning — Watchdog persistence is not blocked.

Tests in tests_v2/test_supervisor_entry_point.py:
- "what is streaming_daily_users" → direct_scout dispatch, no LangGraph invocation
- "why did alert alrt_abc123 fire" → direct_investigator dispatch with alert_id parsed
- "monthly summary" → direct_briefer dispatch
- "compare last quarter to this quarter and explain what changed" → langgraph_supervisor dispatch
- Watchdog run producing a critical alert triggers Investigator background task

Critical constraints:
- Deterministic classification runs FIRST, unconditionally. LangGraph only fires if classifier is UNKNOWN or low confidence.
- The dispatch_path field is critical for observability — it tells you at a glance whether a query went through the fast deterministic path or the slower LLM-orchestrated path.
- Watchdog auto-trigger is fire-and-forget. The Watchdog does not wait for the Investigator to complete.
- Auto-trigger failures never crash the Watchdog.
- Every path goes through the same LangSmith trace so end-to-end visibility is preserved.

Acceptance criteria:
1. handle_query works for all four dispatch paths
2. Watchdog auto-triggers Investigator on critical alerts
3. LangSmith trace shows dispatch decision
4. Tests pass
5. All previous phase tests still pass

Verify before next prompt: manually run 5 different queries through handle_query — one clear Scout, one clear Investigator, one clear Briefer, one complex, one ambiguous. Print the dispatch_path for each. Do they match expectations?
```

---

# Stage 4 — API endpoints + scheduled briefing (2 prompts)

## Prompt 5.4.1 — Supervisor and Briefer API endpoints

```
Add API endpoints for the supervisor entry point and for direct Briefer invocation (for the scheduled cron path).

Files to CREATE:
- BACKEND/api/app/routers/supervisor.py
- BACKEND/api/app/routers/briefer.py

Modify BACKEND/api/app/main.py to register both.

In BACKEND/api/app/routers/supervisor.py:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from clubos2.supervisor.entry_point import handle_query, SupervisorRequest, SupervisorResponse

router = APIRouter(prefix="/api/ai/supervisor", tags=["ai", "supervisor"])

class UnifiedQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    user_id: str | None = None

@router.post("/query", response_model=SupervisorResponse)
async def unified_query(request: UnifiedQueryRequest) -> SupervisorResponse:
    """Single entry point for all natural-language queries.

    Uses deterministic classifier for obvious cases (fast path), LangGraph
    supervisor for complex cases (slower but more capable).

    Returns the underlying agent's output plus dispatch metadata."""
    try:
        return await handle_query(SupervisorRequest(query=request.query, user_id=request.user_id))
    except Exception:
        raise HTTPException(status_code=500, detail="Supervisor query failed")
```

In BACKEND/api/app/routers/briefer.py:

```python
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from clubos2.briefer.orchestrator import run_briefing
from clubos2.briefer.agent_schemas import BriefingInput, BriefingType, BriefingRunResult
from clubos2.briefer.repo import BriefingRepository

router = APIRouter(prefix="/api/ai/briefer", tags=["ai", "briefer"])

class BriefingRunRequest(BaseModel):
    briefing_type: str = Field(default="ad_hoc_summary")
    scope_key: str
    period_start: datetime
    period_end: datetime
    triggered_by: str = Field(default="manual")
    freshness_days: int = Field(default=7, ge=0, le=90)
    force_regenerate: bool = False

@router.post("/run", response_model=BriefingRunResult)
async def run_briefing_endpoint(request: BriefingRunRequest) -> BriefingRunResult:
    """Run a briefing manually. Dedup cache applies unless force_regenerate=True."""
    try:
        return await run_briefing(BriefingInput(
            briefing_type=BriefingType(request.briefing_type),
            scope_key=request.scope_key,
            period_start=request.period_start,
            period_end=request.period_end,
            triggered_by=request.triggered_by,
            freshness_days=request.freshness_days,
            force_regenerate=request.force_regenerate,
        ))
    except Exception:
        raise HTTPException(status_code=500, detail="Briefing generation failed")

@router.post("/run_monthly", response_model=BriefingRunResult)
async def run_monthly_briefing_endpoint(
    year_month: str | None = Query(default=None, description="YYYY-MM, defaults to last complete month"),
) -> BriefingRunResult:
    """Run a monthly briefing. Called by cron. Idempotent via scope_key + dedup cache.

    Example: POST /api/ai/briefer/run_monthly?year_month=2026-03 generates the
    March 2026 briefing. Repeated calls return the cached briefing."""
    from calendar import monthrange
    if year_month is None:
        now = datetime.utcnow()
        first_of_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_of_prev = first_of_this - timedelta(seconds=1)
        year_month = last_of_prev.strftime('%Y-%m')

    try:
        year, month = map(int, year_month.split('-'))
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail=f"Invalid year_month format: {year_month}")

    period_start = datetime(year, month, 1)
    last_day = monthrange(year, month)[1]
    period_end = datetime(year, month, last_day, 23, 59, 59)

    return await run_briefing(BriefingInput(
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key=f"monthly:{year_month}",
        period_start=period_start,
        period_end=period_end,
        triggered_by="scheduled_cron",
    ))

@router.get("", response_model=list[dict])
async def list_briefings(
    limit: int = 20,
    briefing_type: str | None = None,
):
    """List recent briefings."""
    repo = BriefingRepository(session_factory=...)
    briefings = await repo.list_recent(limit=limit, briefing_type=briefing_type)
    return [b.model_dump(mode="json") for b in briefings]

@router.get("/{briefing_id}", response_model=dict)
async def get_briefing(briefing_id: str):
    """Get one briefing by ID."""
    repo = BriefingRepository(session_factory=...)
    briefing = await repo.get_by_id(briefing_id)
    if briefing is None:
        raise HTTPException(status_code=404, detail=f"Briefing {briefing_id} not found")
    return briefing.model_dump(mode="json")
```

Modify BACKEND/api/app/main.py:
```python
from app.routers import supervisor, briefer
app.include_router(supervisor.router)
app.include_router(briefer.router)
```

Tests in tests_v2/test_api_supervisor_briefer.py: standard endpoint registration checks, happy path tests with mocked orchestrators.

Manual smoke test (documented):
```bash
curl -X POST http://localhost:8000/api/ai/supervisor/query \
  -H "Content-Type: application/json" \
  -d '{"query": "what is streaming daily users this month"}'

curl -X POST http://localhost:8000/api/ai/briefer/run_monthly?year_month=2026-03
```

Critical constraints:
- run_monthly is designed to be cron-invocable. Idempotent by design (dedup cache ensures repeated calls return cached briefing).
- Default period for run_monthly is "last complete calendar month" so a cron running on the 1st of each month generates the previous month's briefing.
- Supervisor query endpoint accepts arbitrary natural language.

Acceptance criteria:
1. All 4 endpoints work with real data
2. /docs shows the new endpoints
3. All earlier-phase endpoints still work
4. Tests pass

Verify before next prompt: run all three curl commands. Confirm each returns a coherent response. For run_monthly, run it twice and check that the second call returns was_cached=true.
```

## Prompt 5.4.2 — Cron script for scheduled monthly briefing

```
Create a standalone script that can be invoked by cron (or Cloud Scheduler in production) to trigger the monthly briefing on the 1st of each month.

File to CREATE: scripts/scheduled_monthly_briefing.py

```python
#!/usr/bin/env python3
"""
Scheduled monthly briefing runner. Invoked by cron on the 1st of each month.
Runs the briefing for the PREVIOUS complete calendar month.

Example crontab:
  0 6 1 * * cd /path/to/clubos && python scripts/scheduled_monthly_briefing.py

Idempotent: repeated runs on the same month return the cached briefing without
regenerating.

Exit codes:
  0 — success (either newly generated or returned from cache)
  1 — briefing generation failed
"""
import asyncio
import sys
import logging
from datetime import datetime, timedelta
from calendar import monthrange

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

async def main():
    from clubos2.briefer.orchestrator import run_briefing
    from clubos2.briefer.agent_schemas import BriefingInput, BriefingType

    # Compute last complete calendar month
    now = datetime.utcnow()
    first_of_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_of_prev = first_of_this - timedelta(seconds=1)
    year, month = last_of_prev.year, last_of_prev.month
    last_day = monthrange(year, month)[1]

    year_month = f"{year:04d}-{month:02d}"
    scope_key = f"monthly:{year_month}"

    logger.info(f"Running scheduled monthly briefing for {year_month} (scope: {scope_key})")

    input = BriefingInput(
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key=scope_key,
        period_start=datetime(year, month, 1),
        period_end=datetime(year, month, last_day, 23, 59, 59),
        triggered_by="scheduled_cron",
        freshness_days=7,
    )

    result = await run_briefing(input)

    if result.status == "cached":
        logger.info(f"Briefing already generated (cached): {result.briefing_id}")
        return 0
    if result.status == "completed":
        logger.info(f"Briefing generated: {result.briefing_id} (latency: {result.latency_seconds:.1f}s)")
        return 0
    logger.error(f"Briefing failed: {result.error}")
    return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

Make the script executable:
```bash
chmod +x scripts/scheduled_monthly_briefing.py
```

Add documentation to scripts/README.md (create if it doesn't exist):

```markdown
# ClubOS Scheduled Scripts

## scheduled_monthly_briefing.py

Runs the Briefer for the previous complete calendar month. Designed for cron invocation on the 1st of each month.

**Example crontab entry:**
```
0 6 1 * * cd /path/to/clubos && /path/to/venv/bin/python scripts/scheduled_monthly_briefing.py >> /var/log/clubos_monthly.log 2>&1
```

**Idempotent:** repeated runs return the cached briefing.

**Production deployment:** in GCP Cloud Run, wrap this in a Cloud Scheduler job that hits `/api/ai/briefer/run_monthly` instead of invoking the script directly. The API endpoint has the same dedup behavior.
```

Manual test:
```bash
python scripts/scheduled_monthly_briefing.py
```
Expect: briefing generated (or returned from cache if run recently). Exit code 0.

Critical constraints:
- The script is idempotent. Running it twice on the same day is safe.
- Errors exit with code 1 (so cron alerts can fire).
- Success exit with code 0 whether newly generated or cached (both are valid outcomes).
- Log to stdout (cron collects), also to a rotating log file in production.

Acceptance criteria:
1. Script runs and generates a briefing (or returns cached)
2. Exit code is correct for success and failure paths
3. Second run of the same day returns cached (verify via logs)

Verify before next prompt: run the script twice. First should generate, second should return cached. Check the DB — only one briefings row created.
```

---

# Stage 5 — Evals + Phase 5 completion (5 prompts)

## Prompt 5.5.1 — Golden set expansion to 70 questions

```
Expand the golden set from 40 visible (Phase 4) to 60 visible by adding 20 new questions: 10 supervisor routing scenarios and 10 Briefer scenarios. Holdout stays at 10 questions.

Files to create:
- eval/golden/golden_set_v4.yaml (60 visible entries)

The v4 file contains all 40 v3 entries PLUS 20 new. Keep v3 in the repo. Default now bumps to v4.

New question types:

```python
class QuestionType(str, Enum):
    # ... existing types ...
    SUPERVISOR_ROUTING = "supervisor_routing"  # NEW: tests supervisor's dispatch decisions
    BRIEFER_RUN = "briefer_run"                # NEW: tests Briefer's briefing output
```

The 10 new SUPERVISOR_ROUTING questions (gq_041 through gq_050):

- gq_041 — "what is streaming_daily_users this month" — expected dispatch: direct_scout
- gq_042 — "monthly summary of March 2026" — expected dispatch: direct_briefer
- gq_043 — "why did alert alrt_X fire" (with real alert_id) — expected: direct_investigator
- gq_044 — "how are things this quarter" — expected: langgraph_supervisor (complex/ambiguous)
- gq_045 — "compare last month to this month and explain the differences" — expected: langgraph_supervisor with multi-step plan
- gq_046 — "brief me on last week's investigations" — expected: direct_briefer with scope_key including week window
- gq_047 — "what caused the recent drop in net_sales" — expected: direct_investigator
- gq_048 — "give me an overview of the top metrics" — expected: direct_scout or langgraph
- gq_049 — "show me all alerts and investigations for streaming_daily_users this month" — expected: langgraph with multi-step
- gq_050 — "I don't know what to look at right now, help me" — expected: langgraph or ambiguous handling

For SUPERVISOR_ROUTING entries, expected_answer_facts includes strings like:
- "dispatch_path=direct_scout"
- "classification.confidence=high"
- Or "dispatch_path=langgraph_supervisor" and "plan.steps>=2"

The 10 new BRIEFER_RUN questions (gq_051 through gq_060):

- gq_051 — Monthly briefing for a period with 3 investigations, all HIGH confidence — expected facts about content structure and citation count
- gq_052 — Monthly briefing for a period with 0 investigations — expected: briefing generated with "no critical investigations" language, no fabricated content
- gq_053 — Metric-focused briefing on streaming_daily_users — expected: only references investigations about that metric
- gq_054 — Repeat request for same monthly scope within freshness window — expected: was_cached=true, same briefing_id returned
- gq_055 — Repeat with force_regenerate=true — expected: was_cached=false, new briefing_id
- gq_056 — Incident recap for a specific alert — expected: single-alert focused, references linked investigation
- gq_057 — Briefing with mix of confidence levels — expected: language distinguishes HIGH/MEDIUM/LOW appropriately
- gq_058 — Briefing where the LLM might over-generalize (2 unrelated investigations) — expected: no invented "theme" connecting them
- gq_059 — Briefing with persistent metrics — expected: mentions the pattern with proper source citations
- gq_060 — Briefing referenced by scope_key that has NO source material — expected: valid briefing generated with "no data" content, not an error

Update eval/golden/schema.py to add SUPERVISOR_ROUTING and BRIEFER_RUN to QuestionType.

Update the authoring guide (eval/golden/authoring_guide.md) to describe the two new question types and how to structure their scenario setup.

Tests: golden_set_v4.yaml loads successfully; distribution matches expected counts.

Acceptance criteria:
1. golden_set_v4.yaml has exactly 60 entries
2. 10 new SUPERVISOR_ROUTING + 10 new BRIEFER_RUN entries added
3. All new entries have expected_answer_facts populated with concrete assertions
4. Loader validates without error

Verify before next prompt: read 3 random SUPERVISOR_ROUTING entries and 3 random BRIEFER_RUN entries aloud. Do they specify concrete, checkable facts? If they're vague, tighten before continuing.
```

## Prompt 5.5.2 — Scorers for SUPERVISOR_ROUTING and BRIEFER_RUN

```
Build assertion-based scorers for the two new question types.

Files:
- clubos2/eval/supervisor_scorer.py
- clubos2/eval/briefer_scorer.py

The scorer pattern is the same as for WATCHDOG_RUN and INVESTIGATION: recreate the scenario, run the agent, check expected_answer_facts against the result.

In supervisor_scorer.py:

```python
async def run_supervisor_scenario(entry: GoldenEntry) -> ScenarioResult:
    """Run the query through handle_query, check dispatch_path and other assertions."""
    from clubos2.supervisor.entry_point import handle_query, SupervisorRequest

    result = await handle_query(SupervisorRequest(query=entry.question))

    facts_satisfied = []
    facts_failed = []
    for fact in entry.expected_answer_facts:
        if check_supervisor_fact(fact, result):
            facts_satisfied.append(fact)
        else:
            facts_failed.append(fact)

    return ScenarioResult(
        entry_id=entry.id,
        result=result.model_dump(mode="json"),
        facts_satisfied=facts_satisfied,
        facts_failed=facts_failed,
        overall_pass=len(facts_failed) == 0,
    )

def check_supervisor_fact(fact: str, result: SupervisorResponse) -> bool:
    """Parse fact strings like 'dispatch_path=direct_scout' or 'plan.steps>=2'.

    Supported patterns:
    - dispatch_path=<value>
    - classification.confidence=<value>
    - classification.agent=<value>
    - plan.steps>=<N>, plan.steps==<N>, plan.steps<=<N>
    - result.status=<value>
    - error=null (no error field)
    """
    # Implementation with regex parsing of the fact pattern
    ...
```

In briefer_scorer.py:

```python
async def run_briefer_scenario(entry: GoldenEntry) -> ScenarioResult:
    """Recreate scenario, run Briefer, check assertions."""
    # Each BRIEFER_RUN entry needs a scenario setup function that:
    # 1. Ensures the required investigations/alerts exist in the eval DB
    # 2. Constructs the appropriate BriefingInput
    # 3. Runs the Briefer
    # 4. Checks facts against BriefingRunResult
```

Register scenario setup functions per entry:

```python
BRIEFER_SCENARIOS = {
    "gq_051": setup_gq_051,  # 3 high-confidence investigations
    "gq_052": setup_gq_052,  # 0 investigations
    # etc.
}

async def setup_gq_051() -> BriefingInput:
    """3 investigations of high confidence in the test period."""
    # Insert 3 investigations into the eval investigations table
    # Return the BriefingInput to run
```

Update pipeline.py to dispatch SUPERVISOR_ROUTING and BRIEFER_RUN entries to their respective scorers.

Critical constraints:
- Same eval-DB isolation as WATCHDOG_RUN and INVESTIGATION scorers (var/clubos_watchdog_eval.duckdb)
- Setup functions clean state before running so eval is reproducible
- Assertion patterns are simple regex-based, same style as investigator_scorer.py

Acceptance criteria:
1. All 10 SUPERVISOR_ROUTING entries have working scorer paths
2. All 10 BRIEFER_RUN entries have scenario setup functions
3. Full pipeline runs against golden_set_v4 and completes all 60 visible entries

Verify before next prompt: run the full eval. Print counts by question type. Do all 60 entries score without errors?
```

## Prompt 5.5.3 — Full Phase 5 eval + baseline update

```
Run the full 60-question eval on scout v6 (or higher if further iteration happened), plus the 10-question holdout. Compare visible vs holdout. Update baseline if all clean.

Steps:

1. Run 3 back-to-back full evals on golden_set_v4:
   ```bash
   for i in 1 2 3; do
     python -m clubos2.eval.pipeline --golden v4 --skip-ragas --inter-question-sleep 2 2>&1 | tee eval/runs/phase5_verify_run_$i.log
   done
   ```

2. Extract metrics from all 3 runs, compute variance across the 3 runs on each of:
   - behavioural_pass_rate (across all 60 entries)
   - fabrication_incidence_rate
   - supervisor_routing_pass_rate (new, from SUPERVISOR_ROUTING entries)
   - briefer_run_pass_rate (new)

3. Run the holdout eval:
   ```bash
   python -m clubos2.eval.holdout_runner --inter-question-sleep 2
   ```

4. Compare visible vs holdout metrics. Delta on any metric > 0.10 = overfitting warning.

5. If all clean (variance ≤ 2pp across runs, no overfitting, fabrication = 0):
   - Promote median-of-3 to eval/reports/baseline.json
   - Update docs/phase5_completion.md with real numbers

6. If not clean, report and stop.

Verify:
- Full eval completes in reasonable time (with sleep=2, roughly 60 × 2 = 120 seconds pacing + LLM time)
- No infinite loops or hangs
- All 60 entries score

Acceptance criteria:
1. 3-run variance ≤ 2pp
2. Fabrication 0/60 in all 3 runs
3. Visible vs holdout delta ≤ 0.10 on all metrics
4. Baseline updated

If any check fails, do NOT update baseline. Report the specific failure.
```

## Prompt 5.5.4 — Phase 5 completion report + demo script

```
Write the Phase 5 completion report and end-to-end demo script.

File: docs/phase5_completion.md

Include:
- What was built (all deliverables checked)
- Verified facts (real measured numbers from the baseline)
- What was deliberately NOT done (Phase 6+ items)
- Known gaps deferred
- How to demo Phase 5 end-to-end
- Interview narrative

Include the interview narrative:

"Phase 5 was the system-inflection point. Before Phase 5 I had three components — Scout, Watchdog, Investigator — with point-to-point cross-agent integration. After Phase 5 they're orchestrated through a hybrid supervisor: deterministic classifier for the 80% of queries that are obvious, LangGraph supervisor for complex multi-step queries. Detection is arithmetic (rule-based classifier), reasoning is LLM (supervisor). Same principle as Watchdog-vs-Investigator, applied at the orchestration layer.

I added a Briefer agent that composes monthly executive briefings from investigations and alerts. It has a dedup cache — a briefings SQL table that stores every generated briefing and returns fresh matches without re-generating, keeping cost bounded. Scheduled monthly generation happens via a cron-invocable script that hits the same idempotent endpoint used on-demand.

I also added Watchdog → Investigator auto-trigger for critical alerts. Fire-and-forget; the Watchdog run persists alerts and immediately kicks off background investigation for anything critical. This closes the loop with v1's original stakeholder pitch — the monthly business review that used to take weeks is now generated automatically with cited, deterministic-first reasoning throughout."

File: scripts/v2_demo_phase5.sh — end-to-end bash demo covering:
1. Run Watchdog to produce alerts (critical alerts auto-trigger Investigator in background)
2. Wait for Investigator to complete
3. Ask supervisor a simple Scout question (direct dispatch)
4. Ask supervisor a complex query (LangGraph path)
5. Run monthly briefing
6. Run monthly briefing again (should be cached)
7. Check all outputs
```

## Prompt 5.5.5 — Phase 5 completion verification + commit

```
Verify Phase 5 is genuinely complete.

Checks:
1. All Phase 1-4 endpoints still respond correctly (regression check)
2. New endpoints all live: /api/ai/supervisor/query, /api/ai/briefer/run, /api/ai/briefer/run_monthly, /api/ai/briefer, /api/ai/briefer/{id}
3. Watchdog auto-trigger fires on critical alerts (verified via log inspection)
4. All Phase 5 tests pass
5. 3-run variance ≤ 2pp on golden_set_v4
6. Visible vs holdout delta ≤ 0.10
7. docs/phase5_completion.md written with real numbers
8. scripts/v2_demo_phase5.sh runs end-to-end without errors

If all checks pass:

```bash
git add clubos2/briefer/ clubos2/supervisor/ BACKEND/api/app/routers/supervisor.py BACKEND/api/app/routers/briefer.py BACKEND/api/app/main.py scripts/scheduled_monthly_briefing.py scripts/v2_demo_phase5.sh eval/golden/golden_set_v4.yaml eval/golden/schema.py clubos2/eval/supervisor_scorer.py clubos2/eval/briefer_scorer.py eval/reports/baseline.json docs/phase5_completion.md prompts/briefer_v1.md clubos2/watchdog/orchestrator.py
git commit -m "Phase 5: Briefer agent + hybrid supervisor + auto-trigger

Deliverables:
- Briefer agent with dedup cache (briefings SQL table)
- Hybrid supervisor: rule-based classifier + LangGraph for complex queries
- Watchdog → Investigator auto-trigger on critical alerts
- Scheduled monthly briefing via cron-invocable script
- Golden set expanded to 60 visible + 10 holdout
- Supervisor routing and Briefer run scorers
- Phase 5 completion report

3-run variance: <X>pp
Visible-vs-holdout delta: <X>
Fabrication: 0/60 across all 3 runs

Phase 6 (Slack + HITL) unblocked."
```

Report Phase 5 completion status. Ready for Phase 6 planning.
```

---

# Phase 5 done. What's next.

When all 14 prompts complete and Phase 5 is honestly all-green:
- Scout, Watchdog, Investigator, Briefer all orchestrated through a hybrid supervisor
- Deterministic routing for obvious queries, LLM routing for complex ones
- Monthly briefings generated automatically via cron
- Watchdog auto-triggers Investigator on critical alerts
- 60-question eval with holdout discipline continues

**Phase 6 (next):**
- Slack surface for briefings + alerts
- HITL approval flow for auto-triggered investigations
- Slash commands for supervisor queries

Phase 6 prompts generated after Phase 5 verification.