---
# ClubOS — Product Requirements Document
**Version**: 2.0
**Status**: Production MVP deployed on Cloud Run
**Date**: 2026-05-14
**Author**: Divyansh Shrivastava
---

## 1. Executive Summary

ClubOS is a monthly digital business operating system for elite football clubs that ingests recurring data from four digital platforms, processes it through a Databricks medallion pipeline, and delivers ranked priorities, peer benchmarks, and validated commercial signals. It solves the problem of disconnected, manually produced monthly reporting across website, eCommerce, streaming, and fan app channels — replacing spreadsheet analysis with a deterministic, recurring decision workflow. Primary users are the digital business lead, commercial lead, and digital analyst at the club.

---

## 2. Problem Statement

### 2.1 The Current State

Elite football clubs managing multiple digital businesses — website, eCommerce, streaming, and fan app — currently operate without a unified monthly view. Analysts manually review separate spreadsheets per platform, copy metrics into comparison files, and write summary reports from scratch each month. There is no system that ranks which issues deserve attention first: a declining conversion rate, a persistent bounce rate problem, and a peer gap in subscriptions all sit in separate files with no mechanism to compare urgency. Peer club data exists but is not operationalized into a recurring comparison workflow — analysts look it up separately and interpret it manually. Leading signals that predict commercial outcomes months in advance are buried inside disconnected asset-level exports and are never surfaced systematically. Leadership has no single recurring view of what changed this month that actually matters.

### 2.2 The Opportunity

With ClubOS, the same monthly data files that currently produce manual reports instead feed an automated pipeline. The system recalculates health trends, peer gaps, and signal relationships every time new data arrives. The Priority Board surfaces which metric-asset combinations deserve investigation first, with transparent score breakdowns. Peer benchmark positions refresh automatically, giving the digital team a live view of competitive standing across eight shared KPIs. Leading indicators identified through lagged correlation analysis allow commercial leads to anticipate revenue trends 1–3 months before they fully materialize. Analysts run one workflow instead of producing custom reports; leadership reads one briefing instead of reviewing multiple platform summaries.

---

## 3. Product Vision

ClubOS is a recurring monthly operating system, not a dashboard. Where a dashboard shows what happened, ClubOS tells the club what to act on next. The core design principle is: new data in, same workflow, clear priorities out. When next month's files are uploaded, the pipeline recalculates every score, gap, and signal automatically, and the same five screens reflect the updated state of the business — no manual chart creation, no formula copying, no bespoke storytelling. This repeatability is the product's commercial value: an analyst workflow that scales across months without additional effort, and a leadership interface that always answers "what deserves attention first" from evidence, not intuition.

---

## 4. Target Users

| User | Role | Primary Need |
|------|------|-------------|
| Digital Business Lead | Owns overall digital performance across all four platforms | One consolidated monthly view of digital health and peer position |
| Commercial Lead | Responsible for revenue outcomes across eCommerce, streaming, and sponsorship | Identify which digital behaviors precede stronger or weaker commercial results |
| Digital Analyst | Produces monthly reporting and maintains data pipelines | Eliminate repetitive manual reporting; generate structured monthly summaries backed by evidence |
| Marketing Lead | Oversees campaign effectiveness across digital channels | Understand which traffic sources drive commercial outcomes |
| eCommerce Manager | Manages online merchandise sales and conversion | Track conversion rate health and peer benchmark standing |
| Streaming / Content Lead | Manages video platform subscriptions and engagement | Monitor subscriber growth signals and content engagement trends |

---

## 5. Scope

### 5.1 In Scope — Version 1

- Monthly CSV ingestion for four digital platforms: main website, eCommerce, streaming, fan app
- Bronze → Silver → Gold medallion pipeline on Databricks with Delta Lake tables
- Silver normalization: lowercase snake_case standardization, null handling, outlier flagging, deduplication
- Gold KPI health computation: trend direction, volatility, persistence scoring per metric-asset pair
- Gold peer benchmark: rank, gap to median, 12-month gap movement for 8 benchmarked metrics across 5 peer clubs
- Gold signal relationships: Pearson correlation testing at 1–3 month lags, business prior validation, strength threshold 0.6
- Gold priority board: weighted scoring formula across severity, persistence, peer gap, commercial weight, supporting evidence; top 10 ranked priorities
- Gold monthly briefing inputs: aggregated top 3 priorities, top 4 signals, benchmark summary, health summary
- Polarity-aware benchmark gap calculation (lower is better for bounce_rate; system inverts logic automatically)
- Local snapshot mode: app functions without live Databricks credentials using pre-computed CSV snapshots
- React web application with eight screens: Priority Board, Command Center, Peer Benchmark, Signal Engine, Monthly Briefing, Social Intelligence, Event Calendar, and Connectors
- Priority Board as default landing screen with category labels (critical, opportunity, benchmark, warning)
- Drill-down modals: every number in the UI is clickable and opens a plain-language explanation
- Score decomposition: every priority score shows the five weighted components
- Data quality checks notebook: validates schema compliance, row counts, duplicates, date coverage for all pipeline stages
- 59-metric registry with polarity definitions (metric_dictionary.json)
- 103 months of historical data across all four platforms
- Five anonymised peer clubs: masia_fc, merseyside_red, gunners_fc, fc_baviera, citizens
- AI-generated wording for monthly briefing summaries and priority card explanations (summaries only — not scoring logic)
- Newsprint design system: dark-themed, professional, production-grade visual presentation
- Event Intelligence screen mapping real-world events to metric trends
- Public cloud deployment and CI/CD via Google Cloud Run and GitHub Actions
- 28 regression tests covering core pipeline and API behaviour

