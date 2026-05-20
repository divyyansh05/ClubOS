---
# ClubOS — Technical Requirements Document
**Version**: 1.0
**Status**: Reconstructed from MVP
**Date**: 2026-05-14
**Author**: Divyansh Shrivastava
---

## 1. Technical Vision

ClubOS is built on one engineering premise: **same data in, same output out, every time**. This is not a technical nicety — it is the commercial promise. A digital business lead must be able to defend a ranked priority in a board meeting by pointing to a transparent, reproducible formula. A score that changes every time the notebook reruns, or one produced by an AI model that cannot be interrogated, fails this requirement fundamentally.

This shapes four technical decisions that cascade through every layer of the system:

**Determinism over cleverness.** The priority scoring formula is a fixed weighted sum with documented coefficients. The benchmark gap formula is a deterministic polarity multiplication. Signal validation tests a predefined list of candidate pairs against documented statistical thresholds. None of these computations involve randomness, trained models, or dynamic parameter tuning. Given identical input data, the system must produce byte-identical outputs.

**Explainability at every layer.** Gold tables store intermediate calculations — not just final scores but the five score components that compose them, not just a gap value but the `rm_value`, `peer_median`, and `polarity` used to compute it. The API exposes these components as named fields in typed schemas. The frontend renders every component so that every number on screen is traceable to stored evidence.

**Monthly grain as a hard constraint.** The system is designed around monthly aggregated data. Every table schema uses a `month` column (date precision: first day of month). Every API response includes a `latest_month` field. Every frontend display defaults to the most recent month. Daily granularity is architecturally excluded — there are no daily aggregation pathways, no day-level columns in Gold tables, no UI controls for selecting time windows smaller than one month.

**Independence from live infrastructure.** The backend must function fully without a live Databricks SQL Warehouse connection. Snapshot mode — where Gold tables are served from pre-exported CSV files on the local filesystem — is a first-class operational mode, not a fallback. This means every service function receives the same `list[dict]` data structure regardless of data source, and mode switching is transparent to routers and schemas.

The final principle from `AGENTS.md` encodes all of this in one sentence: **New data in. Same workflow. Clear priorities out.**

---

## 2. System Architecture

### 2.1 High-Level Architecture

ClubOS is a four-layer system. Each layer has a defined input boundary, output boundary, and transformation responsibility. Layers communicate only through their defined interfaces — no layer reads from the layer below its direct predecessor, and no layer writes to any layer above itself.

```
Monthly CSV / Excel files  (analyst uploads to DBFS)
           ↓
 [Layer 1: Data Layer — Databricks]
   Bronze Delta tables   raw ingestion, audit trail
           ↓
   Silver Delta tables   normalized, cleaned, validated
           ↓
   Gold Delta tables     scored, ranked, benchmarked, aggregated
           ↓
 [Layer 2: Service Layer — FastAPI]
   DatabricksClient      reads Gold via SQL or CSV snapshot
   Service modules       filter, aggregate, parse JSON blobs
   Pydantic schemas      validate and type every response
           ↓
 [Layer 3: Presentation Layer — React + TypeScript]
   lib/api.ts            typed fetch wrappers
   Feature pages         render API responses
   MetricDetailModal     drill-down on every number
```

**Layer 1 — Data Layer (Databricks PySpark Notebooks):** Reads raw monthly files from Databricks File System (DBFS), applies three-stage medallion transformation, and produces five Gold Delta Lake tables. Notebooks are the only components allowed to write to Delta tables. Each notebook is idempotent — rerunning on the same data produces the same output. Notebooks communicate only through Delta tables; there is no shared in-memory state between stages.

**Layer 2 — Service Layer (FastAPI):** Reads Gold tables — either by executing `SELECT * FROM {catalog}.{schema}.{table_name}` against a Databricks SQL Warehouse (live mode) or by reading pre-exported CSV files from `data/gold_snapshots/` (snapshot mode). Applies in-Python filtering, aggregation, and JSON blob parsing. Validates every API response against a Pydantic v2 model before returning. Exposes eight REST endpoints on `localhost:8000`.

**Layer 3 — Presentation Layer (React SPA):** Fetches from the FastAPI backend via typed `fetch` wrappers in `lib/api.ts`. Maintains all state locally using React `useState` and `useEffect` — no Redux, no Zustand, no shared global store. Renders five feature screens plus shared layout and modal components. Client-side routing via `react-router-dom v6`.

**Isolation guarantees:**
- Frontend has no knowledge of Delta Lake, PySpark, or Gold table schemas — it only knows Pydantic-validated JSON shapes.
- Backend has no knowledge of Bronze or Silver tables — it only reads Gold outputs.
- Bronze notebooks have no knowledge of business logic — they perform zero transformations beyond metadata enrichment.

---

### 2.2 Architecture Decisions

| Decision | Choice Made | Alternatives Rejected | Rationale |
|----------|------------|----------------------|-----------|
| Data pipeline | Databricks medallion (Bronze→Silver→Gold) | Single ETL script, dbt, Airflow | Medallion separates audit trail (Bronze) from normalization (Silver) from business logic (Gold); each layer independently inspectable; Databricks infrastructure specified by client; Delta Lake adds ACID transactions and time-travel audit capability |
| Scoring logic | Deterministic weighted formula | ML model, GPT-4 auto-scoring, clustering | Stakeholders must defend scores in board meetings; ML scores have no traceable breakdown; AI scores have hallucination risk and API cost; clustering produces no clear ordinal ranking |
| Backend framework | FastAPI + Python 3.11 | Django, Flask, Express | FastAPI auto-generates OpenAPI docs (interactive `/docs` endpoint); native Pydantic v2 integration validates responses at runtime; async-capable without complexity overhead; matches Python 3.11 used in Databricks notebooks |
| Frontend framework | React 18 + TypeScript | Vue 3, Angular, plain JS | React's component model matches five-screen structure naturally; TypeScript catches API contract drift at compile time; Recharts ecosystem integrates cleanly with React's declarative model |
| Data contracts | Pydantic v2 | Manual validation, marshmallow, attrs | Pydantic v2 (Rust core) validates every API response at runtime — schema drift caught before JSON reaches the frontend; auto-generates OpenAPI schemas; integrates natively with FastAPI |
| Dual operating mode | Snapshot mode + Live Databricks mode | Live-only, mock data only | Snapshot mode enables local development without credentials (faster onboarding), offline demos, and isolated test runs; mock data rejected (not realistic); live-only blocks every developer without Databricks access |
| Polarity handling | Stored in metric_dictionary.json, applied in Gold pipeline | Hardcoded if-else, separate "lower-is-better" tables | Dictionary-driven approach scales to any future reverse-polarity metrics without code changes; consistent formula `gap = (rm_value - peer_median) × polarity` applies identically across all 8 benchmarked metrics |
| Signal validation | Three-gate filter (statistical + temporal + business prior) | Test all 52×52 pairs, threshold-only | 2,704 metric pairs would produce high false-positive rate; business prior filter eliminates spurious correlations that are statistically significant but causally backwards or nonsensical |
| State management | React `useState` / `useEffect` only | Redux, Zustand, React Query | Application has no cross-page shared state; all data fetches are per-page; adding a state management library would introduce unnecessary complexity for five read-only screens |

