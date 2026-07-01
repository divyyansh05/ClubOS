# ClubOS 2.0 — Phase 3 Prompt Sequence

**Scope locked:**
- Watchdog Agent that watches the Priority Board top-N and detects rank-change anomalies
- Detection logic is DETERMINISTIC Python (not an LLM agent) — the senior pattern
- Alerts stored in a SQL `watchdog_alerts` table; exposed via `GET /api/ai/alerts`
- Manual trigger via `POST /api/ai/watchdog/run` (cron-replaceable in production)
- LTM alert deduplication via `agent_memory` table — "have I alerted on this in the last N days?"
- 10 new Watchdog-focused golden eval questions; golden set grows to 30

**Out of scope (deferred):**
- Slack delivery → Phase 6
- LangGraph STM checkpointer → Phase 4 (Investigator agent needs it; Watchdog does not)
- Background scheduler → infrastructure concern, manual trigger demos the logic
- Holdout set discipline → Phase 4 when 2+ agents make overfitting a real risk

**Why Phase 3's Watchdog is intentionally NOT an LLM agent.** The senior point from the ClubOS book and our prior conversations: detection is arithmetic, explanation is reasoning. Watchdog detects breaches (rank changes, threshold crossings) with plain Python. The Investigator (Phase 4) is the LLM agent that *explains* why a breach happened. Wrapping a comparison in an LLM is a junior tell — and reviewers in interviews look for exactly this distinction.

**How to use this file.** 12 prompts across 4 stages. Run in order. Each prompt's "Verify before next prompt" gate must pass. Commit once per prompt.

**Conventions inherited from Phase 1 + 2:**
- All new code in `clubos2/`
- Tests in `tests_v2/`
- New router files added inside `BACKEND/api/app/routers/` (the only v1 touch — same pattern as Phase 1 Prompt 4.3)
- Pydantic v2, async by default
- LangSmith traces everywhere
- Every guardrail from Phase 2 still applies

---

# Stage 1 — Alert data model + LTM memory (3 prompts)

The foundation: where alerts live, how deduplication works, the SQL schema that supports everything else.

## Prompt 3.1.1 — Watchdog alerts schema and persistence

```
Create the SQL schema and SQLAlchemy interface for the `watchdog_alerts` table. This is where every Watchdog detection lands.

Files to create:
- clubos2/watchdog/__init__.py
- clubos2/watchdog/alerts_schema.py — SQLAlchemy + Pydantic models
- clubos2/watchdog/migrations/001_create_watchdog_alerts.sql — raw SQL migration
- clubos2/watchdog/alerts_repo.py — repository pattern for alerts

Table specification: `watchdog_alerts`

| Column | Type | Constraint | Purpose |
|---|---|---|---|
| alert_id | VARCHAR(64) | PRIMARY KEY | Stable ID, format: 'alrt_{timestamp_hash}' |
| metric_name | VARCHAR(100) | NOT NULL | Which metric the alert is about (FK in spirit to metric_registry) |
| alert_type | VARCHAR(50) | NOT NULL CHECK | 'rank_jumped_into_top' / 'rank_dropped_significantly' / 'new_in_top_n' / 'persistent_top' |
| severity | VARCHAR(20) | NOT NULL CHECK | 'info' / 'warning' / 'critical' |
| current_rank | INTEGER | NOT NULL | Where the metric sits NOW on the Priority Board |
| previous_rank | INTEGER | NULL | Where it was on the previous Watchdog run (NULL if first time seen) |
| rank_delta | INTEGER | NULL | previous_rank - current_rank (positive = moved up the board) |
| score_current | FLOAT | NOT NULL | The 5-component priority score from gold_priority_board.csv |
| score_previous | FLOAT | NULL | Previous run's score for the same metric |
| triggered_by_rule | VARCHAR(100) | NOT NULL | Which detection rule fired (matches a rule name from the rules engine) |
| context_snapshot | TEXT | NOT NULL | JSON blob of the metric's row at detection time, for audit trail |
| source | VARCHAR(200) | NOT NULL | The CSV file or table the data came from |
| run_id | VARCHAR(64) | NOT NULL | Groups all alerts from a single Watchdog run |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | |
| acknowledged_at | TIMESTAMP | NULL | Set when a human marks the alert read (Phase 6 HITL hook) |
| acknowledged_by | VARCHAR(100) | NULL | |

Indexes:
- INDEX idx_metric_name ON (metric_name) — for "alerts for this metric"
- INDEX idx_run_id ON (run_id) — for "all alerts from this run"
- INDEX idx_created_at ON (created_at DESC) — for "recent alerts"

SQLAlchemy models in alerts_schema.py:
- Use SQLAlchemy 2.0 declarative style with Mapped[] annotations
- Pydantic v2 schemas: WatchdogAlertCreate, WatchdogAlertRead, AlertSeverity (Enum), AlertType (Enum)

Repository in alerts_repo.py:

```python
class AlertsRepository:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def create(self, alert: WatchdogAlertCreate) -> WatchdogAlertRead: ...

    async def create_batch(self, alerts: list[WatchdogAlertCreate]) -> list[WatchdogAlertRead]:
        """Insert multiple alerts in a single transaction (one Watchdog run = one batch)."""

    async def list_recent(
        self,
        limit: int = 50,
        since: datetime | None = None,
        metric_name: str | None = None,
        severity: AlertSeverity | None = None,
    ) -> list[WatchdogAlertRead]: ...

    async def get_by_run(self, run_id: str) -> list[WatchdogAlertRead]: ...

    async def acknowledge(self, alert_id: str, by_user: str) -> WatchdogAlertRead: ...
```

Critical constraints:
- Same dual-backend approach as Phase 1's semantic_layer: must work in Postgres AND DuckDB. No JSONB; use TEXT for context_snapshot.
- alert_id is generated by Python (not DB autoincrement) so it's stable across backends. Format: f"alrt_{uuid4().hex[:16]}"
- Migration is idempotent (CREATE TABLE IF NOT EXISTS).
- DATABASE_URL env var reuses the same DB as the semantic layer (DuckDB local default at ./var/clubos_semantic.duckdb). The watchdog_alerts and metric_registry tables live in the same DB file.

Tests in tests_v2/test_watchdog_alerts_repo.py:
- Create a single alert; assert the returned WatchdogAlertRead has populated created_at and alert_id
- create_batch with 5 alerts: assert all 5 are persisted, all share the same run_id
- list_recent with filters (since, metric_name, severity) returns the expected subset
- acknowledge sets both acknowledged_at and acknowledged_by

Acceptance criteria:
1. Migration runs idempotently against the existing DuckDB file
2. `duckdb var/clubos_semantic.duckdb -c "DESCRIBE watchdog_alerts"` shows all columns
3. The Phase 1 metric_registry table is UNAFFECTED — query it after migration to confirm
4. Tests pass
5. Existing Phase 1 + Phase 2 tests still pass (regression)

Verify before next prompt: insert 3 sample alerts via the repository in a Python REPL. Query them back. Confirm the context_snapshot field round-trips as valid JSON.
```

## Prompt 3.1.2 — Agent memory table for alert deduplication

```
Create the `agent_memory` table — the LTM layer that prevents Watchdog from spamming the same alert every run.

Files:
- clubos2/watchdog/memory_schema.py — SQLAlchemy + Pydantic models
- clubos2/watchdog/migrations/002_create_agent_memory.sql — raw SQL
- clubos2/watchdog/memory_repo.py — repository

Table specification: `agent_memory`

Generic enough to support future agents (Investigator, Briefer, Scout), not just Watchdog. The key insight from our prior discussion: this is a structured-facts LTM, NOT a vector store. Same senior pattern — embed unstructured text, look up structured facts.

| Column | Type | Constraint | Purpose |
|---|---|---|---|
| memory_id | VARCHAR(64) | PRIMARY KEY | 'mem_{hash}' |
| agent_name | VARCHAR(50) | NOT NULL | 'watchdog' / 'investigator' / 'briefer' / 'scout' |
| memory_type | VARCHAR(50) | NOT NULL | 'alert_fired' / 'investigation_concluded' / 'briefing_published' / 'decision_taken' |
| subject_key | VARCHAR(200) | NOT NULL | The thing being remembered. For Watchdog alerts: f"{metric_name}::{alert_type}" |
| subject_metadata | TEXT | NULL | JSON blob with extra context for the subject |
| occurred_at | TIMESTAMP | NOT NULL DEFAULT NOW() | When the remembered event happened |
| expires_at | TIMESTAMP | NULL | If set, this memory is "stale" after this time (for deduplication windows) |
| confidence | FLOAT | NULL | If the memory is a decision/conclusion, how sure the agent was |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | |

Indexes:
- INDEX idx_agent_subject ON (agent_name, subject_key)
- INDEX idx_occurred_at ON (occurred_at DESC)
- INDEX idx_expires_at ON (expires_at) WHERE expires_at IS NOT NULL

Repository in memory_repo.py:

```python
class AgentMemoryRepository:
    async def remember(
        self,
        agent_name: str,
        memory_type: str,
        subject_key: str,
        subject_metadata: dict | None = None,
        ttl: timedelta | None = None,
        confidence: float | None = None,
    ) -> AgentMemoryRead:
        """Record an event. If ttl provided, expires_at = now + ttl."""

    async def has_recent(
        self,
        agent_name: str,
        subject_key: str,
        within: timedelta,
    ) -> bool:
        """True if there's a non-expired memory with this subject in the last `within` window.
        This is the deduplication primitive."""

    async def last_seen(
        self,
        agent_name: str,
        subject_key: str,
    ) -> AgentMemoryRead | None:
        """Return the most recent memory matching this subject, or None."""

    async def purge_expired(self) -> int:
        """Delete memories where expires_at < now. Called as part of Watchdog run cleanup."""
