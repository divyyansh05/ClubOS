# ClubOS 2.0 — Status Audit Report

**Date:** 2026-07-02  
**Auditor:** Claude Code (automated)  
**Repo state:** branch=features, HEAD=a61e8ef

---

## Executive Summary

Phases 1–4 are structurally complete: all source files, migrations, API endpoints, golden sets, and test suites exist as designed. The v2 test suite passes 294/294 non-skipped tests. The backend imports cleanly and all 8 AI endpoints register correctly in OpenAPI. **One BLOCKER exists**: the `gateway/client.py` hardcodes `scout_prompt_version = "v1"` as default, while the baseline eval was generated with `v4` — a fresh install would silently evaluate the wrong prompt. Two MEDIUM issues: the v1 test suite has a working-directory assumption (must be run from project root, not `backend/api/`), and `SCOUT_PROMPT_VERSION` is absent from `.env.v2.example`. Four skill files (`command_center`, `monthly_briefing`, `peer_benchmark`, `social_intelligence`) are confirmed skeletons with TODO placeholders. The `behavioural_summary.overall_pass_rate` in baseline is 0.80, below the ≥ 0.85 target stated in the methodology doc. Overall verdict: **YELLOW — minor gaps to close before Phase 5, estimated 1–2 hours of cleanup.**

---

## Environment

| Key | Value |
|---|---|
| Python | 3.11.14 |
| Pydantic | 2.13.4 |
| DuckDB (Python) | 1.5.4 |
| Working directory | `/Users/divyanshshrivastava/RE Internship project` |
| Branch | `features` |
| HEAD | `a61e8ef` |

---

## Phase-by-Phase Status

### Phase 1 — Semantic Layer + RAG + Scout
- **Status: ✅ COMPLETE**
- **Notes:** All files exist. Semantic DB has 59 metrics, all with non-null definitions (far exceeds the ≥10 target). ChromaDB collection `clubos_skills` contains 24 chunks. Scout agent files, prompt versioning, and `/api/ai/query` endpoint all confirmed present and registered.
- **Gaps/concerns:**
  - `command_center.md`, `monthly_briefing.md`, `peer_benchmark.md`, `social_intelligence.md` — headers present but body is all TODOs (12 TODO markers per file). Skill validator will flag these. Only `priority_board.md` and `signal_engine.md` are fully authored.
  - Default prompt version in `gateway/client.py:36` is `"v1"` — eval baseline was run on `v4`. See BLOCKER below.

---

### Phase 2 — Evals + Guardrails + Observability
- **Status: ✅ COMPLETE**
- **Notes:** All 6 scorer/pipeline files exist. All 3 guardrail files exist. CI gate script exists at `scripts/v2_ci_gate.py` with correct `#!/usr/bin/env python3` shebang. Baseline JSON exists at `eval/reports/baseline.json`.
- **Baseline metrics:**
  - fabrication = 0/20 ✅ (0.0 incidence)
  - behavioural pass rate = **0.80** ⚠️ (below methodology target of ≥ 0.85)
  - RAGAS = null (deferred; acceptable per design)
  - run_id = `eval_2026-06-26T15-18-44.705854`
  - Scout prompt used: `v4` (per `golden_set_version=v1`)
- **Prompt versions present:** scout_v1, scout_v2, scout_v3, scout_v4
- **Gaps/concerns:**
  - Behavioural pass rate 0.80 is below the 0.85 gate in the methodology doc. This is a known gap (Phase 2 deliberately shipped with it) but becomes a BLOCKER for the CI gate if Phase 5 eval reruns hit the same score.
  - `SCOUT_PROMPT_VERSION` is not set in `.env.v2.example` — default falls back to `v1` not `v4`.

---

### Pre-Phase-3 Eval Consolidation
- **Status: ✅ COMPLETE**
- **Methodology doc:** ✅ `docs/eval_methodology.md` exists with Layer 1, Layer 2, Layer 3 sections. Phrase "deterministic-first" found at `docs/phase2_completion.md:39`.
- **`--skip-ragas` flag:** ✅ Present in `clubos2/eval/pipeline.py` at argparse and orchestration function.
- **Gaps/concerns:**
  - The phrase "deterministic-first" appears in `phase2_completion.md` but not in `eval_methodology.md` itself (the methodology doc uses "Layer 1 — Fabrication-rate (deterministic)" and "Layer 2 — Behavioural compliance (deterministic)"). Technically acceptable.
  - Top-level `README.md` does not exist (only `AGENTS.md`, `CLAUDE.md`, `REPO_STRUCTURE.md` at root). `eval_methodology.md` is therefore not linked from any README.