---

## 3. Technology Stack

### 3.1 Data Pipeline

| Technology | Version | Purpose | Why Chosen |
|-----------|---------|---------|------------|
| Python | 3.11.x | Pipeline notebook language | Matches Databricks Runtime 13.x default; strong data science ecosystem; consistent with backend runtime |
| Databricks Runtime | 13.x | Notebook execution environment | Specified by client infrastructure requirement; manages PySpark cluster lifecycle; provides DBFS, Delta Lake, SQL Warehouse |
| PySpark | bundled with Runtime 13.x | Distributed data processing in Bronze/Silver/Gold notebooks | Scales to multi-club deployments without architectural changes; native Delta Lake integration |
| Delta Lake | 2.x | ACID-compliant table format for all pipeline outputs | ACID transactions prevent partial writes from corrupt runs; time travel enables point-in-time audit queries (`VERSION AS OF`); schema evolution handles new metric additions without breaking existing queries |
| pandas | 2.x (in notebooks) | In-notebook data manipulation and CSV export for snapshots | Used in Gold analytics notebooks for correlation calculations and snapshot CSV export |
| scipy / numpy | bundled | Pearson correlation computation in signal validation | Provides `scipy.stats.pearsonr()` for lag-window correlation testing |

### 3.2 Backend

| Technology | Version | Purpose | Why Chosen |
|-----------|---------|---------|------------|
| Python | 3.11.x | Backend runtime | Consistency with pipeline; type hints (3.10+) improve maintainability |
| FastAPI | 0.115.0 | Web framework; router registration; exception handling | Auto-generates OpenAPI docs; native Pydantic v2 integration; lightweight (no ORM, no template engine) |
| Uvicorn | 0.30.6 | ASGI server | `uvicorn[standard]` includes `watchfiles` for `--reload` in development; production-capable single-worker deployment for MVP load |
| Pydantic | 2.8.2 | Runtime schema validation for all API responses | v2 Rust core is 10× faster than v1; validates every response before returning JSON; auto-generates OpenAPI schemas |
| pydantic-settings | 2.3.4 | Environment variable loading | `BaseSettings` reads all configuration from environment or `.env` file; prevents raw `os.getenv()` calls scattered across codebase |
| pandas | 2.2.2 | CSV snapshot reading and in-memory data operations | Reads Gold CSV snapshots; performs in-Python filtering/aggregation that would be SQL in live mode |
| httpx | 0.27.2 | HTTP client in test suite | Async-capable client for pytest-based API contract tests (`TestClient` wrapper) |
| openpyxl | 3.1.5 | Excel file reading | Available for ingestion scripts; not used in current API request handling |
| databricks-sql-connector | not in pyproject.toml | Live Databricks SQL Warehouse queries | Optional dependency — must be installed separately; absence triggers graceful snapshot fallback |

### 3.3 Frontend

| Technology | Version | Purpose | Why Chosen |
|-----------|---------|---------|------------|
| React | 18.2.x | UI component framework | Component model matches five-screen structure; React 18 automatic batching reduces re-renders; large ecosystem |
| TypeScript | 5.x | Type safety across component props and API contracts | Compile-time detection of API schema drift; IDE autocomplete and refactoring support |
| Vite | 5.x | Build tool and development server | Sub-200ms hot module replacement (vs 1–2s with Webpack); native ES modules in development; tree-shaking in production |
| Tailwind CSS | 3.x | Utility-first styling framework | Newsprint design system defined in `tailwind.config.js` (custom fonts, semantic colors, dark mode via `class` strategy); no CSS-in-JS runtime overhead; PurgeCSS removes unused classes (production CSS <10KB) |
| Recharts | 2.x | Data visualisation library | React-native API (no D3.js imperative DOM manipulation); supports all required chart types (line, bar, donut); `ResponsiveContainer` handles viewport resizing automatically |
| react-router-dom | 6.x | Client-side routing | HTML5 history API (clean URLs); `NavLink` provides active state for navigation; nested routes wrap all five pages in `PageShell` |
| @tailwindcss/forms | latest | Form styling plugin | Consistent styled form elements without custom CSS |
| Node.js | 20.16.0 | Frontend build runtime | LTS version pinned in `.nvmrc` for reproducibility across developer machines |

---

## 4. Data Architecture Requirements

### 4.1 Medallion Architecture

**Bronze Layer — Raw Ingestion**

The Bronze layer is the system's immutable audit trail. Bronze notebooks must satisfy these requirements:

- **Zero transformations**: Read raw CSV/Excel files exactly as provided. No column renaming, no null filling, no type casting. Source columns are preserved verbatim.
- **Metadata enrichment only**: Add `ingestion_timestamp` (ISO datetime of notebook execution) and `source_file` (DBFS path of the ingested file). These are the only columns Bronze adds.
- **Append-only writes**: Bronze tables receive new monthly rows on each pipeline run. Historical rows are never updated or deleted.
- **Tables produced**: `bronze.internal_metrics` (four digital platforms) and `bronze.benchmark_metrics` (peer club data).
- **Purpose**: Provides a full audit trail from which any Silver or Gold computation can be reconstructed from source.

