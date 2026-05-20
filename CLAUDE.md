# ClubOS Claude Instructions

## Session Context (Last Updated: 2026-05-19)

**Current State:**
- Branch: `dev`
- Tests: 36 passing backend tests
- Status: V1.5.4 complete, all features committed
- Last milestone: Conversion Rate Volume Pairing

**Completed Features:**
- V1 MVP: All 10 phases complete (Priority Board, Peer Benchmark, Signal Engine, Health Summary, Monthly Briefing)
- V1.5.1: Event Calendar & Annotation Engine (gold_events.csv, 5 API endpoints, chart annotations)
- V1.5.2: Event-Adjusted Anomaly Detection (anomaly_context_service, event-driven classification)
- V1.5.3: Seasonal Baseline Intelligence (seasonal_service, 12-month baselines, z-score interpretation)
- V1.5.4: Conversion Rate Volume Pairing (conversion_context_service, quadrant classification)

**Key Files:**
- Backend services: `backend/api/app/services/{priority,event,anomaly_context,seasonal,conversion_context}_service.py`
- Backend tests: `backend/api/tests/` (36 passing)
- Frontend: `apps/clubos-web/src/features/{priority-board,events}/`
- Data: `data/gold_snapshots/gold_*.csv` (6 tables including gold_events)
- API: `backend/api/app/routers/` (8 endpoints: priorities, events, health, benchmark, signals, briefing, refresh, analytics)

**Known Good State:**
- Backend runs on port 8000
- Frontend runs on port 5174
- CORS configured for 5174, 5176, 5177
- All 36 backend tests green
- All V1.5.1-V1.5.4 features documented in `docs/project_plan/IMPLEMENTATION_PLAN.md`

**Recent Bug Fixes:**
- Port 8000 orphaned processes resolved
- Frontend .env fixed to point to 8000
- CORS updated to allow port 5174

**Documentation:**
- Full implementation plan: `docs/project_plan/IMPLEMENTATION_PLAN.md`
- Master wiki: `docs/MASTER_WIKI.md`
- Schema contracts: `docs/architecture/gold_table_contracts.md`
- Data contracts: `data_contracts/*.md`

---

## Project Instructions

Before doing any work, read:

1. `AGENTS.md`
2. `REPO_STRUCTURE.md`
3. `docs/product/clubos_product_definition_report.md`
4. `docs/product/clubos_mvp_spec.md`
5. `docs/product/clubos_screen_blueprint.md`
6. `docs/architecture/clubos_databricks_schema_plan.md`

Then:

- choose the correct role file from `agents/`
- work only inside the folders owned by that role
- follow the build order in `AGENTS.md`
- do not overclaim what the monthly data supports
- keep the Priority Board as the hero feature
- treat AI as a support layer, not core logic

If there is a conflict between product ambition and real data support, prefer the real data.