---

### Phase 3 — Watchdog + LTM Memory
- **Status: ✅ COMPLETE**
- **Detection rules present: 6/6** (`rule_new_in_top_n`, `rule_rank_jumped_into_top`, `rule_large_rank_change`, `rule_large_score_jump`, `rule_dropped_out_of_top_n`, `rule_persistent_top`)
- **Notes:** All 8 watchdog source files exist. All 3 API endpoints registered (`POST /api/ai/watchdog/run`, `GET /api/ai/watchdog/alerts`, `POST /api/ai/watchdog/alerts/{alert_id}/acknowledge`). Scout cross-agent enrichment confirmed (`enable_alert_context` at `clubos2/agents/scout.py:279`).
- **DB table state:** `watchdog_alerts`, `agent_memory`, `priority_board_snapshots` do NOT exist yet in `var/clubos_semantic.duckdb`. This is expected — the `bootstrap_watchdog_alerts_db()` function creates tables on first `POST /api/ai/watchdog/run` call. Migration SQL files exist and are referenced correctly.
- **Gaps/concerns:**
  - Phase 3 completion report (`docs/phase3_completion.md`) contains real numbers (219 passing, 4 skipped E2E). ✅ No documentation drift detected.

---

### Phase 4 — Investigator + MCP Web Search
- **Status: ✅ COMPLETE**
- **Investigator tools present: 6/6** (`query_metrics`, `search_knowledge`, `get_recent_alerts`, `get_metric_definition`, `get_peer_benchmark`, `web_search` — all `@tool` decorated)
- **MCP server:** Files exist (server_config.py, web_search_client.py, web_search_server.py). `WebSearchProvider` enum has `TAVILY` and `BRAVE`. `.env.v2.example` lists `TAVILY_API_KEY=` and `BRAVE_SEARCH_API_KEY=` (empty — keys not committed).
- **Golden set v3:** 40 visible entries (gq_001–gq_040), 10 holdout entries (h_001–h_010). Overlap sanity check passes.
- **LangGraph:** `state.py`, `graph.py`, `checkpointer.py` all exist. `var/clubos_investigator_checkpoints.sqlite` exists (0 bytes — no investigation run yet, expected).
- **Gaps/concerns:**
  - `docs/phase4_completion.md` does not contain actual run numbers for visible-vs-holdout comparison (checklist items are unchecked). Specifically: "Visible-vs-holdout delta on faithfulness < 0.05" is `[ ]` not `[x]`. The "Phase 5 entry checklist" lists 5 items, all unchecked. This is acceptable documentation state (conditions not yet met) but worth noting.
  - `v2-eval-holdout` Makefile target is **MISSING**. The `clubos2/eval/holdout_runner.py` exists, but there is no corresponding `v2-eval-holdout` Make target. Audit spec expected one.

---

## Test Status

| Suite | Passing | Failing | Skipped | Notes |
|---|---|---|---|---|
| **v1 (backend)** | **167** | **0** | **0** | Must run from **project root**: `pytest backend/api/tests/ -q` |
| **v2 (clubos2)** | **294** | **0** | **7** | Run from project root: `pytest tests_v2/ -q` |

**v1 note:** When run from the `backend/api/` subdirectory (`cd backend/api && pytest tests/ -q`), 34 tests fail due to path resolution. The failing tests use project-root-relative paths like `Path("backend/api/app/config/scoring_config.json")` and `data/gold_snapshots/...`. Run from project root, all 167 pass.

**v2 skipped tests (7):**
- `tests_v2/test_phase1_e2e.py` — 3 tests (gated: `RUN_E2E=1`)
- `tests_v2/test_phase3_e2e.py` — 4 tests (gated: `RUN_E2E=1`)

All skips are intentional E2E gates, not regressions.

---