```

Why this design specifically (worth noting in code comments):
- `subject_key` is a STRING, not a foreign key. It's a flexible identifier each agent defines. For Watchdog it's f"{metric_name}::{alert_type}"; for future Investigator it might be f"investigation::{alert_id}".
- TTL-based expiry means deduplication windows are configurable per use case. "Don't alert on this metric again for 7 days" = remember with ttl=7d.
- `purge_expired` is called once per Watchdog run (cleanup hygiene); also safe to call on a schedule independently.

Tests in tests_v2/test_agent_memory_repo.py:
- remember → has_recent returns True within the TTL window
- has_recent returns False after the TTL window expires (use freezegun or pass an explicit `as_of` parameter for testability)
- has_recent returns False for a different agent_name even with the same subject_key (memory is scoped per agent)
- purge_expired removes only memories with expires_at < now
- last_seen returns the most recent matching memory

Critical constraints:
- This is the ONLY memory infrastructure built in Phase 3. STM (within-session state via LangGraph checkpointer) is deferred to Phase 4 where the Investigator needs it.
- Generic enough to be reused by all future agents. Document in code comments: "DO NOT add per-agent columns; use subject_metadata JSON for agent-specific data."
- TTL handling must be timezone-aware. All timestamps stored UTC. Document this.

Acceptance criteria:
1. Migration runs idempotently
2. `duckdb var/clubos_semantic.duckdb -c "DESCRIBE agent_memory"` shows all columns
3. The remember → has_recent → wait → has_recent flow works as expected
4. Tests pass (use freezegun for time manipulation)
5. Phase 1 and Phase 2 tests still pass

Verify before next prompt: in a Python REPL, do:
- remember(agent="watchdog", subject_key="streaming_daily_users::new_in_top_n", ttl=7 days)
- has_recent(agent="watchdog", subject_key="streaming_daily_users::new_in_top_n", within=10 days) → True
- has_recent(agent="watchdog", subject_key="streaming_daily_users::new_in_top_n", within=1 hour) → False (depending on when you remember()d it; this one is the "within window is too tight" case)
- has_recent(agent="investigator", subject_key="streaming_daily_users::new_in_top_n", within=10 days) → False (different agent)

Confirm the agent-scoping works correctly. This is critical — Watchdog's memories must not leak into other agents' deduplication logic.
```

## Prompt 3.1.3 — Priority Board snapshot reader

```
Build the data-access layer that reads the current and historical Priority Board state. Watchdog needs to compare "this run" to "the previous run" — that requires snapshot retrieval.

File: clubos2/watchdog/priority_board_reader.py

The Priority Board lives in DATA/gold_snapshots/gold_priority_board.csv. In v1's dev mode, this CSV is updated periodically (monthly in production). For Phase 3, we treat each Watchdog run as taking a SNAPSHOT of the current CSV state and storing the previous snapshot for diffing.

```python
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import pandas as pd

class PriorityBoardRow(BaseModel):
    metric_name: str
    business_name: str
    rank: int
    score: float
    severity_component: float
    persistence_component: float
    peer_gap_component: float
    commercial_component: float
    evidence_component: float
    source: str  # always 'DATA/gold_snapshots/gold_priority_board.csv'
    snapshot_time: datetime

class PriorityBoardSnapshot(BaseModel):
    snapshot_id: str        # 'snap_{timestamp_hash}'
    captured_at: datetime
    rows: list[PriorityBoardRow]
    source_path: str
    row_count: int

class PriorityBoardReader:
    def __init__(self, csv_path: str = "DATA/gold_snapshots/gold_priority_board.csv"):
        self.csv_path = Path(csv_path)

    async def read_current(self) -> PriorityBoardSnapshot:
        """Read the current state of the Priority Board CSV.
        Returns a snapshot — NOT persisted yet (that's the next prompt's job)."""

    async def diff_against_previous(
        self,
        current: PriorityBoardSnapshot,
        previous: PriorityBoardSnapshot | None,
    ) -> list["PriorityBoardDiff"]:
        """Compute per-metric changes between two snapshots.
        Returns a list of diffs, one per metric that exists in either snapshot."""
```

Diff model:

```python
class PriorityBoardDiff(BaseModel):
    metric_name: str
    business_name: str

    # Current state
    current_rank: int | None        # None if metric dropped off the board
    current_score: float | None

    # Previous state
    previous_rank: int | None       # None if metric is new to the board
    previous_score: float | None

    # Computed deltas
    rank_delta: int | None          # previous_rank - current_rank; positive = moved up
    score_delta: float | None       # current_score - previous_score

    # Classifications (set by the diff function)
    is_new_in_top_n: bool           # appeared in top N for the first time
    is_dropped_out: bool            # was in top N, now isn't
    is_persistent: bool             # in top N this run AND previous N runs (separate query)
```

Implementation notes:
- read_current: pandas read_csv with type coercion; validate the expected columns are present; raise PriorityBoardSchemaError if not
- diff_against_previous: handle three cases per metric — present in both (compute deltas), only current (is_new_in_top_n=true), only previous (is_dropped_out=true)
- The "top N" threshold defaults to 10 but is configurable (env or config object)

Add snapshot persistence to clubos2/watchdog/snapshot_repo.py:

```python
class PriorityBoardSnapshotRepository:
    """Persists snapshots so Watchdog can diff current vs previous run."""

    async def save(self, snapshot: PriorityBoardSnapshot) -> str:
        """Store as JSON in the priority_board_snapshots table.
        Schema (simple):
          snapshot_id PRIMARY KEY, captured_at TIMESTAMP, source_path TEXT, rows_json TEXT
        Returns the snapshot_id."""

    async def get_latest(self) -> PriorityBoardSnapshot | None:
        """Return the most recent saved snapshot, or None if no snapshots exist yet."""

    async def get_previous(self, before_snapshot_id: str) -> PriorityBoardSnapshot | None:
        """The snapshot immediately before the given one (for diffing)."""

    async def prune_older_than(self, days: int = 90) -> int:
        """Delete snapshots older than N days. Storage hygiene; return count deleted."""
```

Add SQL migration: migrations/003_create_priority_board_snapshots.sql with the obvious schema (id, captured_at, source_path, rows_json TEXT, created_at).

Tests in tests_v2/test_priority_board_reader.py:
- read_current returns a snapshot with at least 10 rows from the real DATA/gold_snapshots/gold_priority_board.csv
- diff with previous=None marks every row as is_new_in_top_n=True
- diff with two synthetic snapshots correctly computes rank_delta and is_dropped_out
- save → get_latest round-trips correctly
- snapshot rows_json is valid JSON

Critical constraints:
- read_current MUST NOT modify the CSV. Read-only.
- The Watchdog's "previous run" is whichever snapshot was saved last — there's no notion of "skip a day." If a Watchdog run is missed, the next run compares to whatever the last saved snapshot was.
- Snapshot JSON serialization preserves all PriorityBoardRow fields including timestamps. Pydantic v2's model_dump_json handles this — verify with a round-trip test.

Acceptance criteria:
1. `await PriorityBoardReader().read_current()` returns a snapshot from the real CSV
2. The snapshot serialises to JSON and deserialises back to an equivalent object
3. Saving and retrieving via the repository works
4. diff_against_previous correctly classifies new/dropped/changed metrics
5. Tests pass

Verify before next prompt: run a manual diff. In a REPL, read the current snapshot, save it, modify the CSV slightly (or use a backed-up older version), read again, diff. Confirm the diffs are intuitive — if a metric moved from rank 5 to rank 2, rank_delta should be 3 (positive = moved up).
```

---

# Stage 2 — Watchdog detection engine (3 prompts)

Pure Python, no LLM. This is the deterministic core.

## Prompt 3.2.1 — Detection rules engine

```
Build the detection rules engine. This is the heart of the Watchdog — a set of named rules, each a pure function that takes a PriorityBoardDiff and decides whether to fire an alert.

File: clubos2/watchdog/detection_rules.py

Why "rules engine" not "rules as LLM": each rule is a Python function with explicit logic. Same input always produces same alert. Reviewable, testable, auditable. Wrapping these in an LLM is the anti-pattern.

```python
from pydantic import BaseModel
from typing import Callable, Awaitable
from clubos2.watchdog.priority_board_reader import PriorityBoardDiff
from clubos2.watchdog.alerts_schema import WatchdogAlertCreate, AlertSeverity, AlertType

class DetectionResult(BaseModel):
    """Output of a single rule evaluating a single diff."""
    fired: bool
    rule_name: str
    alert: WatchdogAlertCreate | None = None
    reason: str  # human-readable explanation, included in alert if fired

class DetectionContext(BaseModel):
    """Context passed to rules — current snapshot metadata + config."""
    top_n: int = 10
    rank_jump_threshold: int = 5
    score_jump_threshold: float = 0.20
    persistence_threshold_runs: int = 3
    run_id: str

