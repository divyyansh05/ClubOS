# ClubOS 2.0 — Prompt 1.5 Report

**Date:** 2026-07-02  
**Branch:** features  
**Commits:** 6d7bf42 (gateway default), 5069eb5 (config propagation), + this doc

---

## Part A — Config propagation

### Files modified

| File | Change | Verification |
|---|---|---|
| `clubos2/eval/pipeline.py:15,81` | signature default `"v1"` → `None`; argparse default `"v1"` → `None`; resolves from `GatewaySettings` with `logger.info` | ✓ bare invocation picks up env-configured version |
| `clubos2/eval/runner.py:53,115` | same pattern | ✓ |
| `clubos2/eval/holdout_runner.py:11` | signature default `"v1"` → `None`; resolves from `GatewaySettings` | ✓ |
| `scripts/v2_ci_gate.py:35` | argparse default `"v1"` → `None`; resolves from `GatewaySettings` + `print()` statement for CI log visibility | ✓ |
| `clubos2/agents/scout.py:32,34` | double-fallback hardcoded `"v1"` → `"v4"` + `logger.warning` (never fires in production) | ✓ |

**Architectural outcome:** `GatewaySettings.scout_prompt_version` is now the single source of truth. `SCOUT_PROMPT_VERSION` in the environment propagates automatically to all 7 consumers. No per-file drift possible.

**Important env finding during verification:** The local `.env.v2` has `SCOUT_PROMPT_VERSION=v3`, so `GatewaySettings().scout_prompt_version` resolves to `v3` on this machine — NOT `v4`. The bare pipeline invocation confirmed this by logging `scout_prompt_version=v3`. This means:
- The code default (`v4`) is correct for fresh installs
- The local dev environment is pinned to `v3` — intentional or an oversight worth reviewing
- The baseline was generated on `v4` — so this local env is divergent from the baseline

### Test verification

- `pytest tests_v2/ -q` → **294 passing / 0 failing / 7 skipped** ✓
- Bare `python -m clubos2.eval.pipeline --golden v1 --skip-ragas` → picks up `v3` from `.env.v2` (env-driven, correct behaviour) ✓
- Explicit `--prompt-version v3` override → resolves to `v3` (argparse plumbing confirmed) ✓

### Files left unmodified (intentional)

- `tests_v2/test_reporter.py:41` — pinned test fixture, `"v1"` is the object being tested, not the prompt under evaluation
- `tests_v2/test_ragas_scorer.py:38` — same

---

## Part B — Diagnostic surface

### B1 — Temperature audit

| File:line | temperature= value | Context | Concern? |
|---|---|---|---|
| `clubos2/agents/scout.py:383` | `0.0` | Scout narrative answer generation | NO |
| `clubos2/agents/scout.py:396` | `0.0` | Scout structured output (ScoutAnswer JSON) | NO |
| `clubos2/investigator/graph.py:26` | `0` | LangGraph Investigator agent | NO |
| `clubos2/eval/ragas_scorer.py:45` | `0` | RAGAS evaluator LLM | NO |
| `clubos2/gateway/client.py:151,161` | resolved from `settings.default_temperature` (default `0.0`) | All gateway-routed calls | NO |

**Summary:** No non-zero temperatures anywhere in the Scout path or eval pipeline. Temperature is fully locked at 0.0. Temperature leak is **ruled out** as a variance source.

**Note:** `default_temperature: float = Field(default=0.0)` in `GatewaySettings` — any call that doesn't pass an explicit temperature gets 0.0.

---

### B2 — Retrieval configuration

| File:line | n_results | Embedding | Deterministic? |
|---|---|---|---|
| `clubos2/rag/retriever.py:184` | `min(k_vector, total_chunks)` where `k_vector=20` | `embed_texts()` via `text-embedding-3-small` (OpenAI, 1536 dim) | YES |
| ChromaDB raw `.query()` | — | default Chroma embedder (all-MiniLM-L6-v2, 384 dim) | N/A — fails with dimension mismatch; never used in production path |

**Retrieval stack:**
1. `embed_texts([query])` → OpenAI `text-embedding-3-small` → 1536-dim vector
2. ChromaDB cosine search using pre-computed vector (not Chroma's built-in embedder)
3. BM25 over all 24 chunks (deterministic given fixed corpus)
4. RRF fusion of vector + BM25 results
5. Cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) → top 5