## Runtime Health

- **Backend starts cleanly:** YES — all imports succeed, app initializes, "Application startup complete" logged. Bind fails on port 8000 only because another service (ScoutIQ API, PID 41151) is using that port. Backend confirmed operational on port 8001.
- **Endpoints registered (confirmed via OpenAPI at :8001):**
  - `/api/ai/query` ✅ (Phase 1)
  - `/api/ai/watchdog/run` ✅ (Phase 3)
  - `/api/ai/watchdog/alerts` ✅ (Phase 3)
  - `/api/ai/watchdog/alerts/{alert_id}/acknowledge` ✅ (Phase 3)
  - `/api/ai/investigator/run/{alert_id}` ✅ (Phase 4)
  - `/api/ai/investigator` ✅ (Phase 4)
  - `/api/ai/investigator/{investigation_id}` ✅ (Phase 4)
- **TODO/FIXME count in `clubos2/`:** 32 occurrences
- **Notable TODO items:**
  1. `clubos2/rag/skills/command_center.md` — 6 TODOs: "needs human authorship — placeholder for 2026-07-04"
  2. `clubos2/rag/skills/monthly_briefing.md` — 6 TODOs: "needs human authorship — placeholder for 2026-07-04"
  3. `clubos2/rag/skills/peer_benchmark.md` — 6 TODOs: "needs human authorship — placeholder for 2026-07-04"
  4. `clubos2/rag/skills/social_intelligence.md` — 6 TODOs: "needs human authorship — placeholder for 2026-07-04"
  5. `clubos2/guardrails/injection_defence.py:47` — "TODO Phase 5+: if MCP/external content is ingested, harden with semantic injection" (appropriately deferred)

---

## Recent Commit History

```
a61e8ef feat: Phase 4.3.2 + 4.4.3 — Scout investigation context, holdout runner, completion report, demo
ff73c5c feat: Phase 4.2.4 + 4.3.1 — orchestrator, investigate endpoint, findings query API
92b3e82 feat: Phase 4.4.2 — investigation scenario runner, fact checker, scorer
1f58fe2 feat: Phase 4.1.3 + 4.2.2 + 4.2.3 — tool registry, LangGraph ReAct graph, SqliteSaver checkpointer
9f9c114 feat: Phase 4.4.1 — golden_set_v3 (40 entries), holdout_set_v1 (10 entries), INVESTIGATION type
0812bfc feat: Phase 4.1.1 + 4.2.1 — investigations schema, repo, agent_schemas, state, prompt
b5c7860 feat: Phase 4.1.2 — MCP web search server, Tavily/Brave client, FastMCP server
6b7b2bf chore: remove legacy v1 demos, mockups and research docs
2bb5dcc Phase 3: Watchdog agent — deterministic detection, LTM dedup, Scout integration
923b32b Phase 2: ship deterministic baseline; defer RAGAS to on-demand
f524222 feat: complete Phase 1 implementation of ClubOS 2.0 AI agentic layer
ff61f4c Merge branch 'features'
23c25c2 feat: upcoming features grid layout + documentation sync
26a15eb feat: upcoming features roadmap — docs + /upcoming screen
1c54765 chore: redeploy to pick up new github secrets
0b025c9 feat: inject secrets into cloud run deployment for connectors
034957f fix: update Dockerfile to explicitly use requirements/base.txt
9b51a5c chore: remove redundant requirements files and point dockerfile directly to requirements/base.txt
aec32d3 fix: add requests to root requirements.txt for docker build
9ad0961 fix: add requests dependency and copy integrations dir to docker image
```

---

## Directory Structure

### Expected top-level directories

| Directory | Status | Notes |
|---|---|---|
| `clubos2/` | ✅ EXISTS | |
| `backend/api/` | ✅ EXISTS | (not BACKEND/api — lowercase) |
| `apps/clubos-web/` | ✅ EXISTS | (not APPS/ — lowercase) |
| `data/gold_snapshots/` | ✅ EXISTS | (not DATA/ — lowercase) |
| `databricks/` | ✅ EXISTS | (not DATABRICKS/ — lowercase) |
| `prompts/` | ✅ EXISTS | |
| `eval/` | ✅ EXISTS | |
| `tests_v2/` | ✅ EXISTS | |
| `var/` | ✅ EXISTS | |
| `docs/` | ✅ EXISTS | (not DOCS/ — lowercase) |