# A rule is a Callable[[PriorityBoardDiff, DetectionContext], DetectionResult]
# Sync, not async — rules are pure computation.
```

The Phase 3 rules to implement:

RULE 1 — `new_in_top_n`
- Fires when: diff.is_new_in_top_n AND diff.current_rank <= context.top_n
- Severity: 'warning' if current_rank > 5, 'critical' if <= 5
- alert_type: AlertType.NEW_IN_TOP_N
- Reason: f"{metric} entered the top {top_n} at rank {current_rank}"

RULE 2 — `rank_jumped_into_top`
- Fires when: previous_rank > top_n AND current_rank <= top_n AND NOT is_new_in_top_n
  (metric was on the board but outside top N, now inside)
- Severity: 'warning'
- alert_type: AlertType.RANK_JUMPED_INTO_TOP
- Reason: f"{metric} moved from rank {previous_rank} to {current_rank}"

RULE 3 — `large_rank_change`
- Fires when: abs(rank_delta) >= context.rank_jump_threshold AND both ranks within top N
- Severity: 'warning' if rank_delta > 0 (got worse), 'info' if rank_delta < 0 (improved)
- alert_type: AlertType.RANK_DROPPED_SIGNIFICANTLY (for either direction; the score_delta tells you which way)
- Reason: f"{metric} rank shifted by {rank_delta} (now {current_rank}, was {previous_rank})"

RULE 4 — `large_score_jump`
- Fires when: abs(score_delta) >= context.score_jump_threshold (regardless of rank)
- Severity: 'warning'
- alert_type: AlertType.SCORE_JUMP
- Reason: f"{metric} score changed by {score_delta:+.2f} ({previous_score:.2f} → {current_score:.2f})"

RULE 5 — `dropped_out_of_top_n`
- Fires when: diff.is_dropped_out AND previous_rank <= context.top_n
- Severity: 'info' (not a problem, but worth knowing)
- alert_type: AlertType.DROPPED_OUT
- Reason: f"{metric} dropped out of top {top_n} (was rank {previous_rank})"

Persistent-top alerts (RULE 6) require querying history beyond the immediate diff. Defer to a separate prompt (3.2.2) — it needs LTM lookup, not just a diff comparison.

```python
RULES_REGISTRY: dict[str, Callable[[PriorityBoardDiff, DetectionContext], DetectionResult]] = {
    "new_in_top_n": rule_new_in_top_n,
    "rank_jumped_into_top": rule_rank_jumped_into_top,
    "large_rank_change": rule_large_rank_change,
    "large_score_jump": rule_large_score_jump,
    "dropped_out_of_top_n": rule_dropped_out_of_top_n,
}

def apply_all_rules(
    diffs: list[PriorityBoardDiff],
    context: DetectionContext,
) -> list[DetectionResult]:
    """Run every rule against every diff. Return all results (fired or not).
    The caller filters to results.fired for alert creation."""
    results = []
    for diff in diffs:
        for rule_name, rule_func in RULES_REGISTRY.items():
            results.append(rule_func(diff, context))
    return results
```

Rule implementation template:
```python
def rule_new_in_top_n(diff: PriorityBoardDiff, ctx: DetectionContext) -> DetectionResult:
    if not (diff.is_new_in_top_n and diff.current_rank and diff.current_rank <= ctx.top_n):
        return DetectionResult(fired=False, rule_name="new_in_top_n", reason="not new in top n")

    severity = AlertSeverity.CRITICAL if diff.current_rank <= 5 else AlertSeverity.WARNING

    alert = WatchdogAlertCreate(
        alert_id=f"alrt_{uuid4().hex[:16]}",
        metric_name=diff.metric_name,
        alert_type=AlertType.NEW_IN_TOP_N,
        severity=severity,
        current_rank=diff.current_rank,
        previous_rank=None,
        rank_delta=None,
        score_current=diff.current_score,
        score_previous=None,
        triggered_by_rule="new_in_top_n",
        context_snapshot=json.dumps(diff.model_dump(mode="json")),
        source="DATA/gold_snapshots/gold_priority_board.csv",
        run_id=ctx.run_id,
    )
    return DetectionResult(
        fired=True,
        rule_name="new_in_top_n",
        alert=alert,
        reason=f"{diff.metric_name} entered the top {ctx.top_n} at rank {diff.current_rank}",
    )
```

Tests in tests_v2/test_detection_rules.py (one test per rule, at minimum):
- rule_new_in_top_n: synthetic diff with is_new_in_top_n=True and rank=3 → fired=True with severity=CRITICAL
- rule_new_in_top_n: rank=15 (outside top_n=10) → fired=False
- rule_rank_jumped_into_top: previous_rank=15, current_rank=8 → fired=True
- rule_rank_jumped_into_top: both ranks already in top N → fired=False (large_rank_change handles that case)
- rule_large_rank_change: rank_delta=7 → fired=True
- rule_large_score_jump: score_delta=0.25 → fired=True
- rule_dropped_out_of_top_n: is_dropped_out=True → fired=True with severity=INFO
- apply_all_rules: 3 diffs × 5 rules = 15 results, regardless of how many fired

Critical constraints:
- Every rule is a PURE FUNCTION. No DB calls, no LLM calls, no async needed (synchronous). This is the testability win.
- Severity escalation logic is hardcoded per rule. Phase 3 doesn't try to learn severity from data — that's a Phase 4+ concern if it comes up.
- The context_snapshot in the alert MUST round-trip valid JSON. The Pydantic mode="json" serialisation handles datetime → ISO string; verify with a test.

Acceptance criteria:
1. `apply_all_rules` runs against a real PriorityBoardDiff list and returns one DetectionResult per (diff, rule) combination
2. All 5 rules have at least 2 unit tests each (fired + not-fired case)
3. Synthetic test: construct a diff where the metric just entered the top 3 → exactly one rule (new_in_top_n) fires, severity CRITICAL
4. All tests pass
5. Phase 1 + Phase 2 tests still pass

Verify before next prompt: run a manual test on real data. Load the current Priority Board snapshot, diff against an artificially-older snapshot, apply rules. Look at which rules fired. Does it match intuition? If a "new_in_top_n" rule fires on a metric that's been in the top 10 for months, the diff logic is wrong — debug before continuing.
```

## Prompt 3.2.2 — Persistent-top detection (LTM-aware rule)

```
Add the 6th detection rule that requires LTM lookup, not just a diff: detect when a metric has been in the top N for several consecutive runs ("this has been a problem for a while now").

This rule is separate from Prompt 3.2.1's rules because it consumes the AgentMemoryRepository, making it async and stateful. The other 5 rules are pure functions of a single diff.

File modification: clubos2/watchdog/detection_rules.py (append to it)

```python
from clubos2.watchdog.memory_repo import AgentMemoryRepository
from datetime import timedelta

async def rule_persistent_top(
    diff: PriorityBoardDiff,
    ctx: DetectionContext,
    memory_repo: AgentMemoryRepository,
) -> DetectionResult:
    """Fires when a metric has been in the top N for >= persistence_threshold_runs consecutive runs.

    Implementation:
    1. Check if current_rank is in the top N (else, not applicable)
    2. Query memory for past 'present_in_top_n' memories for this metric over the last
       (persistence_threshold_runs + 1) runs
    3. If count meets threshold, fire alert
    """
    if not diff.current_rank or diff.current_rank > ctx.top_n:
        return DetectionResult(fired=False, rule_name="persistent_top", reason="not in top n")

    subject_key = f"{diff.metric_name}::present_in_top_n"

    # Count distinct memories within a window covering the threshold
    # (Window calculation depends on Watchdog run cadence — assume daily for Phase 3.
    #  3 consecutive daily runs = 3-day window. Make this configurable.)
    window = timedelta(days=ctx.persistence_threshold_runs)
    history = await memory_repo.count_within(
        agent_name="watchdog",
        subject_key=subject_key,
        within=window,
    )

    if history < ctx.persistence_threshold_runs:
        return DetectionResult(
            fired=False,
            rule_name="persistent_top",
            reason=f"present in top n only {history} times in window",
        )

    alert = WatchdogAlertCreate(
        alert_id=f"alrt_{uuid4().hex[:16]}",
        metric_name=diff.metric_name,
        alert_type=AlertType.PERSISTENT_TOP,
        severity=AlertSeverity.WARNING,
        current_rank=diff.current_rank,
        previous_rank=diff.previous_rank,
        rank_delta=diff.rank_delta,
        score_current=diff.current_score,
        score_previous=diff.previous_score,
        triggered_by_rule="persistent_top",
        context_snapshot=json.dumps(diff.model_dump(mode="json")),
        source="DATA/gold_snapshots/gold_priority_board.csv",
        run_id=ctx.run_id,
    )
    return DetectionResult(
        fired=True,
        rule_name="persistent_top",
        alert=alert,
        reason=f"{diff.metric_name} has been in top {ctx.top_n} for {history} consecutive runs",
    )
```

Add `count_within` to AgentMemoryRepository in memory_repo.py (this is the new memory method this rule needs):

```python
async def count_within(
    self,
    agent_name: str,
    subject_key: str,
    within: timedelta,
) -> int:
    """Count non-expired memories matching subject_key in the last `within` window."""
```

ALSO add a method that the Watchdog orchestrator will use to record "this metric was present in top N this run" (so the rule has data to query in future runs):

```python
async def remember_top_n_presence(
    self,
    metric_names: list[str],
    run_id: str,
    ttl: timedelta = timedelta(days=30),
) -> None:
    """Bulk-record one memory per metric currently in top N.
    Called once per Watchdog run after detection completes."""
    for metric_name in metric_names:
        await self.remember(
            agent_name="watchdog",
            memory_type="present_in_top_n",
            subject_key=f"{metric_name}::present_in_top_n",
            subject_metadata={"run_id": run_id},
            ttl=ttl,
        )
