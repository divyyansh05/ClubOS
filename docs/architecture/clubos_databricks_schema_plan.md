# ClubOS Databricks Table and Schema Plan

## Purpose

This document defines the Databricks-side data plan for ClubOS.

It covers:

- ingestion structure
- normalization rules
- recommended bronze, silver, and gold tables
- table purposes
- key columns
- relationships between tables

The objective is to create a reusable data foundation so that future monthly uploads can flow through the same product without redesigning the app.

## 1. Data Design Principles

The Databricks design must satisfy four principles:

1. **Reusability**
   - future monthly files should flow through the same model
2. **Traceability**
   - every output can be traced back to a source upload
3. **Stability**
   - frontend tables should keep a stable shape across refreshes
4. **Transparency**
   - every score and output should be explainable from stored intermediate logic

## 2. Source Inputs

### 2.1 Internal Workbook

Source file:

- `Tema5.internal_metrics.dataset.xlsx`

Sheets:

- Main_Website
- eCommerce
- Streaming_Website
- Fan_App
- Info

### 2.2 Benchmark Workbook

Source file:

- `Tema5.benchmark.dataset.xlsx`

Sheets:

- Main_Website
- eCommerce
- Streaming
- Fan_App
- Info

### 2.3 Optional Event Annotation File

Recommended additional source:

- manually maintained CSV or Delta table of event annotations

Suggested event columns:

- event_id
- event_name
- event_type
- event_month
- club_scope
- notes

This should not be embedded manually in code.

## 3. Medallion Architecture Overview

### Bronze Layer

Purpose:

- preserve raw uploads
- capture file metadata
- keep source lineage

### Silver Layer

Purpose:

- standardize schemas
- resolve naming inconsistencies
- normalize asset naming
- validate metric ranges
- prepare clean tables for analytics

### Gold Layer

Purpose:

- provide app-ready, analysis-ready outputs
- hold benchmark summaries
- hold priority scoring inputs and outputs
- serve stable frontend contracts

## 4. Bronze Tables

### 4.1 `bronze_internal_main_website`

Source:

- internal workbook / Main_Website sheet

Key columns:

- month
- digital_active
- active_type
- unique_visitors
- visits
- page_views
- international_visits
- mobile_visits
- search_organic_visits
- social_organic_visits
- marketing_visits
- other_channels_visits
- consumption
- bounce_rate
- recurrence
- new_users
- logged_users
- source_file_name
- ingestion_timestamp

### 4.2 `bronze_internal_ecommerce`

Key columns:

- month
- digital_active
- active_type
- unique_visitors
- visits
- purchases
- items
- net_sales
- search_organic_purchases
- social_organic_purchases
- marketing_purchases
- other_channels_purchases
- cart_value
- product_views_rate
- card_addition_rate
- checkout_rate
- conversion_rate
- recurrence
- source_file_name
- ingestion_timestamp

### 4.3 `bronze_internal_streaming`

Key columns:

- month
- digital_active
- active_type
- unique_visitors
- daily_users
- video_plays
- streamers
- subscriptions
- search_organic_plays
- social_organic_plays
- marketing_plays
- otherl_traffic_plays
- subscription_rate
- streamers_rate
- video_recurrence
- video_play_rate
- video_progress_25_rate
- video_progress_50_rate
- video_progress_75_rate
- video_complete_rate
- source_file_name
- ingestion_timestamp

Normalize column names at Silver, not Bronze.

### 4.4 `bronze_internal_fan_app`

Key columns:

- month
- digital_active
- active_type
- unique_visitors
- visits
- app_downloads
- matchday_visits
- pct_android
- organic_launch_visits
- app_push_visits
- deeplink_visits
- marketing_visits
- other_channel_visits
- recurrence
- session_time_avg
- new_users
- logged_users
- heavy_users
- user_rating
- source_file_name
- ingestion_timestamp

### 4.5 `bronze_benchmark_main_website`

Key columns:

- month
- digital_active
- club
- active_type
- unique_visitors
- visits
- bounce_rate
- recurrence
- source_file_name
- ingestion_timestamp

### 4.6 `bronze_benchmark_ecommerce`

Key columns:

- month
- digital_active
- club
- active_type
- unique_visitors
- visits
- conversion_rate
- cart_value
- source_file_name
- ingestion_timestamp