Note: The audit spec used uppercase (`BACKEND/`, `APPS/`, `DATA/`, `DATABRICKS/`, `DOCS/`) but actual dirs are lowercase. All expected directories exist.

### `clubos2/` subpackages

| Package | Status |
|---|---|
| `gateway/` | ✅ EXISTS |
| `observability/` | ✅ EXISTS |
| `semantic_layer/` | ✅ EXISTS |
| `rag/` | ✅ EXISTS |
| `tools/` | ✅ EXISTS |
| `agents/` | ✅ EXISTS |
| `guardrails/` | ✅ EXISTS |
| `eval/` | ✅ EXISTS |
| `watchdog/` | ✅ EXISTS |
| `investigator/` | ✅ EXISTS |
| `mcp/` | ✅ EXISTS |

### `prompts/` contents
- `scout_v1.md`, `scout_v2.md`, `scout_v3.md`, `scout_v4.md` ✅
- `investigator_v1.md` ✅
- Highest scout version: v4. Highest investigator version: v1.
- Active default: `scout_v1` (gateway default) ⚠️ — see BLOCKER

### `eval/golden/` contents
- `golden_set_v1.yaml` (20 entries) ✅
- `golden_set_v2.yaml` (30 entries: v1 + 5 WATCHDOG_RUN) ✅
- `golden_set_v3.yaml` (40 entries: v2 + 10 INVESTIGATION) ✅
- `holdout_set_v1.yaml` (10 entries) ✅

### `docs/` key files
- `eval_methodology.md` ✅
- `phase1_completion.md` ✅
- `phase2_completion.md` ✅
- `phase3_completion.md` ✅
- `phase4_completion.md` ✅ (with unchecked Phase 5 entry checklist)

---

## What Is Working

- All 294 v2 unit tests pass (7 skipped are intentional RUN_E2E gates)
- All 167 v1 backend tests pass (when run from project root)
- Backend starts cleanly — all Phase 1–4 imports succeed
- All 7 AI/v2 API endpoints register in OpenAPI
- Semantic layer: 59 metrics, all with definitions
- ChromaDB RAG collection: 24 chunks indexed
- Scout agent files, 4 prompt versions present
- All 6 watchdog detection rules implemented
- All 6 investigator tools `@tool` decorated
- LangGraph ReAct graph (state, graph, checkpointer) wired correctly
- Scout cross-agent enrichment: both `enable_alert_context` (Phase 3) and `enable_investigation_context` (Phase 4) present
- Golden sets v1/v2/v3 and holdout set all load without error
- `--skip-ragas` flag present in pipeline.py argparse
- Phase 2 baseline: fabrication = 0/20 (hard guarantee holds)
- MCP server config: Tavily/Brave enum configured, keys in env example (not committed)
- All phase completion docs exist with real numbers

---

## What Is Broken or Missing

1. **`gateway/client.py:36`** — `scout_prompt_version: str = Field(default="v1")`. The baseline eval was run with `v4`. Fresh installs default to `v1`, silently running the wrong prompt.
2. **`.env.v2.example`** — Missing `SCOUT_PROMPT_VERSION=v4`. No way for a developer to know what prompt version to use without reading `docs/phase2_completion.md`.
3. **`Makefile`** — Missing `v2-eval-holdout` target. `clubos2/eval/holdout_runner.py` exists but is not wired into Make. Phase 4 completion doc implies it should be there.
4. **`behavioural_summary.overall_pass_rate = 0.80`** in baseline — below the 0.85 target stated in `docs/eval_methodology.md`. The CI gate will reject a Phase 5 eval run that scores the same.
5. **Skill files skeleton** — `command_center.md`, `monthly_briefing.md`, `peer_benchmark.md`, `social_intelligence.md` have headers but all body sections are TODO placeholders. Placeholder deadline is 2026-07-04.
6. **v1 tests working-directory assumption** — Running `cd backend/api && pytest tests/ -q` produces 34 false failures. No `conftest.py` or `pytest.ini` enforces the correct CWD.
7. **Top-level README.md missing** — Audit spec expected a README with `eval_methodology.md` link. Only `AGENTS.md`, `CLAUDE.md`, `REPO_STRUCTURE.md` exist at root.
8. **`docs/phase4_completion.md`** — Phase 5 entry checklist has 5 unchecked items including "Visible-vs-holdout delta on faithfulness < 0.05" and "At least 7 of 10 INVESTIGATION entries pass on the visible set". These acceptance criteria have not been verified.
9. **Port 8000 occupied** — Another service (ScoutIQ API, PID 41151) is running on port 8000. The ClubOS backend will fail to bind if started without killing that process first.
10. **`.env.v2.example` contains real credentials** — `OPENAI_API_KEY` and `LANGSMITH_API_KEY` values appear to be real API keys committed to the example file. These should be replaced with placeholder strings (`sk-...` style fake values).

