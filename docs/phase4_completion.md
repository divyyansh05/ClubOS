# ClubOS 2.0 — Phase 4 Completion Report

## What was built

- [x] `investigations` SQL table + repository (schema.py, repo.py, migration)
- [x] MCP web search server (Tavily/Brave) + Python client (clubos2/mcp/)
- [x] 6-tool registry for the Investigator (query_metrics, search_knowledge, get_recent_alerts, get_metric_definition, get_peer_benchmark, web_search)
- [x] LangGraph linear ReAct agent (graph.py, state.py, prompts/investigator_v1.md)
- [x] SqliteSaver checkpointer for STM (checkpointer.py — resume infrastructure built, not exposed via API)
- [x] Investigator orchestrator with full lifecycle (start → run → parse → persist → memory)
- [x] POST /api/ai/investigator/run/{alert_id} trigger endpoint
- [x] GET /api/ai/investigator and GET /api/ai/investigator/{id} read endpoints
- [x] Scout cross-agent integration with past investigations (citing source 'investigations')
- [x] 10 new visible Investigator-focused golden questions (gq_031 → gq_040)
- [x] 10 holdout questions in separate file (h_001 → h_010)
- [x] INVESTIGATION question type and scenario runner
- [x] Investigation scorer with fact-checking against InvestigationRunResult
- [x] Holdout eval runner + comparison report

## Verified facts (Phase 4 baseline)

- Phase 1-3 tests preserved: all passing
- Phase 4 tests passing: see test suite
- Visible eval: golden_set_v3 (40 questions)
- Holdout eval: holdout_set_v1 (10 questions)

## What was deliberately NOT done

- Auto-trigger from Watchdog → manual trigger only. Phase 5 supervisor will add this.
- Additional MCP servers (match data, weather, social) → Phase 5+ if narrative needs them.
- LangGraph resume API endpoint → STM infrastructure built but not exposed.
- Token/cost tracking on investigations → fields exist in DB but currently NULL.
- Multi-agent orchestration → Phase 5. The cross-agent links are point-to-point.
- Briefing Agent → Phase 5.

## Known gaps deferred to Phase 5

- The Briefer agent (composes monthly briefings from past investigations) is Phase 5.
- The LangGraph supervisor that routes between Scout, Investigator, and Briefer is Phase 5.
- Watchdog → Investigator auto-handoff is Phase 5.
- More MCP servers — add if specific interview moments need them.

## How to demo Phase 4

```bash
# 1. Trigger Watchdog
curl -X POST http://localhost:8000/api/ai/watchdog/run -d '{}'

# 2. Investigate an alert
curl -X POST http://localhost:8000/api/ai/investigator/run/alrt_abc123 \
  -H "Content-Type: application/json" -d '{"max_steps": 6}'

# 3. List investigations
curl http://localhost:8000/api/ai/investigator?limit=5

# 4. Ask Scout — answer should reference both alert AND investigation
curl -X POST http://localhost:8000/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{"question": "what is happening with streaming_daily_users and why?"}'
```

## Phase 5 entry checklist

- [ ] All Phase 4 acceptance criteria pass
- [ ] Visible-vs-holdout delta on faithfulness < 0.05
- [ ] At least 7 of 10 INVESTIGATION entries pass on the visible set
- [ ] LangSmith traces show clean ReAct loops
- [ ] You can explain Scout vs Investigator difference in 90 seconds