**Silver Layer — Normalisation and Cleaning**

Silver notebooks apply business-agnostic data quality transformations. Silver must satisfy these requirements:

- **Column standardisation**: All column names converted to lowercase snake_case. Source inconsistencies in naming (e.g. `UniqueVisitors` vs `unique_visitors`) are resolved here and nowhere else.
- **Null handling**: Missing values are marked as `NULL`. Zero-imputation is forbidden. Forward-fill is forbidden. NULL must propagate through to Gold and be displayed as "—" in the UI.
- **Outlier flagging**: Statistical outliers (metric value > 3 standard deviations from the historical mean for that metric-asset combination) are flagged with an `is_outlier` boolean. Outliers are not removed — they remain in Silver and Gold with the flag set.
- **Deduplication**: Composite key `(month, asset_name, metric_name)` must be unique in Silver. On re-ingestion of the same month, the most recent row wins (upsert by composite key). Duplicate detection is logged to `silver.data_quality_checks`.
- **Tables produced**: `silver.internal_metrics`, `silver.benchmark_metrics`, `silver.data_quality_checks`.
- **Idempotency requirement**: Running Silver notebooks twice on the same Bronze data must produce identical Silver outputs.

**Gold Layer — Business-Ready Outputs**

Gold notebooks compute all business analytics. Gold outputs are the only data the backend API is permitted to read. Gold must satisfy these requirements:

- **Derived only from Silver**: Gold notebooks read exclusively from Silver tables. No direct Bronze reads in Gold notebooks.
- **App-safe outputs**: All values in Gold tables are typed, bounded, and ready for API consumption. No raw text blobs except the pre-structured `supporting_metrics_json` field (which is a documented JSON schema).
- **Five required tables**: `gold_kpi_health`, `gold_peer_benchmark`, `gold_signal_relationships`, `gold_priority_board`, `gold_monthly_brief_inputs`. All five must be populated before the backend can serve a complete response on any screen.
- **Reproducibility**: Same Silver input → same Gold output. Coefficients, thresholds, and formulas are constants in notebook code, not computed from data distributions at runtime.
- **Historical rows preserved**: Gold tables append new monthly rows on each pipeline run. Prior months' rows are never overwritten (except `gold_signal_relationships` where `validation_status` may update to `inactive` on re-validation failure).

**Analytics Notebooks (Gold layer builders):**

| Notebook | Output table | Core operation |
|----------|-------------|----------------|
| `01_build_kpi_health.py` | `gold_kpi_health` | 6-month trend slope, seasonal deviation, health status classification |
| `02_build_peer_benchmark.py` | `gold_peer_benchmark` | Polarity-aware gap calculation, rank assignment |
| `01_validate_signals.py` | `gold_signal_relationships` | Pearson correlation at lag 1/2/3, business prior gate |
| `04_build_priority_board.py` | `gold_priority_board` | Weighted scoring formula, top-50 rank list |
| `05_build_monthly_brief_inputs.py` | `gold_monthly_brief_inputs` | Aggregation of top priorities, signals, benchmark, health |

---

### 4.2 Data Quality Requirements

The quality notebook (`databricks/notebooks/quality/01_run_data_quality_checks.py`) runs after every Silver stage and writes results to `silver.data_quality_checks`. The API exposes these results via `GET /refresh/status`.

**Required validations (REQUIRED severity — pipeline should not proceed if any fail):**

| Check | Description | Fail condition |
|-------|-------------|----------------|
| Schema compliance | All required columns present in Bronze/Silver tables | Any required column missing |
| Row count bounds | Table row count within expected range | Fewer than 90 months or more than 110 months per asset |
| Duplicate detection | Composite key `(month, asset_name, metric_name)` is unique | Any duplicate key |
| Date coverage | No gaps in monthly sequence; all dates within 2017–present | Calendar gap detected or date outside valid range |
| Metric range bounds | Values within plausible limits | `unique_visitors < 0`, `conversion_rate > 1.0`, `bounce_rate > 1.0` |

**Warning validations (WARNING severity — pipeline proceeds but operator is notified):**

| Check | Description |
|-------|-------------|
| Outlier count | More than 10% of rows flagged as outliers for any single metric |
| Null rate | More than 20% nulls in any non-optional column |
| Late data | Month being ingested is more than 45 days after the reference month end |

**Quality table schema** (`silver.data_quality_checks`):

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | string | Unique run identifier (timestamp-based) |
| `check_timestamp` | datetime | When the check ran |
| `table_name` | string | Which table was validated |
| `check_name` | string | Identifier for the specific check |
| `severity` | string | `REQUIRED` or `WARNING` |
| `status` | string | `PASS` or `FAIL` |
| `message` | string | Human-readable description of result |

---

### 4.3 Data Constraints

These constraints are architectural — they are enforced by schema design, not configurable at runtime.

| Constraint | Specification | Engineering rationale |
|-----------|--------------|----------------------|
| Data granularity | Monthly only — `month` column stores first day of month (YYYY-MM-01) | Day-level columns do not exist in any table; no pathway for sub-monthly aggregation |
| Historical depth | 103 months loaded (2017–2026) | Fixed dataset from client data provider; pipeline can extend on new upload but cannot extend beyond available source data |
| Metric registry | 52 metrics in `metric_dictionary.json`; expanding requires a schema change and pipeline update | Gold table schemas reflect the 52 fixed metrics; adding a metric without updating Gold notebooks produces NULL columns |
| Peer benchmark coverage | Exactly 8 metrics across 2 assets; peer gap = 0 for all other metrics | Benchmark CSV from data provider contains only 8 metrics; the system must never claim comparison on metrics absent from that file |
| Peer club set | 5 anonymised clubs: `masia_fc`, `merseyside_red`, `gunners_fc`, `fc_baviera`, `citizens` | Fixed by data provider agreement; `club_count` column in `gold_peer_benchmark` reflects actual count, typically 6 (Real Madrid + 5 peers) |
| Pipeline refresh trigger | Manual analyst upload to DBFS → notebook execution (V1) | No automated ingestion in V1; analysts upload Excel/CSV files and run notebooks manually |
| NULL propagation | NULL in source → NULL in Silver → NULL in Gold → "—" in UI | Zero-imputation is forbidden at all layers; NULL must never be silently converted to 0 or a default value |