```

Tests in tests_v2/test_persistent_top_rule.py:
- A metric with 0 prior memories → rule does not fire (count below threshold)
- A metric with 3 prior memories within window → rule fires with severity WARNING
- A metric currently NOT in top N → rule does not fire regardless of history
- A metric with prior memories OLDER than the window → rule does not fire
- Use freezegun or as_of parameters to control time deterministically

Critical constraints:
- This rule is async (memory_repo is async). Apply_all_rules will need to handle a mix of sync and async rules — refactor it.
- The "present_in_top_n" memory is recorded by the Watchdog orchestrator (Prompt 3.2.3), NOT by the rule itself. Rules read history; the orchestrator writes it. Separation of concerns.
- TTL on "present_in_top_n" memories is 30 days by default — long enough that infrequent runs don't lose history, short enough that the table doesn't grow unbounded.

Refactor apply_all_rules to accept the memory_repo and call both sync and async rules:

```python
async def apply_all_rules(
    diffs: list[PriorityBoardDiff],
    context: DetectionContext,
    memory_repo: AgentMemoryRepository,
) -> list[DetectionResult]:
    """Run every rule against every diff. Mixed sync/async."""
    SYNC_RULES = {
        "new_in_top_n": rule_new_in_top_n,
        "rank_jumped_into_top": rule_rank_jumped_into_top,
        "large_rank_change": rule_large_rank_change,
        "large_score_jump": rule_large_score_jump,
        "dropped_out_of_top_n": rule_dropped_out_of_top_n,
    }
    ASYNC_RULES = {
        "persistent_top": rule_persistent_top,
    }

    results = []
    for diff in diffs:
        for name, rule in SYNC_RULES.items():
            results.append(rule(diff, context))
        for name, rule in ASYNC_RULES.items():
            results.append(await rule(diff, context, memory_repo))
    return results
```

Acceptance criteria:
1. Rule fires correctly when memory has enough history; doesn't fire otherwise
2. apply_all_rules returns mixed sync+async results in a single list
3. remember_top_n_presence bulk-records memories with correct TTLs
4. Tests pass with controlled time (freezegun)
5. Phase 1 + 2 tests still pass

Verify before next prompt: simulate three Watchdog runs with the same metric in the top N each time. After the third run, persistent_top rule should fire for that metric. Confirm — if it doesn't, debug the count_within query.
```

## Prompt 3.2.3 — Watchdog orchestrator (the run loop)

```
Build the Watchdog orchestrator — the top-level function that runs one complete detection cycle. Reads snapshot, diffs, applies rules, dedupes alerts via LTM, persists alerts, records LTM memories for future persistent_top detection.

File: clubos2/watchdog/orchestrator.py

```python
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timedelta
from clubos2.observability.tracing import traced
from clubos2.watchdog.priority_board_reader import PriorityBoardReader
from clubos2.watchdog.detection_rules import apply_all_rules, DetectionContext
from clubos2.watchdog.alerts_repo import AlertsRepository
from clubos2.watchdog.memory_repo import AgentMemoryRepository
from clubos2.watchdog.snapshot_repo import PriorityBoardSnapshotRepository