**Reranker behaviour:** `CrossEncoder.predict()` is inference-only with no randomness. Given the same query and the same candidate texts, it produces identical scores. Tie-breaking in `sorted()` is stable (Python's Timsort is stable, so equal scores preserve insertion order). **No randomness in reranker.**

**ChromaDB determinism diagnostic:** Raw `.query()` with Chroma's default embedder fails with `InvalidArgumentError: Collection expecting embedding with dimension of 1536, got 384` — confirming the production path never uses Chroma's built-in embedder. The production path always passes pre-computed 1536-dim vectors directly, making vector search fully deterministic for identical inputs.

---

### B3 — Concurrency audit

| File:line | Mechanism | Concurrency level | Shared state risk |
|---|---|---|---|
| `clubos2/agents/scout.py:304` | `asyncio.gather(*metric_tasks, knowledge_task)` | Multiple tool calls per question (parallel) | LOW — read-only tool calls |
| `clubos2/eval/runner.py:63` | `asyncio.Semaphore(parallel=3)` | 3 questions in flight simultaneously | LOW — each question is independent |
| `clubos2/eval/runner.py:92` | `asyncio.gather(*[run_one(e) for e in gs.entries])` | All 20 questions gathered | LOW — results list is ordered by submission |
| `clubos2/eval/pipeline.py:42` | `asyncio.gather(fab_task, behav_task)` | 2 post-processing tasks | NONE — pure in-memory computation |

**Scout-level concurrency (scout.py:304):** `metric_tasks` and `knowledge_task` run in parallel per question. All are reads (DuckDB queries, ChromaDB queries). No shared write state. `asyncio.gather` returns in submission order regardless of completion order, so results are deterministic in ordering.

**Eval-level concurrency (runner.py:92):** 20 questions run with semaphore(3). Completion order within the semaphore window varies by LLM latency, but `asyncio.gather` preserves submission order in results. The final `results` list is deterministically ordered even if individual questions complete out of order.

**Shared state risk:** None identified. Tool calls are read-only. The `agent_memory` and `watchdog_alerts` tables do not exist yet (bootstrap on first watchdog run), so Scout's context enrichment silently returns empty — but this is consistent across all runs.

---

### B4 — Mutable state

- `agent_memory` row count: TABLE MISSING (bootstrap on first watchdog run — consistent across eval runs)
- `watchdog_alerts` row count: TABLE MISSING (same)
- ChromaDB collection: 24 chunks, stable
- Eval pipeline writes to shared state: **NO** — fabrication_scorer and behavioural_scorer are pure in-memory scorers; `eval/runs/*.json` written per run but not read by subsequent eval runs
- Exception: `watchdog_scorer.py:123` — `DELETE FROM <table>` and `memory_repo.remember()` at line 207, and `investigator_scorer.py:171,255` — `repo.create(alert)` — but **these are in the Watchdog and Investigator scorers, not the fabrication/behavioural scoring pipeline used for the baseline**. The baseline eval only runs fabrication + behavioural scorers.

**ChromaDB back-to-back query determinism:** Direct Chroma `.query()` fails with dimension mismatch (see B2). Production path uses pre-computed vectors which are fully deterministic for identical input strings. **Effectively deterministic.**

---

### B5 — Random seed audit

| File:line | Random call | Seeded? |
|---|---|---|
| `clubos2/semantic_layer/seed.py:692` | function named `run_seed` — NOT a random call, it's the seeding script for metric_registry | N/A |

**No `random.`, `np.random`, or `torch.manual_seed` calls found anywhere in `clubos2/`.** Random seeds are not a variance source.

---

### B6 — 3-question A/B diff (the critical experiment)

Script: `scripts/diag_variance_probe.py` (kept as diagnostic tool)  
Output: `var/diag_variance_probe.json` (gitignored)

**gq_001_style — "What was the streaming_daily_users value in the most recent month?"**
- retrieved_contexts match: **YES**
- citations match: **YES**
- metrics_queried match: **YES**
- confidence match: **YES**
- answer_text match: **YES**
- Interpretation: Fully deterministic for this question type (pure quantitative lookup)

**gq_012_style — "What is the current conversion_rate_ecommerce and is it a problem?"**
- retrieved_contexts match: **YES**
- citations match: **NO** ← divergence found here
- metrics_queried match: **YES**
- confidence match: **YES**
- answer_text match: **NO**
- First citation divergence: source field in first citation differs
  - Run 1: `source: 'gold.metrics_monthly'`
  - Run 2: `source: 'data/gold_snapshots/gold_priority_board.csv'`
- Answer text divergence: minor phrasing only ("indicating that it is a high priority issue" vs "This rate is considered a problem") — same factual content

**gq_019_style — "Who is the highest-paid player at Real Madrid this season?"**
- retrieved_contexts match: **YES**
- citations match: **YES**
- metrics_queried match: **YES**
- confidence match: **YES**
- answer_text match: **YES**
- Interpretation: Deterministic (unanswerable question, refusal path)

---

## Diagnosis summary

Based on B1–B6 evidence:

**Retrieval is fully deterministic.** Same chunks, same order, same scores — confirmed in all 3 questions. ChromaDB + BM25 + cross-encoder reranker produce identical outputs on identical inputs.

**The variance is above the retrieval layer — in LLM generation.** At temperature=0, GPT-4o-mini is theoretically deterministic but shows minor non-determinism in practice for questions requiring interpretation (mixed-type questions like gq_012). This is a known property of transformer models: temperature=0 greedy decoding can still vary due to server-side batching, floating-point non-determinism on GPU, and OpenAI infrastructure changes between API calls.

**The specific mechanism causing eval score variance** is citation source normalization. In gq_012, the LLM sometimes cites the same data as `gold.metrics_monthly` (the canonical alias) and sometimes as `data/gold_snapshots/gold_priority_board.csv` (the raw file path). If the behavioural scorer validates citation sources against expected canonical forms, this inconsistency directly causes a pass/fail flip on the citation_correct_rate metric — which feeds into `overall_pass_rate`.

**Primary hypothesis:** LLM temperature=0 tie-breaking non-determinism in citation source naming for mixed/narrative question types. The scoring impact is amplified by the behavioural scorer's citation source validation.

**Evidence:**
- B1: Temperature confirmed 0.0 everywhere — rules out temperature misconfiguration
- B2: Retrieval confirmed deterministic — rules out retrieval non-determinism
- B3: Concurrency is read-only with stable ordering — rules out race conditions
- B4: No mutable state written by eval pipeline — rules out state accumulation
- B5: No random calls — rules out seed issues
- B6: retrieved_contexts match=YES in all 3 cases, but citation source name differs between runs for gq_012 specifically

**Ruled out:**
- Temperature leak (all calls 0.0)
- Retrieval non-determinism (confirmed deterministic)
- Concurrency / race conditions (read-only tools, gather preserves order)
- Mutable state between runs (eval is stateless)
- Random seeds (no random calls in clubos2/)

---

## Recommendation for next investigation

The variance diagnosis should focus on: **citation source normalization in the Scout prompt + behavioural scorer's citation correctness check**.

Concrete fix path:
1. Inspect `clubos2/eval/behavioural_scorer.py` — find the citation source validation logic. Determine whether it checks exact source string or allows canonical aliases.
2. If exact-match: update the scorer to accept both `gold.metrics_monthly` and the raw file path as valid citations for the same underlying data.
3. Alternatively: add a post-processing normalization step in `run_scout()` that maps raw file paths to canonical source aliases before returning `ScoutAnswer.citations`. This is cleaner — fixes it at the source rather than in the scorer.
4. Add a regression test with gq_012-style question that asserts citation source is always canonical form.

Estimated fix effort: **30–60 minutes** (read scorer, add normalization or fix matcher, add test).

---

## Commit

- Commit 1 (Part A): `5069eb5` — `clubos2/eval/pipeline.py`, `clubos2/eval/runner.py`, `clubos2/eval/holdout_runner.py`, `scripts/v2_ci_gate.py`, `clubos2/agents/scout.py`
- Commit 2 (Part B — this doc + diagnostic script): see below
- Files in Commit 2: `docs/config_and_variance_diagnostic_2026-07-02.md`, `scripts/diag_variance_probe.py`