---

## 5. Analytics Requirements

### 5.1 Priority Scoring Formula

The priority score is the core product output. It must be computed identically across every pipeline run and every notebook environment.

**Formula:**
```
priority_score = (0.30 × severity)
              + (0.25 × persistence)
              + (0.20 × peer_gap)
              + (0.15 × commercial_weight)
              + (0.10 × supporting_evidence)
```

**All five components must be normalised to [0, 1] before applying weights.** The weighted sum therefore always falls in [0, 1].

| Component | Weight | Input measure | Source table | Normalisation |
|-----------|--------|--------------|-------------|---------------|
| Severity (SEV) | 30% | Absolute value of 6-month trend slope, scaled by metric magnitude | `gold_kpi_health` | Min-max normalised across all metric-asset pairs for the current month |
| Persistence (PER) | 25% | Count of consecutive months with declining trend (max observed = 12) | `gold_kpi_health` | Divided by 12, capped at 1.0 |
| Peer Gap (GAP) | 20% | Absolute `gap_to_peer_median` value, scaled by metric magnitude | `gold_peer_benchmark` | 0.0 for all non-benchmarked metrics; normalised for the 8 benchmarked metrics |
| Commercial Weight (COM) | 15% | Fixed lookup value from metric-commercial importance table | `metric_dictionary` config | Already in [0, 1] by definition |
| Supporting Evidence (EVD) | 10% | Count of validated signals linked to this metric ÷ 5, capped at 1.0 | `gold_signal_relationships` | `min(signal_count / 5, 1.0)` |

**Commercial weight lookup table (embedded in pipeline config):**

| Asset | Metric | Commercial weight |
|-------|--------|------------------|
| ecommerce | net_sales | 1.0 |
| ecommerce | conversion_rate | 0.9 |
| streaming | subscriptions | 0.8 |
| streaming | subscription_rate | 0.7 |
| fan_app | heavy_users | 0.5 |
| fan_app | app_downloads | 0.3 |
| main_website | unique_visitors | 0.4 |
| All others | — | 0.2 (default) |

**Category assignment rules (applied after scoring):**

| Category | Condition |
|----------|-----------|
| `critical` | `priority_score > 0.8` |
| `opportunity` | Positive trend direction AND `peer_gap > 0` (ahead of peers but growing) |
| `benchmark underperformance` | `peer_gap < 0` (metric is in the benchmarked 8 AND below peer median) |
| `warning` | None of the above; score in [0.4, 0.8] |

**Reproducibility requirement**: Score weights are constants in notebook code. Any change to weights must increment the pipeline version number, not be applied dynamically or via a configuration flag that can vary between runs.

---

### 5.2 KPI Health Scoring

KPI health status is computed per metric-asset pair per month and written to `gold_kpi_health`.

**Inputs:**
- 6-month trend slope: linear regression coefficient on the metric's last 6 monthly values
- Volatility: standard deviation of the last 12 months, divided by the rolling 12-month mean (coefficient of variation)
- Persistence count: number of consecutive months where `trend_direction = down`
- Seasonal deviation: `(metric_value - seasonal_baseline) / seasonal_baseline` where `seasonal_baseline` is the average value for this calendar month across all historical years

**Health status assignment (rule-based, no ML):**

| Status | Condition |
|--------|-----------|
| `good` | Positive 6-month slope AND no outlier flag AND abs(seasonal_deviation) ≤ 0.20 |
| `review` | Negative 6-month slope OR persistence_count ≥ 3 OR abs(seasonal_deviation) > 0.20 |
| `stable` | Neither `good` nor `review` — flat slope, deviation within bounds but no positive momentum |

**Deviation index:** The Command Center displays an aggregate `avg_abs_deviation` — the average of `abs(deviation_from_seasonal_baseline)` across all metric-asset pairs for the latest month. Higher values indicate the current month is more unusual than average.

---

### 5.3 Signal Validation Requirements

Leading indicator signals must pass all three validation gates before being published to the product. A signal failing any gate is not stored with `validation_status = active` and does not appear in any API response or UI screen.

**Gate 1 — Statistical threshold:**
- Compute Pearson correlation coefficient (`r`) between source metric time series and target metric time series, shifted by the lag window (1, 2, and 3 months tested).
- Requirement: `abs(r) ≥ 0.60`.
- Signals with `abs(r) < 0.60` at all tested lags are discarded entirely.
- The lag with the highest `abs(r)` above threshold is selected as the published `lag_months` value.

**Gate 2 — Temporal consistency:**
- The correlation direction must hold across the full historical period, not just a specific sub-window.
- Implementation: compute the correlation over rolling 24-month windows. If the sign of `r` flips in more than 20% of windows, the signal fails temporal consistency.
- Protects against spurious correlations caused by a single anomalous event (e.g., COVID disruption creating a temporary reversal).

**Gate 3 — Business prior:**
- Signal must be pre-registered in the candidate list with a documented business justification before correlation testing begins.
- Currently validated candidate pairs: `main_website:unique_visitors → ecommerce:net_sales`, `main_website:bounce_rate → ecommerce:conversion_rate`, `fan_app:heavy_users → streaming:subscriptions`.
- Reverse-direction signals (e.g. `ecommerce:net_sales → main_website:unique_visitors`) are not in the candidate list and cannot pass Gate 3 regardless of statistical strength.
- Rationale: strong correlation does not imply causation or actionability. Business prior filter eliminates statistically valid but commercially meaningless relationships.

**Publication rule:** Only 2–3 signals are published in the MVP. If more than 3 pairs pass all gates, the highest `strength_score` pairs are published and the rest are stored with `validation_status = inactive`.

---

### 5.4 Peer Benchmark Requirements

**Coverage constraint:** The benchmark layer covers exactly the 8 metrics present in the peer benchmark CSV file. Attempting to benchmark any metric not in this set is forbidden — the pipeline must reject such requests rather than compute a gap using unavailable data.

