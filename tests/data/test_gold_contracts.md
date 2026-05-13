# Gold Contacts Validation Guide

This document defines the conceptual validation checks that will be implemented downstream to test the reliability and accuracy of the foundation Gold tables before they are exposed to the API.

## 1. Validating `gold_kpi_health`

### Expected Sanity Checks
- **Uniqueness Check**: `month` + `asset_name` + `metric_name` must be perfectly unique.
- **Date Continuity**: The `prior_month_value` and `prior_season_same_month_value` fields must correctly trace backward chronologically. If data exists for T-1 or T-12, the lookback columns cannot be null.
- **Trend Synchronization**: `trend_direction` must accurately reflect the mathematical relationship between `metric_value` and `prior_month_value`. If `metric_value > prior_month_value`, the trend must be `up`.
- **Baseline Floor Boundaries**: The `seasonal_baseline` should never be mathematically negative given the metrics tracked. If `rolling_12m_avg` comes back negative for any volume metric, the job must fail.
- **Health Classification Fallback**: Every row must have a `health_status` assigned (`good`, `review`, or `stable`).
- **Polarity Behavior**: Assert that metrics known to be inverse polarity (like `bounce_rate`) correctly receive a `good` health status when their value shrinks significantly relative to standard (`deviation_from_seasonal_baseline < -0.05`), as opposed to the default logic.

## 1.b Validating `silver` Enforcements
*These checks prevent upstream garbage from corrupting Gold pipelines.*
- **Allowed Metric Enforcement**: The unpivoted `metric_name` space must map 1:1 against the approved `ALLOWED_METRICS` dictionary lists deployed in normalization pipelines.
- **Invalid Extra Column Behavior**: In test environments, inject a random column (e.g. `accidental_test_col_123`) into the simulated `bronze` dataframe. Verify that the unpivot expression silently excludes this dimension and the final fact table maintains strict constraint to only the modeled metrics.

## 2. Validating `gold_peer_benchmark`

### Benchmark Coverage Constraints
- **Coverage Minimum**: `club_count` must evaluate to 5. Anything less than 5 implies the peer median calculations are fundamentally biased due to missing data for that month.
- **Client Source Integrity**: `rm_value` must come from `silver_internal_asset_metrics` and never from a benchmark club row.
- **Benchmark Support Integrity**: Every `month + asset_name + metric_name` in `gold_peer_benchmark` must exist in `silver_benchmark_asset_metrics`. Unsupported metrics must be absent.

### Expected Sanity Checks
- **Ranking Bounds**: `rm_rank` must always exist within `1` to `club_count + 1`. 
- **Math Equivalency**: 
  - `gap_to_peer_median` must equal `polarity * (rm_value - peer_median)`.
  - `gap_to_leader` must equal `polarity * (rm_value - peer_leader_value)`.
- **Leader Semantics by Polarity**:
  - if polarity = `1`, `peer_leader_value` must be the peer max for that month/asset/metric.
  - if polarity = `-1`, `peer_leader_value` must be the peer min for that month/asset/metric.
- **Metric Inclusion**: Check that only valid MVP benchmark metrics are populating the table. Things like `net_sales` or `page_views` must automatically fail ingestion if they inadvertently slip through the Bronze benchmark workbook.
- **Null Handlers**: 12-month change metrics (`rank_change_12m`, `gap_change_12m`) must safely accept `nulls` during the first 11 months of reporting.

## 3. Validating `gold_monthly_brief_inputs`

### Structural Checks
- **One Row Per Month**: `month` must be unique.
- **JSON Fields Present**: `top_priority_ids_json`, `top_anomalies_json`, `strongest_signal_ids_json`, `benchmark_summary_json`, `health_summary_json` must be non-null.

### Behavioral Checks
- **Top Priority Bound**: `top_priority_ids_json` must contain at most 3 items.
- **Top Anomaly Bound**: `top_anomalies_json` must contain at most 3 items.
- **Signal Guardrail**: `strongest_signal_ids_json` must only include signal rows derived from `validation_status = 'active'`.

## 4. Validating Quality Fail-Stop

- **Required Checks Gate**: If any required check fails in `01_run_data_quality_checks.py`, the notebook run must raise an error and stop downstream execution.
- **Log Persistence Before Failure**: The quality run must still append all check outcomes into `clubos_silver.silver_data_quality_checks` before raising.
