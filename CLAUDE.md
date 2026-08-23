# ClubOS Claude Instructions

## Session Context (Last Updated: 2026-07-02)

**Current State:**
- Branch: `features`
- Tests: 461 passing (167 v1 backend + 294 v2) — run `pytest` from project root
- Status: V2 Phase 4 complete. Phase 5 (Briefer + LangGraph supervisor) is next.
- Last milestone: Investigator + MCP web search (Phase 4)

**Completed — V1 product:**
- V1 MVP: All 10 phases complete (Priority Board, Peer Benchmark, Signal Engine, Health Summary, Monthly Briefing)
- V1.5.1: Event Calendar & Annotation Engine
- V1.5.2: Event-Adjusted Anomaly Detection
- V1.5.3: Seasonal Baseline Intelligence
- V1.5.4: Conversion Rate Volume Pairing

**Completed — V2 AI layer:**
- Phase 1: Semantic layer (59-metric registry), RAG (ChromaDB, 24 chunks), Scout agent, `/api/ai/query`
- Phase 2: 20-question golden eval set, fabrication/behavioural/RAGAS scorers, guardrails, CI gate, deterministic-first baseline (fabrication=0/20, behavioural=0.80)
- Phase 3: Watchdog (6 detection rules, LTM dedup), `/api/ai/watchdog/*`, Scout alert context, golden_set_v2 (30 questions)
- Phase 4: Investigator (LangGraph ReAct, 6 tools, MCP web search), `/api/ai/investigator/*`, Scout investigation context, golden_set_v3 (40 visible + 10 holdout)

**Key V1 files:**
- Backend services: `backend/api/app/services/`
- Backend routers: `backend/api/app/routers/` (priorities, events, health, benchmark, signals, briefing, refresh, analytics, ai_query, watchdog, investigator)
- Frontend: `apps/clubos-web/src/features/`
- Data: `data/gold_snapshots/gold_*.csv`

**Key V2 files:**
- Agents: `clubos2/agents/scout.py`, `clubos2/agents/scout_schemas.py`
- Investigator: `clubos2/investigator/` (graph.py, orchestrator.py, tools.py, state.py, checkpointer.py, repo.py)
- Watchdog: `clubos2/watchdog/` (detection_rules.py, orchestrator.py, alerts_repo.py, memory_repo.py, snapshot_repo.py)
- RAG: `clubos2/rag/` (chunker.py, embeddings.py, ingest.py, retriever.py, skills/)
- Eval: `clubos2/eval/` (pipeline.py, fabrication_scorer.py, behavioural_scorer.py, watchdog_scorer.py, investigator_scorer.py, holdout_runner.py)
- Prompts: `prompts/scout_v4.md` (active default), `prompts/investigator_v1.md`
- Golden sets: `eval/golden/golden_set_v3.yaml` (40 entries), `eval/golden/holdout_set_v1.yaml` (10 entries)
- Baseline: `eval/reports/baseline.json`

**Known Good State:**
- Backend starts cleanly on port 8000 (check if occupied — another service sometimes runs there)
- Frontend runs on port 5174
- CORS configured for 5174, 5176, 5177
- All 461 tests pass via `pytest` from project root
- `pyproject.toml` sets testpaths and pythonpath — do NOT run `cd backend/api && pytest` (path issues)
- Semantic DB: `var/clubos_semantic.duckdb` (metric_registry only — watchdog/investigation tables bootstrap on first API call)
- ChromaDB: `var/chroma` (24 chunks)
- Investigator checkpoints: `var/clubos_investigator_checkpoints.sqlite`

**Open items entering Phase 5:**
- Behavioural pass rate is 0.80 (baseline) — methodology doc targets 0.85; resolve before CI gate gates Phase 5
- Scout prompt default in `clubos2/gateway/client.py:36` is `"v1"` — should be `"v4"` to match baseline
- 4 skill files are skeleton (command_center, monthly_briefing, peer_benchmark, social_intelligence) — placeholder deadline 2026-07-04
- Phase 4 entry checklist in `docs/phase4_completion.md` has 5 unchecked acceptance criteria

**Documentation:**
- Eval methodology: `docs/eval_methodology.md` — read this before touching any eval or prompt work
- Phase completion reports: `docs/phase1_completion.md` through `docs/phase4_completion.md`
- Prompt versioning: `docs/prompt_versioning.md`
- Architecture: `docs/architecture/`

---

## Project Instructions

Before doing any work, read:

1. `AGENTS.md`
2. `REPO_STRUCTURE.md`
3. `docs/eval_methodology.md` — mandatory if touching eval, prompts, or AI output quality
4. `docs/phase4_completion.md` — mandatory if starting Phase 5 work
5. `docs/product/clubos_product_definition_report.md`
6. `docs/product/clubos_mvp_spec.md`

Then:

- choose the correct role file from `agents/`
- work only inside the folders owned by that role
- follow the build order in `AGENTS.md`
- for V2 AI work: read `clubos2/README.md` for the V2 subpackage map
- do not overclaim what the monthly data supports
- keep the Priority Board as the hero feature
- treat AI as a support layer, not core logic

**V2-specific rules:**
- V2 code lives in `clubos2/`. Do not put V2 logic inside `backend/api/app/` except thin router files.
- Every prompt change requires a re-eval run (`make v2-eval`) and comparison to baseline.
- Additive extension only — V1 must remain independently deployable.
- All eval work uses `eval/golden/golden_set_v3.yaml` as the current visible set and `eval/golden/holdout_set_v1.yaml` as the held-out set (do not train/tune against holdout).

If there is a conflict between product ambition and real data support, prefer the real data.