**Gap calculation formula (polarity-aware):**
```
gap_to_peer_median = (rm_value - peer_median) × polarity
gap_to_leader      = (rm_value - peer_leader_value) × polarity
```

Where `polarity` is read from `metric_dictionary.json`:
- `polarity = +1`: higher metric value is better (all metrics except bounce_rate)
- `polarity = -1`: lower metric value is better (bounce_rate only)
- Result interpretation: positive gap = Real Madrid ahead of peers; negative gap = Real Madrid behind peers

**Rank assignment (polarity-aware):**
- For polarity `+1` metrics: rank 1 = highest value among 6 clubs.
- For polarity `-1` metrics: rank 1 = lowest value among 6 clubs.
- Real Madrid is included in the rank calculation (not excluded as a reference point).

**Peer leader value:** The best-in-class value among all 6 clubs, polarity-adjusted. For bounce_rate (polarity -1), `peer_leader_value` is the minimum value (best engagement), not the maximum.

**Historical range:** All 103 available months are stored in `gold_peer_benchmark` for charting 12-month trend views. The frontend slices to the last 12 months for the benchmark trend chart; the API returns all historical points and lets the frontend determine display window.

**Integrity rule:** The backend must return a structured error (422 or 404) if the frontend requests a benchmark for a metric not present in `gold_peer_benchmark`. It must not return empty arrays with a 200 status, which could be mistaken for "no underperformance found."

---

## 6. API Requirements

### 6.1 Performance

Performance targets assume the MVP-scale data volume (~22,000 internal metric rows, ~4,000 benchmark rows, ~1,200 Gold table rows total).

| Endpoint | Mode | Target response time | Observed |
|----------|------|---------------------|----------|
| `GET /health` | Both | < 10ms | < 5ms |
| `GET /health/summary` | Snapshot | < 100ms | < 50ms |
| `GET /health/summary` | Live Databricks | < 500ms | — |
| `GET /priorities/latest` | Snapshot | < 100ms | < 80ms |
| `GET /priorities/latest` | Live Databricks | < 500ms | — |
| `GET /priorities/{id}` | Snapshot | < 100ms | < 60ms |
| `GET /benchmark/{asset}/{metric}` | Snapshot | < 100ms | < 70ms |
| `GET /signals` | Snapshot | < 100ms | < 50ms |
| `GET /briefing/latest` | Snapshot | < 100ms | < 80ms |
| `GET /refresh/status` | Snapshot | < 100ms | < 30ms |

**JSON payload size constraints:**
- All API responses must be under 50KB JSON to ensure sub-second frontend rendering.
- `GET /priorities/latest` is the largest response (10 cards × enriched schema). Current observed size: ~35KB.
- `GET /benchmark/{asset}/{metric}` returns up to 103 historical data points. Current observed size: ~15KB.

**Concurrency:** The MVP backend is single-threaded Uvicorn (no worker processes). It is designed for ~10 concurrent users. Beyond 100 concurrent requests, pandas CSV parsing will saturate CPU. For higher concurrency, a Redis caching layer should be introduced in V2.

---

### 6.2 Error Handling

**Backend error contracts:**

| Scenario | HTTP Status | Response body | Behaviour |
|----------|-------------|---------------|-----------|
| `priority_id` not found in Gold table | 404 | `{"detail": "Priority not found"}` | Router catches `KeyError` from service, raises `HTTPException(404)` |
| Benchmark requested for non-benchmarked metric | 404 | `{"detail": "No benchmark data for this metric"}` | Service returns empty list; router converts to 404 if list is empty |
| `data/gold_snapshots/` directory missing and no Databricks credentials | 503 | `{"detail": "Snapshot data unavailable. Set CLUBOS_GOLD_SNAPSHOT_DIR or Databricks credentials."}` | `SnapshotAccessError` exception handler registered in `main.py` |
| Databricks SQL Warehouse unreachable (live mode) | 503 | `{"detail": "Databricks connection failed."}` | `databricks-sql-connector` raises `DatabaseError`; backend catches, returns 503 |
| Invalid path parameters | 422 | Pydantic validation error JSON | FastAPI handles automatically via path parameter typing |
| Internal service error | 500 | `{"detail": "Internal server error"}` | Traceback logged server-side; generic message returned to client |

**Fallback behaviour when Databricks unreachable:** If live mode is configured but Databricks is unreachable, the backend does not silently fall back to snapshot mode. It returns 503 explicitly. Silent fallback would serve stale data while appearing to serve live data — an unacceptable integrity violation.

**Frontend error handling:** `lib/api.ts` wraps all `fetch` calls. On `!response.ok`, it logs the error to console and re-throws for component-level error boundaries. Components display a user-readable error state (not raw error messages). NULL fields in API responses are displayed as "—" in the UI — never as "0" or blank.

---

### 6.3 Contract Stability

**Pydantic as the contract layer:** Every API response is validated against a named Pydantic v2 model before being returned. This means any schema drift (backend Gold table column renamed, frontend sending wrong field name) surfaces as a runtime `ValidationError`, not a silent type coercion. The Pydantic models in `backend/api/app/schemas/` are the single source of truth for what the API can return.

**Optional fields with `None` defaults:** Fields that may not be present in older historical data (e.g. `rank_change_12m` for months without 12-month prior, `peer_values` for non-benchmarked metrics) are typed as `Optional[T] = None`. The frontend must handle `null` gracefully for all such fields.

**Versioning strategy (V1):** No API version prefix. All routes are mounted at root (`/priorities/latest`, not `/api/v1/priorities/latest`). If breaking schema changes are introduced in V2, a route prefix (`/v2/`) will be added, and the original routes will remain functional until clients migrate.

**CORS configuration:** Fixed origin allowlist — `http://localhost:5176`, `http://127.0.0.1:5176`, `http://localhost:5177`, `http://127.0.0.1:5177`. Wildcard origins are not permitted. Production deployment will require adding the production frontend origin to this list and redeploying.

