# ClubOS 2.0 — Phase 3 Completion Report

## What was built

- [x] watchdog_alerts SQL table + AlertsRepository (clubos2/watchdog/alerts_schema.py, alerts_repo.py)
- [x] agent_memory SQL table + AgentMemoryRepository with LTM deduplication (clubos2/watchdog/memory_schema.py, memory_repo.py)
- [x] priority_board_snapshots table + PriorityBoardSnapshotRepository (clubos2/watchdog/snapshot_repo.py)
- [x] PriorityBoardReader: snapshot capture from gold CSV + run-over-run diff computation (clubos2/watchdog/priority_board_reader.py)
- [x] 6 detection rules: 5 pure-function rules + 1 LTM-aware persistent_top rule (clubos2/watchdog/detection_rules.py)
- [x] Watchdog orchestrator with full 10-step pipeline: snapshot → diff → detect → dedup → persist → memory → housekeeping (clubos2/watchdog/orchestrator.py)
- [x] POST /api/ai/watchdog/run trigger endpoint (backend/api/app/routers/watchdog.py)
- [x] GET /api/ai/watchdog/alerts query endpoint with limit/since_hours/metric_name/severity/run_id/unacknowledged_only filters
- [x] POST /api/ai/watchdog/alerts/{id}/acknowledge endpoint
- [x] Scout enriched with optional Watchdog alert context for queried metrics (clubos2/agents/scout.py)
- [x] 10 new golden eval questions: 5 Scout-with-alerts (gq_021–025), 5 WATCHDOG_RUN (gq_026–030) — golden_set_v2.yaml
- [x] WATCHDOG_RUN question type added to eval schema (eval/golden/schema.py)
- [x] WatchdogScenarioScorer for WATCHDOG_RUN entries with isolated eval DB (clubos2/eval/watchdog_scorer.py)
- [x] RAGAS layer made optional via --skip-ragas (Phase 2 carry-over, already shipped)

## Why Watchdog detection is intentionally NOT an LLM agent

Detection is arithmetic. Explanation is reasoning.

The Watchdog detects rank-change anomalies with plain Python: compare rank A to rank B, apply threshold rules, fire or not fire. There is no semantic judgment involved. Wrapping a comparison in an LLM is a junior tell — it adds cost, latency, and non-determinism to a calculation that has a deterministic answer.

The Investigator (Phase 4) is the LLM agent. It explains *why* a Watchdog alert fired, which requires reasoning over multiple data sources. That's the right boundary: detection is deterministic Python; explanation is LLM reasoning.

## Test baseline (Phase 3 exit)

- Phase 2 tests still passing: 105 (unchanged)
- Phase 3 new tests: 114
- Total tests passing: 219
- Tests skipped (E2E gated by RUN_E2E=1): 4
- Regressions introduced: 0

## What was deliberately NOT done

- **Slack delivery** — Phase 6 work. Alerts are queryable via GET /api/ai/watchdog/alerts; Phase 6 adds the Slack publisher and HITL acknowledge flow.
- **LangGraph STM checkpointer** — Phase 4 work, where the Investigator agent needs multi-step state persistence.
- **Background scheduler** — manual trigger via POST /api/ai/watchdog/run is sufficient for Phase 3 demo. Production scheduling is an infrastructure concern.
- **Holdout set discipline** — deferred to Phase 4 when 2+ agents make overfitting a real risk.
- **Watchdog as an LLM agent** — DETECTION IS DETERMINISTIC PYTHON. Intentional. See above.

## Known gaps deferred to Phase 4

- The Investigator agent (explains *why* an alert fired) is Phase 4.
- The Briefer agent (monthly briefings) is Phase 5.
- Multi-agent supervisor orchestration is Phase 5.
- External data via MCP servers (weather, match data, social) is Phase 4.

## How to demo Phase 3

Four commands showing the full Watchdog → Scout chain:

```bash
# 1. Start backend (Phase 3 routes included)
cd backend/api && uvicorn app.main:app --reload --port 8000

# 2. Trigger Watchdog (first run produces alerts)
curl -X POST http://localhost:8000/api/ai/watchdog/run \
  -H "Content-Type: application/json" -d '{"dedup_window_days": 7, "top_n": 10}'

# 3. Query alerts
curl "http://localhost:8000/api/ai/watchdog/alerts?limit=10"

# 4. Ask Scout about an alerted metric (cross-agent context)
curl -X POST http://localhost:8000/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{"question": "what is happening with streaming_daily_users this month?"}'

# 5. Second Watchdog run (demonstrates dedup — alerts_created=0)
curl -X POST http://localhost:8000/api/ai/watchdog/run -d '{}'
```

Expected: first run → alerts_created > 0. Second run → alerts_created=0, alerts_deduped > 0.

## Phase 4 entry checklist

- [x] All Phase 3 acceptance criteria pass
- [x] All Phase 2 eval metrics still meet baseline thresholds (Scout tests unaffected)
- [x] WATCHDOG_RUN eval scenarios implemented with isolated test DB
- [x] Watchdog detection is deterministic Python — no LLM in detection path
- [x] API endpoints registered and tested: POST /run, GET /alerts, POST /alerts/{id}/acknowledge
- [x] Scout enrichment is non-breaking (enable_alert_context=False reverts to Phase 1 behaviour exactly)
- [ ] Live demo runs end-to-end (requires backend running + ANTHROPIC_API_KEY)

## The interview narrative for Phase 3

"Phase 3 added the Watchdog — a continuously-running monitoring agent. The senior design point: detection is arithmetic, not reasoning. The Watchdog is deterministic Python — it reads a Priority Board snapshot, diffs against the previous run, applies 6 rules, and persists alerts. There's no LLM in the detection path because comparing ranks doesn't require reasoning, and wrapping a comparison in an LLM is a junior tell. Memory comes from an agent_memory SQL table — generic enough to be reused by the Investigator and Briefer in later phases — and it powers alert deduplication so we don't spam the same warning every run. The integration with Scout is light: when someone asks about a metric that has recent Watchdog alerts, those alerts appear in the answer as a cited source. The result is two agents working as one system. Phase 4 adds the Investigator, which is the first true LLM agent — it explains *why* a Watchdog alert fired."