### 5.2 Out of Scope — Version 1

- User authentication and role-based access control
- Automated monthly alerts or push notifications
- PDF or PowerPoint export of player or monthly briefing content
- Open-ended AI assistant or conversational Q&A interface
- Scenario simulation or what-if modelling
- Multi-club deployment (currently hardcoded for Real Madrid context)
- Weekly or daily data cadence — monthly only
- Day-level precision or short-window campaign optimisation
- Tableau support layer (identified as secondary visualisation option; not built in MVP)
- AI-driven priority ranking (deterministic scoring only — AI cannot be the core ranking logic)
- Broader peer network beyond the five clubs in the provided dataset

---

## 6. Functional Requirements

### 6.1 Core Workflow

The monthly data refresh cycle operates as follows:

1. New monthly CSV files are uploaded to Databricks File System (DBFS) for all four digital platforms plus the peer benchmark file
2. Bronze ingestion notebooks read raw files with zero transformations; add ingestion timestamp and source file metadata
3. Silver normalization notebooks standardize column names, handle nulls explicitly (never zero-impute), flag statistical outliers (>3 standard deviations from historical mean), deduplicate by composite key `(month, asset_name, metric_name)`
4. Gold analytics notebooks compute KPI health scores, peer benchmark gaps, signal relationships, and priority scores
5. Gold priority board notebook ranks all metric-asset combinations by weighted score; top 10 become Priority Board entries
6. Gold monthly briefing inputs notebook aggregates top items across all Gold tables
7. Backend API reads Gold tables (live Databricks SQL Warehouse or local CSV snapshots in fallback mode)
8. React frontend reflects updated state across all five screens without any manual intervention

The pipeline must be idempotent: rerunning on the same data produces the same outputs.

### 6.2 Priority Board Requirements

- Rank all metric-asset combinations by weighted priority score; surface top 10 as the Priority Board
- Priority Board must be the first screen the user sees on load
- Each priority card must display: metric name, digital asset, priority score (0–1), category label, short description of what is happening, breakdown of the five score components, peer context where benchmark exists, suggested next investigation
- Category labels: **critical** (score > 0.8), **opportunity** (positive trend with peer gap), **benchmark** (peer-driven underperformance), **warning** (moderate concern)
- Score formula (deterministic, not AI-generated):
  ```
  priority_score = (0.30 × severity) + (0.25 × persistence) + (0.20 × peer_gap) + (0.15 × commercial_weight) + (0.10 × supporting_evidence)
  ```
- All inputs normalized 0–1 before scoring (Severity uses Seasonal Z-Score deviation rather than static rolling average)
- Commercial weight lookup: eCommerce net_sales = 1.0, streaming subscriptions = 0.8, eCommerce conversion_rate = 0.9, fan app downloads = 0.3 (full lookup table in config)
- Supporting evidence = count of validated signals connected to this metric ÷ 5, capped at 1.0
- Peer gap = 0 for any metric not in the 8 benchmarked metrics

### 6.3 Peer Benchmarking Requirements

- Benchmark layer covers exactly 8 metrics across 2 digital assets:
  - Main Website: unique_visitors, visits, bounce_rate, recurrence
  - eCommerce: unique_visitors, visits, conversion_rate, net_sales
- Five peer clubs: masia_fc, merseyside_red, gunners_fc, fc_baviera, citizens
- Outputs per benchmarked metric: current rank among 6 clubs (Real Madrid + 5 peers), peer median, gap to peer median, 12-month gap movement chart, gap to leader
- Polarity-aware gap calculation: for bounce_rate (polarity = -1), lower values are better; gap logic inverts so that a higher bounce rate than peer median registers as a negative gap
- One resilience comparison view showing shared event windows (e.g. COVID impact month)
- Benchmark layer must not claim comparison on metrics not present in the peer file

### 6.4 Signal Detection Requirements

- Test every metric-asset pair for Pearson correlation at lag windows of 1, 2, and 3 months
- Minimum correlation threshold: 0.6 (absolute value) to qualify as a validated signal
- Business prior gate: signal must be explainable in business language before publication
- Directional consistency check: relationship direction must hold over time, not be an artefact of a single event window
- Only 2–3 validated signals published in the MVP; do not publish a large signal library
- Each published signal displays: source metric, target commercial metric, lag window in months, direction (positive/negative), correlation strength (0–1), plain-English business interpretation
- If a signal fails any validation condition, it does not appear in the product