**Snapshot CSV contract:** When the backend reads Gold CSV snapshots, column names in the CSV must match field names in the corresponding Pydantic schema. A column rename in the Gold table schema (Databricks side) must be reflected in both the CSV export and the Pydantic model simultaneously, or runtime validation will fail on the first API call.

---

## 7. Frontend Requirements

### 7.1 State Management

**Approach:** No global state management library. All state is component-local, managed with React `useState` and `useEffect`. This was chosen because the application is five independent read-only screens — there is no cross-page state to synchronise, no user-generated mutations to track, and no need for server state caching.

**Global state that exists (and how it is handled):**

| State | Mechanism | Scope |
|-------|-----------|-------|
| Dark/light theme | `localStorage.getItem('theme')` + `document.documentElement.classList` | Global — set by `PageShell`, read on every mount |
| WelcomeBanner dismissed | `localStorage.getItem('clubos_welcome_dismissed')` | Global — set once, never reset |
| Active route | `react-router-dom` `useLocation()` + `NavLink` `isActive` | Shell — handled by router |
| Selected metric (Peer Benchmark) | `useState` in `PeerBenchmarkPage` | Page-local |
| Selected signal (Signal Engine) | `useState` in `SignalEnginePage` | Page-local |
| Modal open/closed | `useState` in each feature page | Page-local |
| API data | `useState` in each feature page | Page-local |

**Forbidden patterns:**
- No `window.*` global variables for storing data state.
- No `sessionStorage` for API response caching (stale data risk).
- No prop drilling beyond two levels — if data needs to reach a deeply nested component, restructure or pass through a well-named prop.

---

### 7.2 Data Fetching

**API client:** All backend calls go through `src/lib/api.ts`. No component may call `fetch()` or `axios` directly. The client module exports one named function per backend endpoint.

**Fetch pattern (consistent across all five pages):**
```typescript
// On component mount
useEffect(() => {
  const load = async () => {
    try {
      setLoading(true);
      const data = await getLatestPriorities();  // lib/api.ts function
      setPriorities(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load priorities. Please check the backend is running.');
    } finally {
      setLoading(false);
    }
  };
  load();
}, []);
```

**Loading state requirement:** Every data-fetching component must render a loading state while the API call is in flight. Acceptable implementations: skeleton placeholder, loading spinner, or "Loading…" text. Empty renders while loading are forbidden — they cause layout shift.

**Error state requirement:** Every data-fetching component must render a user-readable error message if the API call fails. The message must not expose raw error strings or stack traces. It must not be a blank page.

**Re-fetch triggers:** In the MVP, data is fetched once on page mount. No polling, no WebSocket, no automatic refresh. The analyst refreshes the page after a new pipeline run to see updated data.

**API base URL:** Hardcoded in `lib/api.ts` as `http://localhost:8000`. This is a deliberate MVP simplicity — the backend and frontend always run on the same machine for V1. Production deployment will require this to be an environment variable injected at build time (`VITE_API_BASE_URL`).

---

### 7.3 Rendering Requirements

**Priority Board rendering:**
- Must render all 10 priority cards from `GET /priorities/latest` in under 2 seconds from API response receipt.
- Category filter buttons must filter the rendered card list client-side without a new API call.
- Recharts components (`LineChart`, `BarChart`) inside the evidence modal must render without blocking the main UI thread. Use `React.lazy` or conditional rendering if chart complexity increases.
- At >50 simultaneous priority cards, React reconciliation slows measurably. The MVP caps at 10 cards by design — if this limit is raised, implement `react-window` virtualised list.

**Theme persistence:**
- Theme (dark/light) must be applied before first render to prevent flash of unstyled content (FOUC). The `PageShell` `useEffect` reads `localStorage.theme` on mount — this runs after the initial render, meaning a brief flash on first load is possible. A V2 improvement is to read and apply the theme in a `<script>` tag in `index.html` before React mounts.
- Once set, theme must persist across page navigation, browser tab close-and-reopen, and hard refresh.

**NULL display contract:**
- Any API field typed `Optional[T]` that arrives as `null` in the JSON response must be displayed as "—" in the UI. It must not be displayed as "0", "null", "undefined", or left blank.
- Components must have explicit null-checks before rendering optional fields. TypeScript's optional chaining (`?.`) and nullish coalescing (`?? '—'`) must be used consistently.

**Chart responsiveness:**
- All Recharts components must be wrapped in `<ResponsiveContainer width="100%" height={N}>`. Fixed-pixel chart widths are forbidden — they break layout on non-standard monitor widths.
- Charts must not throw errors when `data` prop is an empty array — all chart components must handle empty data gracefully (display an empty-state message, not a JavaScript error).

**Frontend bundle size:**
- Target: < 200KB gzipped (currently ~150KB).
- No new heavy dependencies may be added without auditing their bundle impact. `lodash` is forbidden — use native JavaScript equivalents. `moment.js` is forbidden — use `Intl.DateTimeFormat` or `date-fns`.

---

## 8. Testing Requirements

### 8.1 Test Coverage

The MVP includes 23 regression tests across three categories. All 23 must pass before any deployment or demo.

| Test Type | File | Count | What it validates |
|-----------|------|-------|------------------|
| Gold snapshot validation | `tests/data/validate_gold_snapshots.py` | ~8 | CSV files exist; column names match expected schema; no duplicate primary keys; required fields non-null; row count within expected range |
| API contract tests | `backend/api/tests/test_api_contracts.py` | ~12 | HTTP 200 for all success endpoints; HTTP 404 for invalid `priority_id`; JSON response structure matches Pydantic schema; CORS headers present on all responses; `latest_month` field present and valid ISO date |
| UI smoke tests | `tests/ui/smoke_test.sh` | ~3 | Each of the five frontend page URLs returns HTTP 200; `<title>ClubOS</title>` tag present in response (confirms Vite served the SPA, not a 404 fallback) |

**API contract test specifics:**
- Uses `pytest` with `httpx.TestClient` wrapping the FastAPI app.
- Tests run against the snapshot mode backend (no live Databricks required).
- Validates that every field in the Pydantic response model is present in the JSON response with the correct type.
- Validates that `Optional` fields are either correctly typed or `null` — never absent.

