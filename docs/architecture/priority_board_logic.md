# Priority Board Scoring Logic

This document defines the deterministic scoring rules used to calculate priority rankings in `gold_priority_board`. 

## Goal
To transform unranked analytical metrics into a sorted top 5 priority queue for the ClubOS MVP without relying on opaque models or AI generation. 

## Inputs

The final score (`priority_score`) is a weighted composite of 5 variables bounded between `0.0` and `1.0`:
`Priority Score = 0.30(Severity) + 0.20(Persistence) + 0.20(Peer Gap) + 0.20(Commercial) + 0.10(Supporting)`

### 1. Severity Score (Weight: 30%)
Deviation bounded to a max severity threshold of 20%.
- Formula: `MIN(1.0, ABS(deviation_from_seasonal) / 0.20)`

### 2. Persistence Score (Weight: 20%)
Measures consecutive months the metric has failed to remain "stable". Lookback is 3 months.
- Formula: `Count of non-stable months / 3.0`

### 3. Peer Gap Score (Weight: 20%)
Based on peer ranking (`gold_peer_benchmark`) relative to 5 other clubs.
- Rank 5-6 = `1.0`
- Rank 4 = `0.8`
- Rank 3 = `0.4`
- Rank 1-2 = `0.0`

Ranking semantics are polarity-aware through `gold_peer_benchmark`:
- direct metrics (higher-is-better) rank descending by value
- inverse metrics (lower-is-better, e.g. `bounce_rate`) rank ascending by value

### 4. Commercial Weight (Weight: 20%)
Static definitions driven by the `gold_signal_relationships` validation process.
- Target Commercial Metrics (e.g., `net_sales`) = `1.0`
- Validated Leading Indicators (e.g., `bounce_rate` -> sales) = `0.8`
- Generic KPI = `0.4`

### 5. Supporting Evidence (Weight: 10%)
Checks if multiple KPIs under the same asset are simultaneously flagging deviations.
- If Asset flag count > 1 = `1.0`, else `0.0`.

## Final Output
The application simply filters for `WHERE priority_rank <= 5` for any given reporting month to construct the hero page. 
To guarantee transparency, `supporting_metrics_json` persists a deterministic evidence object for each row with:
- `score_components`:
  - `severity`, `persistence`, `peer_gap`, `commercial_weight`, `supporting_evidence`
- `severity_inputs`:
  - `metric_value`, `health_status`, `trend_direction`, `deviation_from_seasonal_baseline`
- `persistence_inputs`:
  - `active_months_in_last_3`, `lookback_months`
- `peer_context` (nullable):
  - `peer_rank`, `peer_club_count`, `peer_median`, `peer_leader_value`, `gap_to_peer_median`, `gap_to_leader`
- `linked_signal_references`:
  - validated signal relationships tied to the metric (if any)
- `supporting_metric_rows`:
  - additional non-stable metric rows from the same asset+month used as supporting evidence

None of the ranking or evidence payload generation relies on AI. Every value comes from stored monthly data and deterministic logic.