### 6.5 Monthly Briefing Requirements

- Auto-generated on every pipeline refresh — no manual authoring required
- Contents:
  - Top 3 priority issues or opportunities from the Priority Board
  - Top 4 validated signals with strength and lag
  - Benchmark summary: count of underperforming metrics, average gap to peer median, worst single gap
  - Health summary: count of metrics by status (Good / Review Needed / Stable)
  - Summary of latest month changes versus seasonal expectation
- AI may be used for natural language wording of the briefing after deterministic logic produces the inputs
- If AI is unavailable, briefing must still generate from deterministic templates — AI is not a hard dependency

### 6.6 Data Requirements

- Four monthly CSV inputs: main_website, ecommerce, streaming, fan_app
- One monthly peer benchmark CSV: five clubs × 8 metrics × monthly grain
- Bronze tables: raw ingestion, zero transformations, audit trail preserved
- Silver tables: normalized, cleaned, validated, deduplicated
- Gold tables: `gold.kpi_health`, `gold.peer_benchmark`, `gold.signal_relationships`, `gold.priority_board`, `gold.monthly_brief_inputs`
- Snapshot mode: pre-computed Gold CSV exports allow full app demo without live Databricks credentials; backend reads CSV files if Databricks connection fails
- Historical depth: 103 months of data across all four platforms
- 59 tracked metrics across all assets; polarity registered in metric_dictionary.json for all 59
- NULL handling: mark missing values as null; never zero-impute; display as "—" in the UI

---

## 7. Non-Functional Requirements

| Requirement | Specification |
|-------------|--------------|
| Data granularity | Monthly only — no day-level or week-level precision |
| Scoring logic | Deterministic weighted formula — not AI-generated, not heuristic |
| AI role | Natural language summaries and explanations only — AI cannot determine ranking or scoring |
| Fallback mode | Full app must function without live Databricks credentials via CSV snapshot mode |
| Explainability | Every priority score must expose a five-component breakdown; no black-box outputs |
| Polarity handling | Benchmark gaps must invert for negative-polarity metrics (bounce_rate); system handles this automatically |
| Pipeline idempotency | Rerunning notebooks on the same data must produce identical outputs |
| Score reproducibility | Same input data must always produce the same priority ranking — no randomness |
| Peer benchmark integrity | Benchmark layer must never claim comparison on metrics absent from the peer dataset |
| Signal conservatism | Only publish signals passing all three gates: statistical (r ≥ 0.6), temporal consistency, business prior |

---

## 8. Success Metrics

ClubOS is working correctly when:

- A new monthly CSV file can be uploaded and processed end-to-end without any code changes or manual chart editing
- All five required Gold outputs refresh automatically after each pipeline run
- The Priority Board surfaces the top 10 ranked issues from the latest month with correct score breakdowns
- Peer benchmark positions update to reflect the most recent month and display polarity-correct gap values
- The signal module shows only the 2–3 validated indicators that passed all three validation gates
- The monthly briefing generates automatically from refreshed Gold data without manual authoring
- The app feels operational: a digital business lead can open it and immediately see what deserves attention this month
- Analysts report reduced time spent on manual monthly summary production
- Every priority score is traceable to its five weighted components — no output is unexplained

---

## 9. Constraints and Assumptions

- Data is monthly only — ClubOS will not claim daily granularity or support campaign-level timing decisions
- Benchmark layer is limited to exactly 8 metrics present in the peer benchmark dataset — no extrapolation beyond what the data supports
- Peer set is fixed at 5 clubs — small peer set limits statistical confidence; this is an accepted constraint of the current data
- Python 3.11 and Databricks Free Edition infrastructure
- Scoring logic must remain deterministic — changes to weights require explicit versioning, not dynamic AI adjustment
- AI cannot be a hard dependency — the system must function fully if AI services are unavailable
- Real Madrid context is assumed for V1 — club-specific constants (team identity, benchmark peers) are embedded and not configurable through the UI
- Monthly cadence is fixed — the product is not designed for real-time or near-real-time data feeds
- 59-metric registry is the complete metric set; expanding it requires a new data contract and pipeline update

---

## 10. Rejected Alternatives

| Alternative | Why Rejected |
|-------------|-------------|
| Tableau / Power BI | Can visualize data but cannot automatically rank priorities or compute polarity-aware peer gaps; requires analysts to build new charts every month; does not scale across 59 metrics × 4 assets × 103 months |
| Excel macros | Fragile against column name changes, cannot handle Databricks-scale data processing, no web interface for stakeholders to self-serve, breaks when file structure shifts |
| AI auto-scoring (GPT-4 generates priorities) | Not auditable, not reproducible, cannot be defended in board meetings; stakeholders need traceable breakdowns for why eCommerce conversion rates outranks streaming engagement |
| Generic BI + manual analyst interpretation | Does not reduce analyst time; still requires bespoke monthly storytelling; no recurring priority ranking; no automated briefing |
| Static one-time dashboard | Demonstrates historical insight once but does not function on next month's data; not a product — a report |

---