class WatchdogRunResult(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float

    # Detection stats
    metrics_evaluated: int
    rules_evaluated: int               # total rule evaluations (metrics × rules)
    rules_fired: int                    # how many rule results had fired=True
    alerts_created: int                 # how many actually persisted (after dedup)
    alerts_deduped: int                 # fired but suppressed by LTM dedup

    # IO references
    snapshot_id: str
    alert_ids: list[str]
    errors: list[str]

@traced(name="watchdog:run", run_type="chain")
async def run_watchdog(
    dedup_window_days: int = 7,
    top_n: int = 10,
) -> WatchdogRunResult:
    """One full Watchdog cycle. The orchestrator.

    Pipeline:
      1. Generate run_id
      2. Read current Priority Board snapshot
      3. Get previous snapshot from repo
      4. Diff current vs previous
      5. Apply all detection rules (with memory_repo for the LTM-aware rule)
      6. For each fired rule: check LTM dedup — has this exact (metric, alert_type) fired
         in the last dedup_window_days? If yes, drop. If no, queue for persistence.
      7. Persist the deduped alerts in one batch transaction
      8. Record LTM memories:
         - One 'alert_fired' memory per persisted alert with ttl=dedup_window_days
         - One 'present_in_top_n' memory per metric currently in top N (for future persistent_top rule)
      9. Save the current snapshot for next run's diff baseline
      10. Purge expired memories (housekeeping)
      11. Return WatchdogRunResult with full stats
    """
    run_id = f"wdog_{uuid4().hex[:16]}"
    started_at = datetime.utcnow()
    errors: list[str] = []

    try:
        reader = PriorityBoardReader()
        alerts_repo = AlertsRepository(session_factory=...)
        memory_repo = AgentMemoryRepository(session_factory=...)
        snapshot_repo = PriorityBoardSnapshotRepository(session_factory=...)

        # 2-3: snapshots
        current_snapshot = await reader.read_current()
        current_snapshot.snapshot_id = f"snap_{uuid4().hex[:16]}"
        previous_snapshot = await snapshot_repo.get_latest()

        # 4: diff
        diffs = await reader.diff_against_previous(current_snapshot, previous_snapshot)

        # 5: detection
        ctx = DetectionContext(top_n=top_n, run_id=run_id)
        results = await apply_all_rules(diffs, ctx, memory_repo)
        fired = [r for r in results if r.fired]

        # 6: dedup
        to_persist = []
        deduped_count = 0
        for result in fired:
            subject = f"{result.alert.metric_name}::{result.alert.alert_type.value}"
            if await memory_repo.has_recent(
                agent_name="watchdog",
                subject_key=subject,
                within=timedelta(days=dedup_window_days),
            ):
                deduped_count += 1
                continue
            to_persist.append(result.alert)

        # 7: persist alerts
        persisted = await alerts_repo.create_batch(to_persist)
        alert_ids = [a.alert_id for a in persisted]

        # 8: record memories for dedup AND for persistent_top rule
        for alert in persisted:
            await memory_repo.remember(
                agent_name="watchdog",
                memory_type="alert_fired",
                subject_key=f"{alert.metric_name}::{alert.alert_type.value}",
                subject_metadata={"alert_id": alert.alert_id, "run_id": run_id},
                ttl=timedelta(days=dedup_window_days),
            )

        # Bulk-record presence in top N for persistent_top rule
        in_top_n_metrics = [
            row.metric_name for row in current_snapshot.rows if row.rank <= top_n
        ]
        await memory_repo.remember_top_n_presence(in_top_n_metrics, run_id=run_id)

        # 9: save snapshot
        await snapshot_repo.save(current_snapshot)

        # 10: housekeeping
        await memory_repo.purge_expired()

        finished_at = datetime.utcnow()
        return WatchdogRunResult(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=(finished_at - started_at).total_seconds(),
            metrics_evaluated=len(diffs),
            rules_evaluated=len(results),
            rules_fired=len(fired),
            alerts_created=len(persisted),
            alerts_deduped=deduped_count,
            snapshot_id=current_snapshot.snapshot_id,
            alert_ids=alert_ids,
            errors=errors,
        )

    except Exception as e:
        errors.append(f"Watchdog run failed: {e}")
        logger.exception("Watchdog orchestrator crashed")
        finished_at = datetime.utcnow()
        return WatchdogRunResult(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=(finished_at - started_at).total_seconds(),
            metrics_evaluated=0, rules_evaluated=0, rules_fired=0,
            alerts_created=0, alerts_deduped=0,
            snapshot_id="", alert_ids=[], errors=errors,
        )
```

CLI: `python -m clubos2.watchdog.orchestrator` runs one cycle and prints the result.

Critical constraints:
- The whole pipeline is one LangSmith trace (run_type="chain"). Sub-steps (snapshot read, diff, rule application, dedup, persistence) each get their own child spans via @traced where appropriate.
- Errors caught at the top level; the WatchdogRunResult always returns, never raises. The errors list captures what went wrong. This is so the API caller in Prompt 3.3.1 can return 200 with errors-in-body rather than 500.
- Memory recording (step 8) and snapshot saving (step 9) happen AFTER alert persistence. If the run fails mid-pipeline, the previous run's state is preserved — Watchdog is idempotent across crashes.
- dedup_window_days defaults to 7. Configurable per run.

Tests in tests_v2/test_watchdog_orchestrator.py:
- A first-ever run (no previous snapshot) creates alerts for everything in top N (all classified as new_in_top_n)
- A second run with the same data dedupes everything (alerts_created=0, alerts_deduped equals rules_fired)
- A second run after dedup_window_days expires re-creates alerts (no dedup)
- A run with an artificial CSV change (one metric jumped from rank 8 to rank 2) produces the expected alerts
- A run mid-failure (mock the alerts_repo to raise) returns a WatchdogRunResult with errors populated, doesn't crash

Acceptance criteria:
1. `python -m clubos2.watchdog.orchestrator` runs end-to-end on the real CSV
2. The first run produces a non-zero alert count
3. Running again immediately produces zero new alerts (dedup works)
4. The DuckDB tables (watchdog_alerts, agent_memory, priority_board_snapshots) have data
5. The LangSmith trace shows the full pipeline as one trace with sub-spans
6. Tests pass with mocked dependencies

Verify before next prompt: run the orchestrator twice in a row. First run should produce N alerts. Second run, immediately after, should produce 0 alerts and N deduped. Then wait/manipulate time so dedup expires, run again — alerts should re-fire. If dedup logic is wrong, you'll see double alerts on the second run.
```

---

# Stage 3 — API integration and surfaces (3 prompts)

Manual trigger endpoint, alerts query endpoint, and integration with the existing v1 backend (only `BACKEND/api/app/main.py` modified — same pattern as Phase 1 Prompt 4.3).

## Prompt 3.3.1 — `POST /api/ai/watchdog/run` trigger endpoint

```
Add the manual-trigger endpoint that runs one Watchdog cycle and returns the result. This is the demoable hook — `curl POST /api/ai/watchdog/run` shows the system working in real time.

File to CREATE: BACKEND/api/app/routers/watchdog.py
File to MODIFY (one line addition only): BACKEND/api/app/main.py

In BACKEND/api/app/routers/watchdog.py:

```python
from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from clubos2.watchdog.orchestrator import run_watchdog, WatchdogRunResult
from clubos2.observability.tracing import get_current_langsmith_trace_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai/watchdog", tags=["ai", "watchdog"])

class WatchdogRunRequest(BaseModel):
    dedup_window_days: int = Field(default=7, ge=1, le=30)
    top_n: int = Field(default=10, ge=3, le=20)
    triggered_by: str = Field(default="manual", description="User or system that triggered the run")

class WatchdogRunResponse(BaseModel):
    run_id: str
    duration_seconds: float
    metrics_evaluated: int
    rules_fired: int
    alerts_created: int
    alerts_deduped: int
    alert_ids: list[str]
    trace_url: str | None
    errors: list[str]

@router.post("/run", response_model=WatchdogRunResponse)
async def trigger_watchdog_run(request: WatchdogRunRequest) -> WatchdogRunResponse:
    """Manually trigger one Watchdog detection cycle.

    Returns the result of the run including all alert IDs created.
    For querying the alerts themselves, use GET /api/ai/alerts.

    Phase 3 design note: this endpoint runs the Watchdog SYNCHRONOUSLY in the
    request handler. The pipeline typically completes in <5s for the current
    data volume. If runs grow expensive, future work will move execution to a
    background task with a status-check endpoint (POST /run returns run_id
    immediately, GET /runs/{run_id} polls for completion).
    """
    try:
        result: WatchdogRunResult = await run_watchdog(
            dedup_window_days=request.dedup_window_days,
            top_n=request.top_n,
        )
        return WatchdogRunResponse(
            run_id=result.run_id,
            duration_seconds=result.duration_seconds,
            metrics_evaluated=result.metrics_evaluated,
            rules_fired=result.rules_fired,
            alerts_created=result.alerts_created,
            alerts_deduped=result.alerts_deduped,
            alert_ids=result.alert_ids,
            trace_url=get_current_langsmith_trace_url(),
            errors=result.errors,
        )
    except Exception:
        logger.exception("Watchdog trigger endpoint failed")
        raise HTTPException(status_code=500, detail="Internal error running Watchdog")
```

Modification to BACKEND/api/app/main.py:
Same pattern as Phase 1 Prompt 4.3. Add EXACTLY two lines:

```python
from app.routers import watchdog
app.include_router(watchdog.router)
```

Place the import near the other router imports; the include_router call near the others. Touch nothing else.

Tests in tests_v2/test_api_watchdog_run.py:

```python
import sys
sys.path.insert(0, "BACKEND/api")
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

def test_watchdog_endpoint_registered():
    schema = client.get("/openapi.json").json()
    assert "/api/ai/watchdog/run" in schema["paths"]

@patch("clubos2.watchdog.orchestrator.run_watchdog", new_callable=AsyncMock)
def test_watchdog_run_happy_path(mock_run):
    from clubos2.watchdog.orchestrator import WatchdogRunResult
    from datetime import datetime
    mock_run.return_value = WatchdogRunResult(
        run_id="wdog_test", started_at=datetime.utcnow(), finished_at=datetime.utcnow(),
        duration_seconds=2.5, metrics_evaluated=20, rules_evaluated=120,
        rules_fired=5, alerts_created=3, alerts_deduped=2,
        snapshot_id="snap_test", alert_ids=["alrt_a", "alrt_b", "alrt_c"], errors=[],
    )
    response = client.post("/api/ai/watchdog/run", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "wdog_test"
    assert body["alerts_created"] == 3
    assert len(body["alert_ids"]) == 3

def test_watchdog_validates_params():
    response = client.post("/api/ai/watchdog/run", json={"top_n": 100})
    assert response.status_code == 422
```

Manual smoke test (document in clubos2/README.md):
```bash
# Terminal 1: existing v1 backend with v2 routes
cd BACKEND/api && uvicorn app.main:app --reload --port 8000

# Terminal 2: trigger Watchdog
curl -X POST http://localhost:8000/api/ai/watchdog/run \
  -H "Content-Type: application/json" \
  -d '{"dedup_window_days": 7, "top_n": 10}'
```

Expect a 200 with run stats. First run produces alerts; second run (immediately) produces zero new (all deduped).

Critical constraints:
- Synchronous execution is fine for Phase 3 (Watchdog completes in seconds). Document the future "move to background task" pattern as a comment but don't implement it.
- The endpoint NEVER raises uncaught exceptions to the client. Errors are either in the WatchdogRunResponse.errors field (operational errors handled by orchestrator) or 500 with generic message (unexpected crashes).
- Auth and rate limiting deferred to Phase 6. Add TODO comment.
- The endpoint is registered under /api/ai/watchdog/ — consistent with /api/ai/query from Phase 1.

Acceptance criteria:
1. POST /api/ai/watchdog/run with empty body returns 200 with a WatchdogRunResponse
2. Existing /api/ai/query (Phase 1) still works
3. All 36 v1 tests still pass
4. The trace_url in the response opens a real LangSmith trace
5. /docs shows the new endpoint
6. Tests pass

Verify before next prompt: run the orchestrator twice via curl. First call should show alerts_created > 0. Second call (immediately, within dedup window) should show alerts_created=0 and alerts_deduped > 0. If both calls produce alerts, dedup isn't working — fix before continuing.
```

## Prompt 3.3.2 — `GET /api/ai/alerts` query endpoint

```
Add the alerts query endpoint that lets clients fetch what Watchdog has detected. This is the read counterpart to the trigger endpoint.

File to MODIFY: BACKEND/api/app/routers/watchdog.py (extend the existing router from Prompt 3.3.1)

Append these endpoints to the same router file:

```python
from datetime import datetime, timedelta
from clubos2.watchdog.alerts_repo import AlertsRepository, AlertSeverity
from clubos2.watchdog.alerts_schema import WatchdogAlertRead

class AlertsListResponse(BaseModel):
    total: int
    alerts: list[dict]
    filters_applied: dict

@router.get("/alerts", response_model=AlertsListResponse)
async def list_alerts(
    limit: int = 50,
    since_hours: int | None = None,
    metric_name: str | None = None,
    severity: str | None = None,
    run_id: str | None = None,
    unacknowledged_only: bool = False,
) -> AlertsListResponse:
    """Query alerts produced by Watchdog runs.

    Filter options (all optional):
    - since_hours: only alerts created in the last N hours
    - metric_name: alerts about a specific metric
    - severity: 'info' | 'warning' | 'critical'
    - run_id: all alerts from a specific Watchdog run
    - unacknowledged_only: skip alerts already acknowledged
    """
    repo = AlertsRepository(session_factory=...)  # inject properly via dependency

    since: datetime | None = None
    if since_hours is not None:
        since = datetime.utcnow() - timedelta(hours=since_hours)

    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid severity: {severity}")

    alerts = await repo.list_recent(
        limit=limit,
        since=since,
        metric_name=metric_name,
        severity=severity_enum,
    )

    if run_id:
        alerts = [a for a in alerts if a.run_id == run_id]

    if unacknowledged_only:
        alerts = [a for a in alerts if a.acknowledged_at is None]

    return AlertsListResponse(
        total=len(alerts),
        alerts=[a.model_dump(mode="json") for a in alerts],
        filters_applied={
            "limit": limit, "since_hours": since_hours, "metric_name": metric_name,
            "severity": severity, "run_id": run_id, "unacknowledged_only": unacknowledged_only,
        },
    )

class AcknowledgeRequest(BaseModel):
    acknowledged_by: str = Field(..., min_length=1, max_length=100)

@router.post("/alerts/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_alert(alert_id: str, request: AcknowledgeRequest) -> dict:
    """Mark an alert as acknowledged. Phase 6 will wire this to Slack approve buttons."""
    repo = AlertsRepository(session_factory=...)
    try:
        updated = await repo.acknowledge(alert_id, by_user=request.acknowledged_by)
        return {
            "alert_id": updated.alert_id,
            "acknowledged_at": updated.acknowledged_at.isoformat(),
            "acknowledged_by": updated.acknowledged_by,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
```

Tests in tests_v2/test_api_alerts_query.py:
- GET /api/ai/alerts with no filters returns all recent alerts
- GET /api/ai/alerts?severity=critical returns only critical alerts
- GET /api/ai/alerts?metric_name=streaming_daily_users returns only alerts for that metric
- GET /api/ai/alerts?since_hours=1 returns only alerts in the last hour
- POST /api/ai/alerts/{alert_id}/acknowledge marks the alert; subsequent GET shows it acknowledged
- Acknowledging a non-existent alert returns 404

Manual smoke test:
```bash
# After running a Watchdog cycle:
curl http://localhost:8000/api/ai/alerts?limit=10
curl http://localhost:8000/api/ai/alerts?severity=critical
curl -X POST http://localhost:8000/api/ai/alerts/alrt_abc123/acknowledge \
  -H "Content-Type: application/json" -d '{"acknowledged_by": "divyansh"}'
```

Critical constraints:
- This endpoint is the seam Phase 6's frontend integration will hit. Keep the response schema stable.
- Filters compose (multiple can be applied simultaneously). All filters are optional; default returns last 50 alerts.
- Acknowledgment is per-alert, not per-batch. Bulk-acknowledge UX is a Phase 6 frontend concern, not a backend one.

Acceptance criteria:
1. GET /api/ai/alerts works after a Watchdog run has produced alerts
2. All filter combinations return correct results
3. Acknowledgment round-trips via the API
4. /docs shows both endpoints
5. Phase 1, Phase 2, and earlier Phase 3 tests still pass

Verify before next prompt: run Watchdog → query alerts → acknowledge one → query unacknowledged_only=true. Confirm the acknowledged one is filtered out. The full read/ack flow must work end-to-end.
```

## Prompt 3.3.3 — Watchdog integration with Scout (optional context enrichment)

```
Light integration: when the Scout agent answers a question about a metric, surface any recent Watchdog alerts for that metric as additional context.

This is a SMALL change to the Scout pipeline that adds value without requiring a multi-agent supervisor (which is Phase 5). It demonstrates that the two agents are part of one system, not isolated.

File to MODIFY: clubos2/agents/scout.py (extend the assemble_context step)

Pseudocode addition to assemble_context:

```python
async def assemble_context(metrics, chunks, ambiguities, *, alerts_repo=None):
    # ... existing code ...

    # NEW: enrich context with recent Watchdog alerts for the queried metrics
    if alerts_repo and metrics:
        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(days=7)
        for metric in metrics:
            recent_alerts = await alerts_repo.list_recent(
                limit=3,
                since=since,
                metric_name=metric.metric_name,
            )
            if recent_alerts:
                alerts_block = format_alerts_for_context(recent_alerts, metric.metric_name)
                # Insert into the context block under a clearly-labeled section
                # like "=== RECENT ALERTS FOR THIS METRIC ==="
```

format_alerts_for_context returns a string like:

```
=== RECENT ALERTS FOR streaming_daily_users ===
[source: watchdog_alerts]
- 2026-06-12 — alert_type: new_in_top_n, severity: critical, rank: 3 (rule: new_in_top_n)
  "streaming_daily_users entered the top 10 at rank 3"
- 2026-06-15 — alert_type: persistent_top, severity: warning, rank: 4 (rule: persistent_top)
  "streaming_daily_users has been in top 10 for 4 consecutive runs"
```

Critical constraints:
- The alerts_repo dependency is INJECTED, not imported globally. If not provided (e.g., in unit tests), the enrichment is skipped silently. This keeps Phase 1 and Phase 2 tests unaffected.
- Alerts are added to the context block, but the Scout prompt is NOT modified — the LLM treats them like any other retrieved data, with the existing citation rules.
- This enrichment is PURELY ADDITIVE to the context. It does not change Scout's tool calls, retrieval logic, or output schema.
- The source citation for alerts is "watchdog_alerts" (the table name). This shows up in ScoutAnswer.citations just like skill files or Gold CSVs.

Modify clubos2/agents/scout.py's run_scout signature:

```python
async def run_scout(
    input: ScoutInput,
    *,
    enable_alert_context: bool = True,
) -> ScoutAnswer:
    """..."""
    alerts_repo = None
    if enable_alert_context:
        try:
            from clubos2.watchdog.alerts_repo import AlertsRepository
            alerts_repo = AlertsRepository(session_factory=...)
        except Exception as e:
            logger.warning(f"Could not initialize alerts_repo, continuing without: {e}")
    # ... pass alerts_repo into assemble_context
```

Tests in tests_v2/test_scout_with_alert_context.py:
- Scout answers a question about a metric that has recent alerts → answer mentions/cites the alerts
- Scout with enable_alert_context=False → no alert context added (Phase 1 behaviour preserved)
- Mocked alerts_repo returning [] → context block has no "RECENT ALERTS" section, no error
- Mocked alerts_repo failing → Scout continues without alert context, logs warning

Critical constraints (re-emphasised):
- This is a non-breaking enhancement to Scout. All Phase 1 and Phase 2 tests must still pass without modification (because enable_alert_context=True by default, but the test mocks for Scout don't have alerts_repo wired, which gracefully falls through).
- The Phase 2 guardrails (no fabricated numbers, source-required, injection defence) all still apply to the new alert context strings. Verify in tests that an alert with an injected instruction gets sanitised.
- This is the ONLY cross-agent integration in Phase 3. The clean multi-agent orchestration (supervisor pattern) is Phase 5.

Acceptance criteria:
1. Asking Scout "what's happening with streaming_daily_users?" returns an answer that references the recent alert (if one exists)
2. Phase 1, Phase 2, and Phase 3 earlier tests still pass
3. The Scout's ScoutAnswer.citations includes "watchdog_alerts" as a source when alerts were used
4. Disabling alert context (enable_alert_context=False) reverts to Phase 1 behaviour exactly
5. Tests pass

Verify before next prompt: run Watchdog (produces alerts), then call Scout asking about one of the alerted metrics via /api/ai/query. The Scout's answer should mention the alert and cite "watchdog_alerts" as a source. Open the LangSmith trace — the alerts retrieval should be visible as a span.
```

---

# Stage 4 — Watchdog evals and Phase 3 completion (3 prompts)

10 new Watchdog-focused eval questions, eval scoring for the orchestrator, and the Phase 3 completion report.

## Prompt 3.4.1 — Add 10 Watchdog-focused golden questions

```
Extend the golden set from 20 questions (Phase 2) to 30 by hand-authoring 10 new questions focused on Watchdog behaviour. As in Phase 2 Prompt 2.1.2, these are HUMAN-AUTHORED — you write each one, the system does NOT generate them.

File to create: eval/golden/golden_set_v2.yaml

The v2 file CONTAINS the 20 questions from v1 plus 10 new ones. Do not delete v1. Keep both files in the repo. The default version used by `make v2-eval` becomes v2 (set via env).

The 10 new questions split:

WATCHDOG ALERT INTERPRETATION (5 questions):
- gq_021 — Scout question about a metric that HAS recent Watchdog alerts. Expected: Scout's answer references the alert and cites watchdog_alerts.
- gq_022 — Scout question about an alert's CAUSE. Expected: Scout correctly says "I can describe what alerted; I cannot determine the cause" — distinguishing detection (Watchdog's job) from explanation (Investigator's Phase 4 job).
- gq_023 — Scout question asking for alert history on a metric ("has streaming_daily_users been alerting?"). Expected: lists recent alerts with timestamps and types.
- gq_024 — Scout question conflating alert types ("is the persistent_top alert serious?"). Expected: Scout clarifies what the alert type means using metric_registry definitions, cites the alert and the registry.
- gq_025 — Scout question asking about an alert that does NOT exist for a metric ("are there critical alerts for fan_app_dau?"). Expected: Scout truthfully says "no recent alerts found for that metric" — must NOT invent.

WATCHDOG OUTPUT BEHAVIOUR (5 questions — these don't go through Scout, they validate Watchdog directly):

These are a different KIND of golden entry. Add a new question_type for them:

```python
class QuestionType(str, Enum):
    QUANTITATIVE = "quantitative"
    NARRATIVE = "narrative"
    MIXED = "mixed"
    AMBIGUOUS = "ambiguous"
    UNANSWERABLE = "unanswerable"
    WATCHDOG_RUN = "watchdog_run"        # NEW: tests the Watchdog orchestrator output
```

For WATCHDOG_RUN entries, the "question" is actually a SCENARIO described in natural language, and the "expected_answer_facts" describe what the WatchdogRunResult should contain.

Example WATCHDOG_RUN entries:

- gq_026 — Scenario: "First Watchdog run, no previous snapshots. Top 10 has 10 metrics. What should the result be?"
  expected_answer_facts: ["10 alerts of type new_in_top_n", "all severities populated", "alerts_deduped=0"]

- gq_027 — Scenario: "Two consecutive runs with identical Priority Board data, dedup_window_days=7. Result of the second run?"
  expected_answer_facts: ["alerts_created=0", "alerts_deduped equals rules_fired from first run", "no errors"]

- gq_028 — Scenario: "Metric X is at rank 8 in run 1, rank 2 in run 2. What alerts fire on run 2?"
  expected_answer_facts: ["large_rank_change rule fires", "rank_delta=6", "severity=warning"]

- gq_029 — Scenario: "Metric Y has been in top 10 for 4 consecutive daily runs, persistence_threshold_runs=3. Result?"
  expected_answer_facts: ["persistent_top rule fires on run 4", "alerts_created includes alert with rule=persistent_top"]

- gq_030 — Scenario: "A run where the CSV is malformed (missing required column). What should happen?"
  expected_answer_facts: ["WatchdogRunResult returned (not exception)", "errors list non-empty", "alerts_created=0"]

Update eval/golden/schema.py to:
- Add WATCHDOG_RUN to QuestionType enum
- Add an optional `scenario_setup` field to GoldenEntry for WATCHDOG_RUN entries to describe initial state
- Update the loader to handle both file versions

Update eval/golden/authoring_guide.md to document:
- The 6 question types (was 5)
- How to author WATCHDOG_RUN entries (scenario + expected WatchdogRunResult fields)
- The new distribution for v2: 6 quantitative, 5 narrative, 4 mixed, 3 ambiguous, 2 unanswerable, 5 Scout-with-alerts, 5 watchdog-run = 30 total

Tests in tests_v2/test_golden_loader_v2.py:
- load_golden_set("v2") returns 30 entries
- The 6 question types are represented
- All 10 new entries have author and created_at populated

Critical constraints:
- WATCHDOG_RUN entries are scored differently from Scout entries — they test the orchestrator's output, not the LLM's. The Phase 2 RAGAS scorer doesn't apply. Phase 3 Prompt 3.4.2 builds the WATCHDOG_RUN scorer.
- Don't modify any v1 entries. The golden set is append-only across versions.
- Make the scenario_setup field optional (defaults to None for non-WATCHDOG_RUN entries) so it doesn't break v1 entry loading.

Acceptance criteria:
1. eval/golden/golden_set_v2.yaml exists with exactly 30 entries (20 original + 10 new)
2. The 10 new entries split correctly: 5 SCOUT-with-alerts (using existing question_types like NARRATIVE/MIXED), 5 WATCHDOG_RUN
3. `python -c "from eval.golden.loader import load_golden_set; gs=load_golden_set('v2'); print(len(gs.entries))"` prints 30
4. Spot-check the WATCHDOG_RUN scenarios — each one describes initial state clearly enough that the WATCHDOG_RUN scorer can recreate it
5. Tests pass

Verify before next prompt: read 3 random WATCHDOG_RUN entries aloud. Could you (a) recreate the scenario in code? (b) verify the expected_answer_facts against an actual WatchdogRunResult? If either is unclear, rewrite — these are the rulers.
```

## Prompt 3.4.2 — Watchdog-specific scoring (for WATCHDOG_RUN entries)

```
Build the scorer that handles WATCHDOG_RUN entries — checking that the actual WatchdogRunResult matches the expected facts.

File: clubos2/eval/watchdog_scorer.py

WATCHDOG_RUN entries are scored DIFFERENTLY from Scout entries:
- No LLM-as-judge (the output is a structured object, not natural language)
- No RAGAS (no retrieval to evaluate)
- No fabrication check (no answer text)
- Instead: assertion-based checks against the WatchdogRunResult

```python
from pydantic import BaseModel
from clubos2.watchdog.orchestrator import WatchdogRunResult
from eval.golden.schema import GoldenEntry

class WatchdogScenarioResult(BaseModel):
    entry_id: str
    scenario_recreated: bool        # were we able to set up the scenario?
    watchdog_result: WatchdogRunResult | None
    expected_facts: list[str]
    facts_satisfied: list[str]      # which expected facts were observed
    facts_failed: list[str]         # which weren't
    overall_pass: bool
    notes: list[str]

async def run_watchdog_scenario(entry: GoldenEntry) -> WatchdogScenarioResult:
    """Recreate the scenario described in entry.scenario_setup, run Watchdog,
    check expected_answer_facts against the result.

    Scenarios are parameterised by:
    - whether to seed a previous snapshot
    - what CSV state to use (real DATA/gold_snapshots, or a fixture)
    - what's in agent_memory at the start

    Each scenario is implemented as a Python function keyed by entry.id.
    """
```

Implementation strategy: define a registry of scenario setup functions, one per WATCHDOG_RUN entry:

```python
async def setup_gq_026() -> None:
    """First-ever run: clear all watchdog state."""
    # Truncate watchdog_alerts, agent_memory, priority_board_snapshots
    ...

async def setup_gq_027() -> WatchdogRunResult:
    """Run Watchdog once, then return — caller will run it again."""
    await setup_gq_026()
    return await run_watchdog(dedup_window_days=7, top_n=10)

async def setup_gq_028() -> None:
    """Inject a previous snapshot where metric X is at rank 8; current CSV has it at rank 2.
    Use a fixture CSV path to avoid modifying real data."""
    ...

SCENARIO_SETUPS = {
    "gq_026": setup_gq_026,
    "gq_027": setup_gq_027,
    "gq_028": setup_gq_028,
    "gq_029": setup_gq_029,
    "gq_030": setup_gq_030,
}
```

Fact-checking logic:

```python
def check_fact(fact: str, result: WatchdogRunResult) -> bool:
    """Parse a human-written fact string and check it against the result.

    Supported fact patterns:
    - "alerts_created=N" → result.alerts_created == N
    - "alerts_deduped=N" → result.alerts_deduped == N
    - "{N} alerts of type {type}" → count alerts with that type from alert_ids
    - "{rule_name} rule fires" → at least one alert from that rule_name exists
    - "errors list non-empty" → len(result.errors) > 0
    - etc.

    Fact patterns are intentionally simple — if a pattern doesn't match, the
    fact is marked as "uncheckable" and logged for manual review (not auto-fail).
    """
```

Critical constraints:
- Scenarios reset state (truncate tables) before running. After the scenario completes, run a CLEANUP to restore the DB to its prior state (use a savepoint or a separate test DB).
- For Phase 3, scenario setup uses a SEPARATE DuckDB file (var/clubos_watchdog_eval.duckdb) so eval doesn't pollute real Watchdog state.
- Fact-checking is regex-based and intentionally lossy. If a fact can't be parsed, mark as uncheckable and continue — don't auto-fail.

Integrate into the eval pipeline (clubos2/eval/pipeline.py):

```python
async def run_full_eval(golden_version: str = "v2", scout_prompt_version: str = "v1"):
    gs = load_golden_set(golden_version)

    # Split entries by type
    scout_entries = [e for e in gs.entries if e.question_type != QuestionType.WATCHDOG_RUN]
    watchdog_entries = [e for e in gs.entries if e.question_type == QuestionType.WATCHDOG_RUN]

    # Existing Scout flow for scout_entries (Phase 2)
    scout_run = await run_eval_for_scout(scout_entries, scout_prompt_version)
    scout_scores_ragas = await score_with_ragas(scout_run)
    scout_scores_fab = score_fabrication_batch(scout_run)
    scout_scores_behav = score_behaviour_batch(scout_run, gs)

    # NEW Watchdog flow for watchdog_entries
    watchdog_scores = []
    for entry in watchdog_entries:
        result = await run_watchdog_scenario(entry)
        watchdog_scores.append(result)

    # Combined report (next prompt extends the reporter to handle both)
    ...
```

Tests in tests_v2/test_watchdog_scorer.py:
- Each scenario setup function is callable and produces deterministic state
- check_fact correctly parses each supported pattern
- A run that satisfies all expected facts → overall_pass=True
- A run that fails one fact → overall_pass=False, facts_failed lists it

Critical constraints:
- Scenarios MUST be isolated. After the eval pipeline finishes, real Watchdog data must be untouched. Use a separate DB file or transaction-with-rollback.
- The scorer does NOT call LLMs. Pure deterministic checks.
- Adding a new WATCHDOG_RUN golden entry in the future requires adding a scenario setup function — this is by design. Document this in the authoring guide.

Acceptance criteria:
1. Running the full eval pipeline against golden_set_v2 completes all 30 entries: 25 Scout + 5 Watchdog
2. All 5 WATCHDOG_RUN scenarios have setup functions and complete cleanly
3. Eval DB is separate from production Watchdog DB — verify by running eval, then querying the real DB to confirm no eval artifacts leaked
4. Tests pass

Verify before next prompt: run the full pipeline. The total should show 30 entries scored, with breakdown by type. Check the var/clubos_watchdog_eval.duckdb file — it should have evaluation alerts; var/clubos_semantic.duckdb (production) should NOT have evaluation alerts mixed in.
```

## Prompt 3.4.3 — Phase 3 completion report and end-to-end demo script

```
Build the verification scaffolding for Phase 3 completion and write the human-readable state report.

Files to create:
- tests_v2/test_phase3_e2e.py — end-to-end integration tests
- DOCS/phase3_completion.md — state report
- scripts/v2_demo_phase3.sh — bash demo script

In tests_v2/test_phase3_e2e.py:

```python
import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_E2E") != "1",
    reason="E2E tests require RUN_E2E=1 and real API keys + clean DB",
)

@pytest.mark.asyncio
async def test_watchdog_full_cycle_creates_alerts():
    """First-ever Watchdog run produces alerts; second run dedupes."""
    from clubos2.watchdog.orchestrator import run_watchdog
    # Clean state assumed (tester is responsible)

    result1 = await run_watchdog(dedup_window_days=7, top_n=10)
    assert result1.alerts_created > 0, "First run should produce alerts"
    assert result1.alerts_deduped == 0

    result2 = await run_watchdog(dedup_window_days=7, top_n=10)
    assert result2.alerts_created == 0, "Second immediate run should dedupe all"
    assert result2.alerts_deduped == result1.alerts_created

@pytest.mark.asyncio
async def test_scout_picks_up_watchdog_alerts():
    """End-to-end: run Watchdog, then Scout question about an alerted metric includes alert context."""
    from clubos2.watchdog.orchestrator import run_watchdog
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput

    await run_watchdog()
    # Find an alerted metric (read from alerts_repo)
    from clubos2.watchdog.alerts_repo import AlertsRepository
    repo = AlertsRepository(...)
    alerts = await repo.list_recent(limit=1)
    assert len(alerts) > 0, "Need at least one alert for this test"
    metric = alerts[0].metric_name

    answer = await run_scout(ScoutInput(question=f"what is happening with {metric}?"))
    sources = {c.source for c in answer.citations}
    assert "watchdog_alerts" in sources, f"Scout should cite watchdog_alerts; got {sources}"

@pytest.mark.asyncio
async def test_v1_endpoints_still_work():
    """Regression: v1 still functional after Phase 3 additions."""
    import sys
    sys.path.insert(0, "BACKEND/api")
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    assert client.get("/priorities").status_code == 200

@pytest.mark.asyncio
async def test_phase1_and_phase2_endpoints_still_work():
    """Regression: Phase 1 + Phase 2 still functional."""
    import sys
    sys.path.insert(0, "BACKEND/api")
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.post("/api/ai/query", json={"question": "what is streaming_daily_users this month?"})
    assert response.status_code == 200
```

DOCS/phase3_completion.md template:

```markdown
# ClubOS 2.0 — Phase 3 Completion Report

## What was built
- [ ] watchdog_alerts SQL table + AlertsRepository
- [ ] agent_memory SQL table + AgentMemoryRepository (LTM for deduplication)
- [ ] priority_board_snapshots table + repository (run-over-run diffs)
- [ ] PriorityBoardReader: snapshot capture + diff computation
- [ ] 6 detection rules (5 pure functions + 1 LTM-aware)
- [ ] Watchdog orchestrator with full pipeline including dedup and housekeeping
- [ ] POST /api/ai/watchdog/run trigger endpoint
- [ ] GET /api/ai/alerts query endpoint with filters
- [ ] POST /api/ai/alerts/{id}/acknowledge endpoint
- [ ] Scout enriched with optional alert context for queried metrics
- [ ] 10 new golden eval questions (5 Scout-with-alerts, 5 WATCHDOG_RUN)
- [ ] WatchdogScenarioScorer for WATCHDOG_RUN entries
- [ ] Eval pipeline integrated for the 30-question v2 golden set

## Verified facts (Phase 3 baseline)
- Total v1 tests still passing: 36
- Total v2 tests passing: {N}
- Total Phase 3 tests passing: {N}
- Phase 2 eval (Scout, 20 questions) still passes baseline thresholds
- Phase 3 eval (Watchdog scenarios, 5 questions) all pass

## What was deliberately NOT done
- Slack delivery — Phase 6 work. Alerts are queryable via API; Phase 6 adds the Slack publisher.
- LangGraph STM checkpointer — Phase 4 work, where the Investigator agent needs multi-step state.
- Background scheduler — manual trigger via POST is sufficient for Phase 3. Phase 6+ may add a cron-replaceable scheduler if real deployment requires it.
- Holdout discipline (50 questions with 10 hidden) — deferred to Phase 4 when 2+ agents make overfitting a real risk.
- Watchdog as an LLM agent — DETECTION IS DETERMINISTIC PYTHON. This is intentional and a senior point.

## Known gaps deferred to Phase 4
- The Investigator agent (which explains *why* a Watchdog alert fired) is Phase 4.
- The Briefing agent (which composes monthly briefings) is Phase 5.
- Multi-agent supervisor orchestration is Phase 5.
- External data via MCP servers (weather, social, match data) is Phase 4 (informs the Investigator's reasoning).

## How to demo Phase 3
Three commands that show Phase 3 working end-to-end:

1. Start the backend with Phase 3 routes:
   ```bash
   cd BACKEND/api && uvicorn app.main:app --reload --port 8000
   ```

2. Trigger Watchdog:
   ```bash
   curl -X POST http://localhost:8000/api/ai/watchdog/run \
     -H "Content-Type: application/json" -d '{"dedup_window_days": 7, "top_n": 10}'
   ```
   Expect: 200 with run stats including alerts_created > 0 on a clean run.

3. Query alerts:
   ```bash
   curl http://localhost:8000/api/ai/alerts?limit=10
   ```
   Expect: list of recent alerts with metric_name, alert_type, severity, score values.

4. Ask Scout about an alerted metric (cross-agent integration):
   ```bash
   curl -X POST http://localhost:8000/api/ai/query \
     -H "Content-Type: application/json" \
     -d '{"question": "what is happening with streaming_daily_users this month?"}'
   ```
   Expect: Scout's answer references the Watchdog alert and cites watchdog_alerts.

5. Run the second Watchdog cycle to demonstrate dedup:
   ```bash
   curl -X POST http://localhost:8000/api/ai/watchdog/run -d '{}'
   ```
   Expect: alerts_created=0, alerts_deduped > 0.

## Phase 4 entry checklist
- [ ] All Phase 3 acceptance criteria pass
- [ ] All Phase 2 eval metrics still meet baseline thresholds (no regression from adding alert context to Scout)
- [ ] All 5 WATCHDOG_RUN scenarios pass
- [ ] You can explain to an interviewer why Watchdog detection is deterministic (not an LLM agent) in 60 seconds
- [ ] GCP Cloud Run deployment of v1 still works (manual deploy verified)

## The interview narrative for Phase 3
"Phase 3 added the Watchdog — a continuously-running monitoring system. The senior point in the design: detection is arithmetic, not reasoning. The Watchdog itself is deterministic Python — it reads a Priority Board snapshot, diffs against the previous run, applies 6 rules, and persists alerts. There's no LLM in the detection path because comparing ranks doesn't require reasoning, and wrapping a comparison in an LLM is a junior tell. Memory comes from an agent_memory SQL table — generic enough to be reused by Investigator and Briefer in later phases — and it powers alert deduplication so we don't spam the same warning every day for a persistent issue. The integration with Scout is light: when someone asks Scout about a metric that has recent alerts, those alerts appear in the answer as a cited source. The result is two agents working as one system, with the clean orchestrator pattern coming in Phase 5."
```

In scripts/v2_demo_phase3.sh (bash, executable):

```bash
#!/usr/bin/env bash
# ClubOS 2.0 — Phase 3 end-to-end demo.
# Requires: backend running on localhost:8000, valid API keys in env.

set -euo pipefail

API=http://localhost:8000

echo "=== Phase 3 Demo ==="
echo ""

echo "1. Triggering first Watchdog run..."
curl -s -X POST $API/api/ai/watchdog/run \
  -H "Content-Type: application/json" \
  -d '{"dedup_window_days": 7, "top_n": 10}' | jq .

echo ""
echo "2. Querying recent alerts..."
curl -s "$API/api/ai/alerts?limit=10" | jq '.alerts[:3]'

echo ""
echo "3. Asking Scout about an alerted metric..."
curl -s -X POST $API/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{"question": "what is happening with streaming_daily_users this month?"}' | jq .

echo ""
echo "4. Triggering second Watchdog run (should dedupe)..."
curl -s -X POST $API/api/ai/watchdog/run \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.alerts_created, .alerts_deduped'

echo ""
echo "=== Demo complete ==="
```

Critical constraints:
- E2E tests gated by RUN_E2E=1 (do not run in normal CI; cost concerns)
- The completion report is honest — every checkbox marked accurately
- The demo script runs end-to-end in under 30 seconds and produces visible, real output

Acceptance criteria:
1. E2E tests pass with RUN_E2E=1 and a valid setup
2. DOCS/phase3_completion.md exists with every section filled honestly
3. scripts/v2_demo_phase3.sh runs without errors and produces real Watchdog → Scout chain output
4. All Phase 1, Phase 2, and Phase 3 tests pass
5. v1 backend still deployable to GCP Cloud Run

Verify Phase 3 complete:
- Walk through the demo script. Real output appears for each step.
- Open the LangSmith dashboard: there should be traces for the Watchdog run (showing snapshot read → diff → rules → persistence) AND traces for the Scout query (showing the new alerts retrieval).
- If the Watchdog produces alerts but Scout doesn't pick them up when asked about the alerted metric, the cross-agent integration is broken — fix before moving on.
- Read the interview narrative aloud. If any part feels rehearsed or marketing-y, rewrite as plain engineer-talk.

This Phase 3 completion is the second major demoable piece of ClubOS 2.0. After Phase 1 you had Scout answering questions; after Phase 3 you have Scout + a real monitoring agent + cross-agent context. The story has moved from "I built a RAG chatbot" to "I built two agents that work together as one system, with explicit deterministic-vs-probabilistic boundaries". This is the inflection point in the interview narrative.

Do not start Phase 4 until the Phase 3 completion report has every box honestly ticked.
```

---

# Phase 3 done. What's next.

When all 12 prompts above are complete and the Phase 3 completion report is honestly all-green, the system can:
- Monitor the Priority Board on demand and detect rank-change anomalies deterministically
- Deduplicate alerts so persistent issues don't generate daily noise
- Surface recent alerts inside Scout's grounded answers automatically
- Be evaluated end-to-end on 30 golden questions including 5 Watchdog scenarios

**Phase 4 (next phase) will cover:**
- The Investigator Agent — the FIRST true LLM agent (LangGraph ReAct loop, not a deterministic pipeline like Scout)
- LangGraph STM checkpointer — multi-step state persistence for investigation runs
- MCP servers for external context — weather, match data, social, web search
- Per-metric tool routing logic
- Golden set expansion to 50 questions with 10-question holdout (overfitting discipline begins)
- First multi-agent linkage: Watchdog → Investigator handoff (Watchdog fires alert, Investigator investigates)

Phase 4 prompts will be generated after you confirm Phase 3 is complete and the demo script runs cleanly.
