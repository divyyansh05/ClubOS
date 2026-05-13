# ClubOS MVP Specification

## Objective

This document defines the strict MVP for ClubOS.

The MVP is the smallest version of the product that:

- proves the product is a recurring monthly operating system
- demonstrates clear business value to Real Madrid
- supports the strongest buy case from the current data
- is realistic to build and demo convincingly

This MVP is intentionally narrower than the long-term product vision.

## 1. MVP Product Promise

After each monthly data upload, ClubOS should automatically:

- refresh the health view of the four digital businesses
- update peer benchmark positions on supported KPIs
- recalculate the top business priorities
- surface 2-3 evidence-backed leading signals
- generate a monthly business briefing

The MVP is successful if it can do this repeatedly on the same data structure.

## 2. MVP Business Questions

The MVP must answer these questions reliably:

1. What are the most important issues or opportunities this month?
2. Where is Real Madrid ahead or behind peers on benchmark-supported KPIs?
3. Which internal digital signals tend to precede stronger or weaker commercial outcomes?
4. What changed this month compared to seasonal expectation and recent history?

Anything outside these four questions is secondary.

## 3. MVP Users

Primary users:

- Digital business lead
- Commercial lead
- Digital analyst

The MVP should optimize for these three user types only.

## 4. MVP Modules

The MVP includes five modules.

### 4.1 Priority Board

This is the hero module.

Required outputs:

- top 5 ranked issues or opportunities for the latest month
- priority score
- short description
- why it is ranked
- supporting metrics
- peer context where available
- suggested next investigation

This module must be the first screen in the app.

### 4.2 Command Center

Required outputs:

- one status card per digital asset:
  - main website
  - eCommerce
  - streaming
  - fan app
- latest period value
- trend versus prior month
- trend versus prior season equivalent
- seasonal position indicator

This module exists to provide overall context, not to drive the buy case.

### 4.3 Peer Benchmark Engine

Required outputs:

- current rank for benchmark-supported KPIs
- peer median
- gap versus peer median
- 12-month movement in gap
- one resilience comparison view for a shared event window such as COVID

The MVP benchmark layer must remain strictly within the metrics actually supported by the benchmark file.

### 4.4 Commercial Signal Engine

Required outputs:

- 2 or 3 validated leading indicators only
- each indicator must show:
  - source metric
  - target commercial metric
  - lag window in months
  - direction of relationship
  - plain-English explanation

The MVP must not include a large signal library. Keep only the strongest results.

### 4.5 Monthly Briefing

Required outputs:

- summary of latest month
- top 3 notable changes
- top 3 priorities
- one short benchmark summary
- one short signal summary

This can be generated with deterministic templates first, with optional AI support for wording.

## 5. MVP KPI Set

The MVP should use a restricted KPI set.

### 5.1 Main Website

- unique_visitors
- visits
- bounce_rate
- recurrence

### 5.2 eCommerce

- net_sales
- conversion_rate
- cart_value
- checkout_rate

### 5.3 Streaming

- subscriptions
- subscription_rate
- streamers_rate
- video_play_rate

### 5.4 Fan App

- app_downloads
- matchday_visits
- heavy_users
- recurrence

These KPIs are enough to support the MVP without overextending the scope.

## 6. Priority Board Logic

Each priority should be scored from transparent factors.

### 6.1 Score Components

- **severity**
  - size of deviation from seasonal norm
- **persistence**
  - number of consecutive months the issue or opportunity persists
- **peer_gap**
  - distance from peer median or leader when benchmark is available
- **commercial_weight**
  - importance of the metric to revenue, conversion, subscription, or growth
- **supporting_evidence**
  - confirmation from related metrics

### 6.2 MVP Score Formula

The exact weights can be tuned later, but the MVP should use a simple weighted sum:

`priority_score = 0.30*severity + 0.20*persistence + 0.20*peer_gap + 0.20*commercial_weight + 0.10*supporting_evidence`

Use normalized values from 0 to 1 for each component before scoring.

### 6.3 MVP Priority Categories

All priorities in the MVP should fall into one of these categories:

- growth risk
- conversion weakness
- benchmark underperformance
- engagement opportunity
- resilience concern

## 7. Leading Indicator Rules

The MVP should only publish a leading indicator if it passes these conditions:

- statistically stable at 1-3 month lags
- directionally consistent over time
- explainable in business language
- not contradicted by obvious confounds in the same window

If an indicator fails these conditions, it should not appear in the product.

## 8. Event Layer In MVP

The event module in the MVP should be narrow.

Include only:

- COVID
- 2 to 4 major football/business events with clear month anchors

The event layer should support:

- pre/post month windows
- cross-asset comparison
- peer comparison where a shared event or shared shock exists

The MVP should not attempt a large archetype engine or complex event clustering.

## 9. AI Scope In MVP

AI is supportive, not core.

Allowed uses:

- wording for the monthly briefing
- wording for priority explanations
- summary generation for latest month

Not allowed as MVP-critical logic:

- ranking priorities
- determining signal relationships
- open-ended unrestricted chat
- free-form recommendations without evidence

If AI is unstable, the MVP must still work without it.

## 10. MVP Screens

The MVP requires these screens only:

1. Priority Board
2. Priority Detail
3. Command Center
4. Peer Benchmark
5. Commercial Signal Engine
6. Monthly Briefing

Any additional screen is stretch.

## 11. MVP Databricks Outputs

The MVP requires these Gold outputs:

- `gold_kpi_health`
- `gold_peer_benchmark`
- `gold_signal_relationships`
- `gold_priority_board`
- `gold_monthly_brief_inputs`

Optional but not required for MVP:

- `gold_event_windows`

## 12. MVP Non-Goals

The MVP will not include:

- broad open-ended AI assistant
- scenario simulator as hero experience
- full event archetype clustering
- benchmarking on unsupported metrics
- custom visual experimentation before logic is proven
- deployment to public cloud as a requirement

## 13. MVP Success Criteria

The MVP is complete only if:

- a new monthly file can be ingested and processed
- all five required Gold outputs refresh automatically
- the Priority Board shows real ranked cards from the latest month
- the benchmark module shows live comparison from the peer dataset
- the signal module shows only validated indicators
- the monthly briefing updates from refreshed data
- the app feels operational, not like a static data story

## 14. MVP Stretch Items

Only after the strict MVP is done:

- event intelligence screen
- additional KPI depth
- richer benchmark storytelling
- AI Q&A assistant
- Tableau support layer
- more polished leadership reporting exports

## 15. Build Sequence

Recommended order:

1. metric inventory and data contract
2. data cleaning and standardization
3. gold benchmark table
4. leading indicator analysis
5. priority scoring logic
6. monthly briefing inputs
7. React MVP shell
8. Priority Board UI
9. benchmark and signal screens
10. optional event and AI layers

This order must be respected. The Priority Board should not be designed before the scoring logic exists.