**Snapshot validation specifics:**
- Validates that all six CSV files in `data/gold_snapshots/` are present.
- Checks that `gold_priority_board.csv` has column `priority_score` with values in [0, 1].
- Checks that `gold_peer_benchmark.csv` has no rows with `metric_name` outside the 8 benchmarked metrics.
- Checks that `gold_signal_relationships.csv` has no rows with `strength_score < 0.6` (invariant of the validation pipeline).

---

### 8.2 Test Commands

```bash
# Run all 23 regression tests
./scripts/run_all_tests.sh

# Run API contract tests only
pytest backend/api/tests/ -v

# Run Gold snapshot validation only
python tests/data/validate_gold_snapshots.py

# Run UI smoke tests only (requires frontend dev server running on port 5176)
bash tests/ui/smoke_test.sh
```

**Test environment requirements:**
- Backend must be running (`uvicorn app.main:app --reload`) on port 8000.
- `data/gold_snapshots/` must contain all six CSV files.
- Frontend dev server must be running (`npm run dev`) on port 5176 for UI smoke tests.
- No live Databricks credentials required for any test category.

---

### 8.3 Definition of Test Pass

The test suite is considered passing when:

1. All `pytest` tests in `backend/api/tests/` exit with `0 failed`.
2. `validate_gold_snapshots.py` exits with status code `0` and prints no `FAIL` lines.
3. `smoke_test.sh` receives HTTP 200 on all five frontend page URLs.

**Zero tolerance policy:** No test may be marked `xfail` or `skip` in the MVP codebase without a documented blocking reason. A skipped test in the contract suite is equivalent to an untested API contract. All 23 tests must be green before the demo date.

**Test failure triage:**
- Gold snapshot validation failure → schema drift between CSV and Pydantic model; requires CSV re-export or Pydantic model update.
- API contract failure → service function returning wrong type or missing field; fix in service module, not schema.
- UI smoke failure → frontend dev server not running, or Vite config changed the build output; check server status before re-running.

---

## 9. Security Requirements (V1)

**No authentication in V1.** This is an explicit, documented scope decision. The application has no login screen, no session management, and no access tokens. Anyone with the URL can access all data. The consequence is that the application must not be deployed to a public internet address — it is an internal tool accessible only on a private network or local machine.

**Credential isolation:**
- `CLUBOS_DATABRICKS_TOKEN` and all Databricks credentials are loaded exclusively from environment variables or a `.env` file at the backend working directory.
- `.env` files are in `.gitignore` — they must never be committed to version control.
- No credentials appear in any source code file, API response, frontend bundle, or log output.
- The frontend bundle (compiled JavaScript) must not contain any Databricks credentials. The frontend has no Databricks credentials and does not need them.

**No sensitive data in version control:**
- `data/source/` (raw client data files) is in `.gitignore`.
- `data/gold_snapshots/` CSVs — if they contain real Real Madrid commercial data — should also be excluded from version control. Snapshot CSVs for demo use contain representative but non-sensitive values.
- `agents/` directory (internal AI agent configuration) is in `.gitignore`.
- `docs/research/` and `docs/delivery/` (internal strategy documents) are in `.gitignore`.

**API security surface:**
- No write endpoints exist — the API is 100% read-only (`GET` methods only).
- No user input is accepted by the API (no POST bodies, no free-text query parameters). Path parameters (`asset`, `metric`, `priority_id`) are validated by FastAPI's type system.
- SQL injection is not a risk in live Databricks mode because `_read_live()` constructs only `SELECT * FROM {catalog}.{schema}.{table_name}` — no user-supplied values are interpolated into SQL strings.
- CORS allowlist prevents cross-origin requests from arbitrary websites.

**V2 security roadmap:**
- SSO via Okta, Auth0, or Google Workspace OAuth
- Role-based access control: viewer (read-only) vs. admin (can trigger pipeline refresh)
- API rate limiting (prevent abuse on multi-user deployment)
- HTTPS enforcement (TLS termination at reverse proxy)
- Audit logging (who viewed which priority, when)

---

## 10. Known Technical Limitations

These limitations are accepted constraints of the MVP. Each entry documents the root cause (why it exists), its impact (what breaks or degrades), and the V2 resolution path.

