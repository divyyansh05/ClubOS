# Gold Table Contracts

This document formalizes the operational schema contracts for the first stable Gold tier tables. The frontend will consume these directly.

## 1. `gold_kpi_health`

**Purpose**: Powers the Command Center. Serves the foundational month-over-month and season-over-season logic. 
**Upstream Dependency**: `silver_internal_asset_metrics`
**Primary App Screen**: Command Center (API endpoint reads from here)

### Structural Grain
- One row per **`month`**, **`asset_name`**, **`metric_name`**.

### Key Columns
| Column Name | Type | Description |
|---|---|---|
| `month` | Date | The start date of the reporting month. |
| `asset_name` | String | Standardized product grouping (e.g., `main_website`, `fan_app`). |
| `metric_name` | String | Standardized metric name (e.g., `bounce_rate`, `net_sales`). |
| `metric_value` | Float | The absolute observed value for the given month. |
| `prior_month_value` | Float | Lookback value for M-1. |
| `prior_season_same_month_value` | Float | Lookback value for exactly 12 months prior. |
| `rolling_12m_avg` | Float | Trailing 12-month average of the metric. |
| `seasonal_baseline` | Float | Expected normal baseline. Proxying the 12m rolling average for the MVP. |
| `deviation_from_seasonal_baseline` | Float | Percentile variance from the baseline. |
| `trend_direction` | String | Enum (`up`, `down`, `flat`) against prior month. |
| `health_status` | String | Enum (`good`, `review`, `stable`) based on metric-aware polarity. |

### Limitations
- `health_status` depends on a strict polarity configuration (1 = higher is better, -1 = lower is better) applied during Gold processing. If a new metric is introduced without definition, it defaults to 1 (higher is better).


## 2. `gold_peer_benchmark`

**Purpose**: Powers the Peer Benchmark screens. Compares Real Madrid internal metric values against competitor benchmark distributions. 
**Upstream Dependencies**: `silver_internal_asset_metrics`, `silver_benchmark_asset_metrics`
**Primary App Screen**: Peer Benchmark Engine

### Structural Grain
- One row per **`month`**, **`asset_name`**, **`metric_name`** where:
- the Real Madrid value comes from internal data
- the metric is benchmark-supported
- full peer coverage exists in the benchmark table

### Key Columns
| Column Name | Type | Description |
|---|---|---|
| `month` | Date | The start date of the reporting month. |
| `asset_name` | String | Standardized product grouping. |
| `metric_name` | String | Standardized metric name. |
| `rm_value` | Float | Real Madrid internal metric value for the month. |
| `peer_median` | Float | 50th percentile of benchmark peers only (RM excluded). |
| `peer_mean` | Float | Mean of benchmark peers only (RM excluded). |
| `peer_leader_value` | Float | Best benchmark peer value for the month based on metric polarity (max for direct metrics, min for inverse metrics like `bounce_rate`). |
| `rm_rank` | Integer | RM rank position when evaluated against peers + RM (1 is best). |
| `club_count` | Integer | Benchmark peer club count used for context (expected 5). |
| `gap_to_peer_median` | Float | Polarity-adjusted gap to peer median. Positive = better than peer median; negative = worse. |
| `gap_to_leader` | Float | Polarity-adjusted gap to peer leader. Positive = better than peer leader; negative = worse. |
| `rank_change_12m` | Integer | Net positive/negative movement in ordinal rank since T-12. |
| `gap_change_12m` | Float | Net movement in the total gap since T-12. |

### Limitations
- Supported metrics are aggressively restricted. `gold_peer_benchmark` does *not* exist for net_sales, page_views, items, etc. The App must gracefully hide benchmark comparisons for unsupported KPIs.
- The table never reuses a benchmark club row as the client row.

## 3. `gold_monthly_brief_inputs`

**Purpose**: Powers the Monthly Briefing module with deterministic monthly briefing payloads.
**Upstream Dependencies**: `gold_priority_board`, `gold_kpi_health`, `gold_peer_benchmark`, `gold_signal_relationships`
**Primary App Screen**: Monthly Briefing

### Structural Grain
- One row per **`month`**.

### Key Columns
| Column Name | Type | Description |
|---|---|---|
| `month` | Date | The start date of the reporting month. |
| `top_priority_ids_json` | String (JSON array) | Top 3 ranked priorities with id/title/category/score. |
| `top_anomalies_json` | String (JSON array) | Top 3 review anomalies by absolute seasonal deviation. |
| `strongest_signal_ids_json` | String (JSON array) | Top active validated signals for the validated month; empty array on other months. |
| `benchmark_summary_json` | String (JSON object) | Monthly peer-benchmark summary counters and gap metrics. |
| `health_summary_json` | String (JSON object) | Monthly health-status summary across KPI rows. |

### Limitations
- Signal relationships are not generated at month-grain; therefore signal payloads populate only the `last_validated_month` and remain empty for other months.

## 4. Quality Gate Behavior

The quality notebook (`databricks/notebooks/quality/01_run_data_quality_checks.py`) must:
- run required checks for nulls, duplicate keys, month coverage, benchmark club coverage, and rate bounds
- append all check results into `clubos_silver.silver_data_quality_checks`
- **fail-stop the run** by raising an error when any required check fails