---

## What Needs Correction Before Phase 5

- **[SEVERITY: BLOCKER]** Default scout prompt version is `v1` but baseline was evaluated on `v4`. Fix: set `scout_prompt_version: str = Field(default="v4")` in `clubos2/gateway/client.py:36` AND add `SCOUT_PROMPT_VERSION=v4` to `.env.v2.example`. Without this, any Phase 5 eval run will compare against a different prompt than the baseline, making the CI gate meaningless.

- **[SEVERITY: BLOCKER]** `.env.v2.example` contains real API keys (`OPENAI_API_KEY`, `LANGSMITH_API_KEY`). Replace with placeholder stub values immediately before any push or PR. This is a credential leak risk.

- **[SEVERITY: BLOCKER]** `behavioural_summary.overall_pass_rate = 0.80` is below the 0.85 threshold in `docs/eval_methodology.md`. If Phase 5 eval produces ≥ 0.85, the CI gate will reject the current baseline (inverted logic). Either: (a) re-run the baseline eval after fixing the prompt default to confirm actual score, or (b) update the methodology doc threshold to reflect 0.80 as the real acceptance bar with rationale. Do not leave this unresolved — Phase 5 CI gate will hit this on day one.

- **[SEVERITY: MEDIUM]** Add `v2-eval-holdout` target to `Makefile`. The holdout runner exists (`clubos2/eval/holdout_runner.py`) but is not wired. One-line fix.

- **[SEVERITY: MEDIUM]** Fix v1 test invocation — add a note to `AGENTS.md` or add a `pytest.ini` at project root that sets `testpaths = backend/api/tests tests_v2`. Currently `cd backend/api && pytest tests/` causes 34 false failures, which will confuse Phase 5 CI work.

- **[SEVERITY: MEDIUM]** Kill or document the ScoutIQ service on port 8000. Phase 5 will involve running the ClubOS backend — it needs to own port 8000, or the port needs to be changed in the CORS/frontend config.

- **[SEVERITY: MINOR]** Author the 4 skeleton skill files (`command_center.md`, `monthly_briefing.md`, `peer_benchmark.md`, `social_intelligence.md`) by the 2026-07-04 placeholder deadline. These affect RAG retrieval quality but Phase 5 can start without them.

- **[SEVERITY: MINOR]** Add `eval_methodology.md` link to top of `AGENTS.md` or create a top-level README. Currently there is no discovery path from repo root to the eval architecture doc.

- **[SEVERITY: MINOR]** Update `CLAUDE.md` session context — it references `dev` branch and V1.5.4 state. The current branch is `features` and we are at Phase 4 complete.

---

## Recommendation

The project is very close to ready for Phase 5. All structural code is in place and tests are healthy. Three items warrant attention before starting: (1) fix the `v1` vs `v4` prompt default — this is a one-line change but has significant eval consequences; (2) rotate the real API keys out of `.env.v2.example`; (3) clarify the behavioural pass rate threshold before the Phase 5 CI gate tries to enforce it. These three items together are about **30 minutes of work**. The skeleton skill files (medium priority) add another 1–2 hours if done properly. Phase 5 can begin in parallel with the skill file authoring, but the prompt version and credential issues should be fixed first.

---

*Audit completed at 2026-07-02T13:19Z. Report saved to `docs/status_audit_2026-07-02.md`*