| # | Limitation | Root Cause | Impact | V2 Resolution |
|---|-----------|-----------|--------|---------------|
| 1 | No authentication or authorisation | Scoped out of MVP to reduce delivery complexity; internal-tool assumption for V1 | Application cannot be deployed to public internet; anyone with URL can access sensitive commercial data | SSO via Okta/Auth0; role-based access control (viewer vs. admin); session tokens |
| 2 | Single-threaded Pandas serving (no connection pool) | Snapshot mode reads CSV files on each request with no caching; live mode opens one SQL connection per request | CPU saturation at ~100 concurrent requests; Pandas CSV re-parse on every GET call is redundant | Redis caching layer — parse DataFrames once, evict on pipeline refresh signal; connection pooling for live Databricks |
| 3 | Monthly data cadence only | Source data from client analytics platform is monthly-aggregated; pipeline schemas have no day-level columns | Cannot detect intra-month issues; a week-3 conversion rate drop is invisible until month end | Weekly ingestion for critical metrics (`conversion_rate`, `net_sales`); add `week` column to Silver/Gold schemas |
| 4 | Manual data upload workflow | No API connector to client analytics platform; Databricks ingestion trigger is manual | Human error risk on upload (wrong file, corrupt data, missed month); dependency on analyst availability | Automated monthly pull via analytics platform API or scheduled DBFS ingestion; upload validation before Bronze write |
| 5 | Only 3 signal candidate pairs tested | Business prior gate limits testing to pre-registered pairs; MVP conservative on signal count | May miss commercially significant leading indicators (e.g. social engagement → streaming subscriptions) | Expand candidate list to 10–15 pairs based on domain expertise; add temporal validation dashboard for ongoing signal monitoring |
| 6 | Event Intelligence not integrated into UI | `event_annotations.csv` seed exists and `03_build_event_windows.py` notebook exists but Priority Board has no event context layer | Users see anomalies without business context (cannot distinguish "conversion drop = product issue" from "conversion drop = holiday") | Build Event Intelligence module; annotate Priority Board cards and anomaly table with overlapping event windows |
| 7 | No email alerts or push notifications | Out of scope for V1; requires email service integration (SendGrid, SES) | Users must manually check dashboard after each pipeline run; critical issues may go unnoticed for days | Email alerts for `critical` priority cards (score > 0.8); weekly digest with top 3 priorities; webhook-based integration option |
| 8 | Single club only (Real Madrid hardcoded) | No `club_id` dimension in internal metrics schema; all Gold tables implicitly assume one club | Cannot deploy ClubOS for a second club without a full schema migration and separate Databricks workspace | Add `club_id` to internal metrics schema; multi-tenant architecture; club-level RBAC; parameterise benchmark peer set per club |
| 9 | No export capabilities | Not implemented in MVP; requires PDF generation library or CSV download handlers | Stakeholders copy-paste priority data into PowerPoint (manual, error-prone); no version-controlled exported reports | PDF export for monthly briefing (ReportLab/WeasyPrint); CSV download for all table views; shareable priority deep-link URLs |
| 10 | Databricks vendor lock-in | Pipeline tightly couples to Delta Lake, PySpark notebooks, and Databricks SQL Warehouse; no abstraction layer | Cannot migrate to Snowflake, BigQuery, or Spark-on-Kubernetes without full pipeline rewrite | Abstract data layer behind `read_table()`/`write_table()` interfaces; support Delta Lake, Parquet, and PostgreSQL backends interchangeably |
| 11 | Peer benchmark limited to 8 of 52 metrics | Peer data provider contract covers only 8 metrics across 2 assets; no peer data exists for the other 44 | Priority scoring peer_gap component = 0 for 85% of metrics; system cannot contextualise streaming or fan app underperformance against peers | Renegotiate data provider agreement to cover 20+ metrics; alternatively, compute synthetic peer benchmarks from publicly available club traffic estimates (lower confidence) |
| 12 | React DOM lag at >50 priority cards | No virtualised list in MVP; React reconciles all card DOM nodes simultaneously | Priority Board would visibly lag at 50+ cards; current max is 10 by design constraint | Implement `react-window` virtualised list for Priority Board; enables displaying full top-50 without DOM performance degradation |
| 13 | Databricks notebook 15-minute timeout at scale | Default Databricks job timeout applies; sequential notebook execution; single-node cluster | Full pipeline (Bronze→Gold) for 1 club takes ~2 minutes now, but would exceed 15 minutes at 50 clubs × 200 metrics | Parallelise Bronze ingestion (one notebook per club); partition Gold tables by `club_id`; upgrade to multi-node Spark cluster for large-scale runs |
| 14 | Snapshot CSV staleness risk | No automatic sync between Gold Delta tables (Databricks) and CSV exports (`data/gold_snapshots/`) | Developer working in snapshot mode may serve data that is weeks out of date without knowing it; schema drift between CSV and Pydantic model causes runtime ValidationErrors | Automate CSV export as part of pipeline completion step; add snapshot freshness check to `GET /refresh/status`; document manual refresh procedure in ENV_SETUP.md |
| 15 | No AI integration in current MVP | AI provider configured via `CLUBOS_AI_PROVIDER` and `CLUBOS_AI_API_KEY` env vars but not called by any service | Monthly briefing summaries and priority card explanations are deterministic-template strings, not AI-generated prose | Wire AI provider to briefing generation; add guardrails (summaries ground AI prompts in Gold table inputs); ensure deterministic fallback if AI service unavailable |

---

## Appendix A: Shared Engineering Rules (from AGENTS.md)

These seven rules govern all engineering decisions in ClubOS and take precedence over implementation convenience:

1. **Prefer deterministic logic over cleverness.** A simple weighted formula that can be explained is worth more than a sophisticated model that cannot.
2. **Keep all scoring logic inspectable.** Every priority score must expose its five component values. No output is a black box.
3. **Store intermediate calculations for trust and debugging.** Gold tables contain not just final scores but the inputs that produced them (`severity_inputs`, `persistence_inputs`, `peer_context` fields in `supporting_metrics_json`).
4. **Use stable schema names and canonical metric names.** `conversion_rate` in Bronze, `conversion_rate` in Silver, `conversion_rate` in Gold, `conversion_rate` in API JSON, `conversion_rate` in frontend display. No synonyms, no abbreviations in different layers.
5. **Use typed contracts between layers whenever possible.** Pydantic schemas between backend and frontend; Delta Lake Delta schemas between pipeline stages; TypeScript interfaces between API client and React components.
6. **Every recommendation in the UI must be traceable to stored evidence.** A "View Evidence" button must open a panel backed by real Gold table data. No UI element may claim a relationship or trend that is not computed and stored.
7. **When a metric or relationship is weak, hide it rather than forcing it into the product.** If a signal fails any validation gate, it does not appear. If a metric lacks peer benchmark data, the peer gap component is zero (not estimated). Conservative publication builds stakeholder trust; spurious insights destroy it.

---

## Appendix B: Build Sequence

From `AGENTS.md` — the order in which ClubOS components must be built (later steps depend on earlier steps being complete and validated):

| Step | Component | Dependency |
|------|-----------|-----------|
| 1 | Data contract and metric inventory | None |
| 2 | Bronze ingestion | Step 1 (schema must exist before ingestion) |
| 3 | Silver normalisation and validation | Step 2 (Bronze tables must exist) |
| 4 | Gold benchmark and KPI health outputs | Step 3 (Silver tables must exist) |
| 5 | Signal validation | Step 4 (Gold KPI health needed for trend inputs) |
| 6 | Priority scoring logic | Steps 4 and 5 (benchmark gaps and signals needed as scoring inputs) |
| 7 | Backend API | Step 6 (Gold tables must be fully populated) |
| 8 | Frontend product shell | Step 7 (API must be running and returning data) |
| 9 | AI summaries | Step 8 (briefing screen must exist before AI wording can be added) |
| 10 | Tableau support layer | Step 6 (Gold tables must be stable; Tableau reads Gold directly) |

---