### 4.7 `bronze_benchmark_streaming`

Key columns:

- month
- digital_active
- club
- active_type
- unique_visitors
- daily_users
- streamers_rate
- video_play_rate
- source_file_name
- ingestion_timestamp

Note:

- the current benchmark file appears to have a digital_active inconsistency for streaming. This should be corrected in Silver.

### 4.8 `bronze_benchmark_fan_app`

Key columns:

- month
- digital_active
- club
- active_type
- unique_visitors
- visits
- matchday_visits
- app_downloads
- recurrence
- heavy_users
- user_rating
- source_file_name
- ingestion_timestamp

### 4.9 `bronze_event_annotations`

Optional but recommended.

Key columns:

- event_id
- event_name
- event_type
- event_month
- event_scope
- description
- created_at

## 5. Silver Layer Design

Silver tables should standardize, clean, and align the data.

### 5.1 Shared Silver Rules

All Silver tables should:

- standardize `month` to a proper month-start date
- standardize asset names
- standardize column naming to snake_case
- remove unnamed empty columns
- validate metric ranges
- attach upload metadata
- ensure one row per entity and month

### 5.2 `silver_internal_asset_metrics`

Purpose:

- unify all internal asset metrics into one normalized fact table

Recommended columns:

- month
- asset_name
- asset_type
- metric_name
- metric_value
- metric_category
- source_type = internal
- source_file_name
- ingestion_timestamp

This long-format table is useful for flexible calculations, anomaly detection, and app queries.

### 5.3 `silver_internal_asset_monthly`

Purpose:

- preserve one wide row per internal asset per month for simpler downstream joins

Recommended columns:

- month
- asset_name
- asset_type
- all cleaned internal metrics
- season_label
- calendar_year
- month_index

### 5.4 `silver_benchmark_asset_metrics`

Purpose:

- unify peer benchmark metrics into one normalized fact table

Recommended columns:

- month
- club
- asset_name
- asset_type
- metric_name
- metric_value
- source_type = benchmark
- source_file_name
- ingestion_timestamp

### 5.5 `silver_benchmark_asset_monthly`

Purpose:

- preserve one wide row per club, asset, and month for benchmarked KPIs

Recommended columns:

- month
- club
- asset_name
- asset_type
- benchmark-supported metrics only
- season_label
- calendar_year
- month_index

### 5.6 `silver_event_annotations`

Purpose:

- store curated event metadata aligned to month granularity

Recommended columns:

- event_id
- event_name
- event_type
- event_month
- event_scope
- description

### 5.7 `silver_calendar`

Purpose:

- central date dimension for monthly analytics

Recommended columns:

- month
- calendar_year
- calendar_month
- season_label
- season_year_start
- season_year_end
- month_name
- quarter

## 6. Gold Layer Design

The Gold layer should provide stable, product-ready outputs.

## 6.1 `gold_kpi_health`

Purpose:

- power Command Center
- support month-over-month and seasonal status

Grain:

- one row per month, asset, metric

Recommended columns:

- month
- asset_name
- metric_name
- metric_value
- prior_month_value
- prior_season_same_month_value
- rolling_12m_avg
- seasonal_baseline
- deviation_from_seasonal_baseline
- trend_direction
- health_status

## 6.2 `gold_peer_benchmark`

Purpose:

- power Peer Benchmark screen

Grain:

- one row per month, asset, metric

Recommended columns:

- month
- asset_name
- metric_name
- rm_value
- peer_median
- peer_mean
- peer_leader_value
- rm_rank
- club_count
- gap_to_peer_median
- gap_to_leader
- rank_change_12m
- gap_change_12m

## 6.3 `gold_signal_relationships`

Purpose:

- store validated leading indicators

Grain:

- one row per validated source-target-lag relationship

Recommended columns:

- source_asset
- source_metric
- target_asset
- target_metric
- lag_months
- relationship_direction
- strength_score
- validation_status
- business_interpretation
- last_validated_month

Only stable relationships should be written here.

## 6.4 `gold_priority_inputs`

Purpose:

- hold the decomposed scoring inputs before final ranking

Grain:

- one row per month, asset, metric, priority_candidate

Recommended columns:

- month
- priority_candidate_id
- asset_name
- metric_name
- severity_score
- persistence_score
- peer_gap_score
- commercial_weight_score
- supporting_evidence_score
- category

This table is useful for debugging and trust.

## 6.5 `gold_priority_board`

Purpose:

- power the Priority Board screen

Grain:

- one row per month, priority item

Recommended columns:

- month
- priority_id
- priority_title
- priority_category
- priority_score
- priority_rank
- asset_name
- primary_metric
- summary_text
- why_it_matters
- peer_context_available
- suggested_next_investigation
- supporting_metrics_json

This is the most important Gold table in the product.

## 6.6 `gold_monthly_brief_inputs`

Purpose:

- feed the monthly briefing and any templated or AI-generated summaries

Grain:

- one row per month

Recommended columns:

- month
- top_priority_ids_json
- top_anomalies_json
- strongest_signal_ids_json
- benchmark_summary_json
- health_summary_json

## 6.7 `gold_event_windows`

Purpose:

- support the Event Intelligence screen

Grain:

- one row per event, asset, relative_month_offset, metric

Recommended columns:

- event_id
- event_name
- event_type
- event_month
- asset_name
- metric_name
- relative_month_offset
- metric_value
- baseline_value
- deviation_from_baseline
- club_scope

This table is useful but can be phase-two if needed.

## 7. Relationship Model

### 7.1 Core Relationships

- `silver_calendar.month` joins all monthly tables
- `silver_event_annotations.event_month` joins to monthly tables by month
- `gold_priority_board` references `gold_priority_inputs`
- `gold_monthly_brief_inputs` references outputs from:
  - `gold_priority_board`
  - `gold_signal_relationships`
  - `gold_peer_benchmark`
  - `gold_kpi_health`

### 7.2 Frontend Contract

The frontend should read only Gold tables.

Do not bind UI components directly to Bronze or Silver.

This keeps the app stable even if the ingestion logic changes.

## 8. Data Validation Plan

Validation should happen in Silver.

### 8.1 Required Validation Checks

- missing required columns
- duplicate month/entity rows
- invalid month formats
- null spikes in required KPI fields
- values outside expected range for percentages or rates
- benchmark club coverage count by month

### 8.2 Validation Outputs

Recommended table:

- `silver_data_quality_checks`

Columns:

- run_id
- table_name
- check_name
- status
- issue_count
- issue_details
- run_timestamp

This improves reliability for recurring monthly runs.

## 9. Refresh Strategy

Each monthly run should:

1. ingest new raw files into Bronze
2. run validation and standardization into Silver
3. rebuild Gold outputs
4. timestamp the run
5. expose only the latest successful Gold snapshot to the app

Recommended run metadata table:

- `gold_refresh_log`

Columns:

- refresh_id
- refresh_month
- run_timestamp
- status
- source_file_names
- notes

## 10. Schema Evolution Strategy

Because future files may evolve slightly, the model should support limited schema change.

Recommended approach:

- maintain a schema mapping layer in Silver
- map renamed source columns to canonical names
- flag new unknown columns for review
- avoid hardcoding column positions

This is important if the product is expected to keep working across future deliveries.

## 11. MVP Table Set

The strict MVP requires these tables:

Bronze:

- bronze_internal_main_website
- bronze_internal_ecommerce
- bronze_internal_streaming
- bronze_internal_fan_app
- bronze_benchmark_main_website
- bronze_benchmark_ecommerce
- bronze_benchmark_streaming
- bronze_benchmark_fan_app

Silver:

- silver_internal_asset_monthly
- silver_benchmark_asset_monthly
- silver_calendar

Gold:

- gold_kpi_health
- gold_peer_benchmark
- gold_signal_relationships
- gold_priority_inputs
- gold_priority_board
- gold_monthly_brief_inputs

Optional for MVP:

- gold_event_windows
- silver_event_annotations
- silver_data_quality_checks
- gold_refresh_log

## 12. Build Priority

Recommended order:

1. Bronze ingestion tables
2. Silver normalization tables
3. Gold benchmark table
4. Gold KPI health table
5. Gold signal relationships table
6. Gold priority inputs
7. Gold priority board
8. Gold monthly brief inputs
9. Gold event windows

This order aligns with the product build sequence and keeps the hero workflow intact.
