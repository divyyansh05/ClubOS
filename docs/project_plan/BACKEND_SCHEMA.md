---
# ClubOS — Backend Schema Document
**Version**: 1.0
**Status**: Reconstructed from MVP
**Date**: 2026-05-14
---

## 1. Data Architecture Overview

ClubOS implements a Databricks medallion architecture with three pipeline stages — Bronze (raw ingestion), Silver (normalisation and cleaning), Gold (business-ready analytics) — followed by a FastAPI application layer and a React frontend. Only Gold tables are app-facing: the backend API reads exclusively from Gold Delta Lake tables (in live Databricks mode) or their exported CSV equivalents (in snapshot mode). The frontend has no direct access to Bronze, Silver, or raw source files. The pipeline is write-only from the perspective of the application: ClubOS is strictly read-only against the PostgreSQL and Delta Lake data stores. Every API response is typed against a Pydantic v2 schema, validated at runtime before being returned to the frontend.

```
Monthly CSV files
      ↓
Bronze Delta tables  (raw ingestion, audit trail)
      ↓
Silver Delta tables  (normalised, cleaned, deduplicated)
      ↓
Gold Delta tables    (scored, ranked, benchmarked, aggregated)
      ↓
FastAPI backend      (reads Gold via SQL or CSV snapshot)
      ↓
React frontend       (typed fetch via lib/api.ts)
```

---

## 2. Gold Tables

### 2.1 gold_priority_board

**Purpose**: Stores the ranked priority output for every monthly pipeline run. Each row is one metric-asset issue or opportunity for one month, scored by the weighted priority formula. The frontend Priority Board reads the latest month's top-ranked rows from this table.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `month` | date (YYYY-MM-DD) | Reporting month this priority belongs to |
| `priority_id` | string | Composite key: `{month}_{asset_name}_{metric_name}` |
| `priority_title` | string | Human-readable headline for the priority card |
| `priority_category` | string | Enumerated label: `critical`, `opportunity`, `benchmark underperformance`, `warning` |
| `priority_score` | float | Weighted composite score 0.0–1.0 |
| `priority_rank` | int | Ordinal rank within the month (1 = highest score) |
| `asset_name` | string | Digital platform: `main_website`, `ecommerce`, `streaming`, `fan_app` |
| `primary_metric` | string | The metric driving this priority (references metric_dictionary) |
| `summary_text` | string | One-sentence summary of the metric's status this month |
| `why_it_matters` | string | Plain-English explanation of commercial significance |
| `suggested_next_investigation` | string | Recommended next step for the team |
| `supporting_metrics_json` | JSON string | Embedded JSON blob containing: `score_components` (five weighted values), `severity_inputs` (metric value, health status, trend direction, deviation), `persistence_inputs` (active months in last 3), `peer_context` (rank, club count, peer median, leader value, gaps), `linked_signal_references` (signal IDs), `supporting_metric_rows` (up to 12 corroborating metrics with their own health status and severity scores) |

**Primary key**: `(month, priority_id)` — one row per metric-asset per month.

**Updated**: After each monthly pipeline run (Gold notebook `04_build_priority_board.py`). New rows appended for the latest month; historical rows are not modified.

---

### 2.2 gold_kpi_health

**Purpose**: Stores computed health status for every tracked metric across all digital assets for every month in the historical dataset. This is the source of truth for trend direction, deviation from seasonal baseline, and volatility signals. The Command Center reads the latest month's aggregate from this table.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `month` | date (YYYY-MM-DD) | Reporting month |
| `asset_name` | string | Digital platform: `main_website`, `ecommerce`, `streaming`, `fan_app` |
| `metric_name` | string | Canonical metric name (references metric_dictionary) |
| `metric_value` | float | Actual metric value for this month |
| `prior_month_value` | float (nullable) | Value from the immediately preceding month |
| `prior_season_same_month_value` | float (nullable) | Value from the same calendar month in the prior year |
| `rolling_12m_avg` | float | Rolling 12-month average of metric_value |
| `seasonal_baseline` | float | Expected value for this month based on historical seasonal patterns |
| `deviation_from_seasonal_baseline` | float | `(metric_value - seasonal_baseline) / seasonal_baseline` — signed percentage deviation |
| `trend_direction` | string | Enumerated: `up`, `down`, `flat` — based on 6-month slope |
| `health_status` | string | Enumerated: `good`, `review`, `stable` — assigned by rule-based logic |

**Health status assignment logic**:
- `good`: positive trend slope AND volatility within norm AND not flagged as outlier
- `review`: negative slope OR persistence ≥ 3 months declining OR abs(deviation) > 20%
- `stable`: neither of the above — flat trend, no significant change

**Primary key**: `(month, asset_name, metric_name)` — one row per metric per asset per month.

**Updated**: After each monthly pipeline run (Gold notebook `01_build_kpi_health.py`).

---

### 2.3 gold_peer_benchmark

**Purpose**: Stores Real Madrid's position relative to five peer clubs for each of the 8 benchmarked metrics, across all historical months. Polarity-aware gap calculations are pre-computed here. The Peer Benchmark screen reads time series from this table.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `month` | date (YYYY-MM-DD) | Reporting month |
| `asset_name` | string | Digital platform the metric belongs to |
| `metric_name` | string | One of the 8 benchmarked metrics |
| `rm_value` | float | Real Madrid's actual metric value this month |
| `peer_median` | float | Median value across the 5 peer clubs (Real Madrid excluded from median) |
| `peer_mean` | float | Mean value across the 5 peer clubs |
| `peer_leader_value` | float | Best-in-class value among all 6 clubs (polarity-aware: leader for bounce_rate is the lowest value) |
| `rm_rank` | int | Real Madrid's rank among 6 clubs (1 = best, 6 = worst), adjusted for polarity |
| `club_count` | int | Number of clubs in comparison (always 5 peers + Real Madrid = 6 in current data, but the column reflects actual club count for the metric-month) |
| `gap_to_peer_median` | float | `(rm_value - peer_median) × polarity` — positive = ahead of peers, negative = behind |
| `gap_to_leader` | float | `(rm_value - peer_leader_value) × polarity` — positive = Real Madrid is leader, negative = behind leader |
| `rank_change_12m` | int (nullable) | Change in rank vs same metric 12 months ago (positive = improved) |
| `gap_change_12m` | float (nullable) | Change in gap_to_peer_median vs 12 months ago |

**Benchmarked metrics** (the only 8 metrics that appear in this table):

| Asset | Metric |
|-------|--------|
| main_website | unique_visitors |
| main_website | visits |
| main_website | bounce_rate |
| main_website | recurrence |
| ecommerce | unique_visitors |
| ecommerce | visits |
| ecommerce | conversion_rate |
| ecommerce | net_sales |

**Primary key**: `(month, asset_name, metric_name)`.

**Updated**: After each monthly pipeline run (Gold notebook `02_build_peer_benchmark.py`).

---

### 2.4 gold_signal_relationships

**Purpose**: Stores validated leading indicator relationships — pairs of metrics where one (source) reliably predicts the other (target) at a 1–3 month lag. Only signals passing all three validation gates (statistical, temporal consistency, business prior) are stored with `validation_status = active`. The Signal Engine reads all rows from this table.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `source_asset` | string | Digital platform of the source (predictor) metric |
| `source_metric` | string | Source metric name |
| `target_asset` | string | Digital platform of the target (predicted) metric |
| `target_metric` | string | Target metric name |
| `lag_months` | int | Number of months between source signal and target response (1, 2, or 3) |
| `relationship_direction` | string | `positive` (metrics move together) or `negative` (inverse relationship) |
| `strength_score` | float | Absolute Pearson correlation coefficient, 0.6–1.0 (only signals ≥ 0.6 retained) |
| `validation_status` | string | `active` (currently valid) or `inactive` (failed recent re-validation) |
| `business_interpretation` | string | Plain-English explanation of what this signal means commercially |
| `last_validated_month` | date (YYYY-MM-DD) | Most recent month for which this signal was tested and passed |

**Signal ID** (used in API responses but not stored as a column): composed as `{source_asset}__{source_metric}__{target_asset}__{target_metric}__{lag_months}`.

**Primary key**: `(source_asset, source_metric, target_asset, target_metric, lag_months)`.

**Updated**: After each monthly pipeline run (analytics notebook `01_validate_signals.py`). Existing signal rows may have `validation_status` updated to `inactive` if re-validation fails.

---

### 2.5 gold_monthly_brief_inputs

**Purpose**: Pre-aggregated inputs for the Monthly Briefing executive summary. Each row represents one month's complete briefing data, stored as a set of JSON blobs. The Monthly Briefing API reads the latest month's row and deserialises the JSON fields into typed structures.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `month` | date (YYYY-MM-DD) | Reporting month |
| `top_priority_ids_json` | JSON string | Ordered list of priority_id strings for the top-ranked priorities this month |
| `top_anomalies_json` | JSON string | List of anomaly objects: `{asset_name, metric_name, metric_value, deviation_from_seasonal_baseline}`, ordered by absolute deviation descending |
| `strongest_signal_ids_json` | JSON string | Ordered list of signal identifier strings (strongest signals by strength_score) |
| `benchmark_summary_json` | JSON string | Object: `{benchmarked_metric_count, benchmark_underperformance_count, avg_gap_to_peer_median, worst_gap_to_peer_median}` |
| `health_summary_json` | JSON string | Object: `{metric_count, good_count, review_count, stable_count, avg_abs_deviation}` |

**Primary key**: `month` — one row per monthly pipeline run.

**Updated**: After each monthly pipeline run (Gold notebook `05_build_monthly_brief_inputs.py`). New row appended; prior months not modified.

---

### 2.6 gold_events

**Purpose**: Stores real-world events (signings, matches, trophies, commercial activities) that provide business context for metric movements. Events are displayed as annotations on metric charts and managed through the Event Calendar UI.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | string | Unique identifier for the event (format: evt_XXX) |
| `event_date` | date (YYYY-MM-DD) | Date when the event occurred |
| `event_name` | string | Short descriptive name of the event |
| `event_category` | string | Enumerated: `player_signing`, `player_departure`, `match_result_win`, `match_result_loss`, `trophy_win`, `trophy_loss`, `transfer_window`, `media_event`, `injury_news`, `commercial_event` |
| `event_description` | string | Detailed description of the event and its expected impact |
| `expected_impact` | string | Comma-separated list of affected digital assets: `main_website`, `ecommerce`, `streaming`, `fan_app`, or `all` |
| `impact_magnitude` | string | Enumerated: `high`, `medium`, `low` — estimated significance of impact |

**Primary key**: `event_id` — one row per event.

**Updated**: Manual via Event Calendar UI (POST /events, DELETE /events/{event_id}).

**Usage**: The `/events/near/{asset}/{metric}/{month}` endpoint returns events within 30 days of a given month for annotation on metric charts. The Priority Board modal displays event markers on 12-month trend charts.

---

### 2.7 gold_social_metrics (V1.6.1)

**Purpose**: Stores monthly aggregated social media performance metrics for Real Madrid across five platforms (Instagram, TikTok, X, Facebook, YouTube). One row per month with platform breakdowns, content type performance, and language audience distribution.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `month` | date (YYYY-MM-DD) | Reporting month |
| `asset_name` | string | Always "social_media" |
| `total_posts` | int | Total posts across all platforms |
| `total_engagement` | float | Total engagement (likes + comments + reposts + saves) |
| `avg_engagement_per_post` | float | Average engagement per post |
| `total_likes` | float | Total likes/reactions |
| `total_comments` | float | Total comments/replies |
| `total_reposts` | float | Total reposts/retweets |
| `total_saves` | float | Total post saves |
| `total_estimated_views` | float | Total estimated views |
| `total_estimated_impressions` | float | Total estimated impressions |
| `instagram_posts` | int | Instagram post count |
| `instagram_engagement` | float | Instagram total engagement |
| `instagram_avg_engagement` | float | Instagram avg engagement per post |
| `instagram_engagement_rate` | float | Instagram engagement / max followers |
| `tiktok_posts` | int | TikTok post count |
| `tiktok_engagement` | float | TikTok total engagement |
| `tiktok_avg_engagement` | float | TikTok avg engagement per post |
| `tiktok_engagement_rate` | float | TikTok engagement / max followers |
| `x_posts` | int | X (Twitter) post count |
| `x_engagement` | float | X total engagement |
| `x_avg_engagement` | float | X avg engagement per post |
| `x_engagement_rate` | float | X engagement / max followers |
| `facebook_posts` | int | Facebook post count |
| `facebook_engagement` | float | Facebook total engagement |
| `facebook_avg_engagement` | float | Facebook avg engagement per post |
| `facebook_engagement_rate` | float | Facebook engagement / max followers |
| `youtube_posts` | int | YouTube post count |
| `youtube_engagement` | float | YouTube total engagement |
| `youtube_avg_engagement` | float | YouTube avg engagement per post |
| `goal_celebration_avg_engagement` | float | Avg engagement for goal celebration content |
| `training_avg_engagement` | float | Avg engagement for training content |
| `score_graphic_avg_engagement` | float | Avg engagement for score graphics |
| `player_arrival_avg_engagement` | float | Avg engagement for player arrival content |
| `lineup_graphic_avg_engagement` | float | Avg engagement for lineup graphics |
| `birthday_avg_engagement` | float | Avg engagement for birthday content |
| `game_preview_avg_engagement` | float | Avg engagement for game preview content |
| `spanish_account_engagement` | float | Engagement from Spanish language accounts |
| `english_account_engagement` | float | Engagement from English language accounts |
| `arabic_account_engagement` | float | Engagement from Arabic language accounts |
| `french_account_engagement` | float | Engagement from French language accounts |
| `other_account_engagement` | float | Engagement from other language accounts |
| `international_engagement_ratio` | float | (Total - Spanish) / Total engagement |
| `top_performing_platform` | string | Platform with highest avg engagement per post |
| `top_performing_content_type` | string | Content type with highest avg engagement |

**Primary key**: `month` — one row per month.

**Updated**: Generated by `scripts/process_social_data.py` from source CSV. In production, would be populated by monthly data pipeline.

**Data source**: Real Madrid social media dataset with 55,598 posts across 2025. Includes Instagram (180M followers), TikTok (54.7M), X (48.8M), Facebook (127M), YouTube (18.9M).

---

### 2.8 silver_data_quality_checks (reference table)

**Purpose**: Not consumed by the main UI screens but exposed via `GET /refresh/status`. Stores pass/fail results from the pipeline quality validation notebook, allowing the API to report pipeline health.

**Location**: `data/gold_snapshots/silver_data_quality_checks.csv` (snapshot export of the Silver-layer quality table).

---

## 3. Metric Dictionary

**Source**: `databricks/seeds/metric_dictionary.json`

**Structure**:

| Field | Type | Purpose |
|-------|------|---------|
| `metric_name` | string | Canonical snake_case name used identically across all Gold tables, API responses, and frontend display |
| `polarity` | int | `+1` = higher is better (visits, sales, engagement); `-1` = lower is better (bounce_rate only); `0` = neutral/descriptive (pct_android) |

**Note**: The metric_dictionary.json in the current MVP stores only `polarity`. Commercial weight and asset grouping are derived from pipeline logic and config, not stored in this seed file. The file is read by the Gold peer benchmark notebook to invert gap calculations for negative-polarity metrics.

**Asset groups and metric counts**:

| Asset | Metric Count | Key Metrics |
|-------|-------------|-------------|
| main_website | 14 | unique_visitors, visits, page_views, international_visits, mobile_visits, search_organic_visits, social_organic_visits, marketing_visits, other_channels_visits, consumption, bounce_rate (-1), recurrence, new_users, logged_users |
| ecommerce | 12 | purchases, items, net_sales, search_organic_purchases, social_organic_purchases, marketing_purchases, other_channels_purchases, cart_value, product_views_rate, card_addition_rate, checkout_rate, conversion_rate |
| streaming | 16 | daily_users, video_plays, streamers, subscriptions, search_organic_plays, social_organic_plays, marketing_plays, other_traffic_plays, subscription_rate, streamers_rate, video_recurrence, video_play_rate, video_progress_25_rate, video_progress_50_rate, video_progress_75_rate, video_complete_rate |
| fan_app | 10 | app_downloads, matchday_visits, pct_android (0), organic_launch_visits, app_push_visits, deeplink_visits, other_channel_visits, session_time_avg, heavy_users, user_rating |
| social_media | 7 | total_engagement, avg_engagement_per_post, engagement_rate, instagram_engagement, total_posts (0), international_engagement_ratio, total_estimated_views |
| **Total** | **59** | |

**Polarity breakdown**: 56 metrics polarity `+1` (higher is better), 1 metric polarity `-1` (bounce_rate), 2 metrics polarity `0` (pct_android, total_posts — neutral, directional meaning depends on context).

**Benchmarked subset**: 8 of the 52 metrics have peer comparison data in the benchmark dataset. Only these 8 appear in `gold_peer_benchmark` and receive a non-zero peer_gap score component in priority scoring.

### 2.8 gold_social_posts (V1.7.0)

**Purpose**: Post-level social media data for Real Madrid CF. Unlike gold_social_metrics (monthly aggregated), this table preserves individual posts for granular analytics.

**Row count**: 55,598 posts (Real Madrid only, filtered from 1.1M source posts)

**Columns** (22 total):
- `post_id` — Unique post identifier
- `entity` — Always "Real Madrid CF" (filtered)
- `username` — Account username
- `platform` — Platform name (Instagram, TikTok, X, Facebook, YouTube, Douyin)
- `media_type` — Content type (image, video)
- `variety` — Format variety (post, reel, story, etc.)
- `post_text` — Post caption (truncated to 500 chars)
- `post_date` — DD/MM/YYYY format
- `day_of_week` — Monday through Sunday
- `day_number` — 1-7 (1=Monday)
- `month` — YYYY-MM format
- `scene` — Content scene (Goal Celebration, Training, Birthday, etc.)
- `match_moment` — Classified moment: pre_match | during_match | post_match | non_matchday | other
- `engagement` — Total engagement (likes + comments + reposts + saves)
- `likes`, `comments`, `reposts`, `saves` — Individual metrics
- `estimated_views`, `estimated_impressions` — Platform estimates
- `follower_count` — Account followers at post time
- `hashtags` — Comma-separated lowercase hashtags extracted from post_text

**Key insight**: 7.8x engagement multiplier for ig_reel vs standard post (522K vs 67K avg)

### 2.9 gold_social_dayofweek (V1.7.0)

**Purpose**: Day of week × platform × match moment aggregated performance for timing optimization.

**Row count**: 411 rows (7 days × ~60 unique combinations of platform/moment/media/variety)

**Columns** (17 total):
- `day_of_week`, `day_number` — Day identification
- `platform`, `match_moment`, `media_type`, `variety` — Grouping dimensions
- `post_count` — Posts in this group
- `total_engagement`, `avg_engagement_per_post`, `median_engagement_per_post` — Engagement stats
- `max_engagement_post_date` — Date of highest-performing post
- `total_likes`, `total_comments`, `total_reposts` — Sums
- `avg_likes`, `avg_comments`, `avg_reposts` — Averages

**Key insight**: Thursday on Instagram averages 426K engagement (17.8% above weekly average)

### 2.10 gold_social_hashtags (V1.7.0)

**Purpose**: Hashtag performance analysis by type (branded, event, player, farewell) for content strategy.

**Row count**: 2,143 rows (unique hashtag × platform × month combinations)

**Columns** (11 total):
- `hashtag` — Hashtag with # prefix (e.g., #graciasluka)
- `platform`, `month` — Grouping dimensions
- `post_count`, `total_engagement`, `avg_engagement_per_post` — Performance metrics
- `posts_with_this_hashtag` — Count (same as post_count)
- `is_branded` — True if hashtag in [#rmcity, #realmadrid, #madridistas, #halamadrideternamente]
- `is_event` — True if matches event keywords (ucl, laliga, elclasico, championsleague, nationsleague)
- `is_player` — True if player name (mbappe, vinicius, bellingham, modric, etc.)
- `is_farewell` — True if starts with "gracias" (#graciasluka, #graciascarlo)

**Key insight**: Farewell hashtags (#graciasluka: 896K avg) outperform branded hashtags by 12.4x

---

## 4. API Endpoints

### 4.1 Endpoint Inventory

All routes are prefixed at `http://localhost:8000`. No `/api/` or `/api/v1/` prefix — routes are mounted directly.

| Method | Path | Router | Purpose |
|--------|------|--------|---------|
| GET | `/health` | health.py | Liveness check — confirms API is running |
| GET | `/health/summary` | health.py | KPI health aggregate for the latest month |
| GET | `/priorities/latest` | priorities.py | All priority cards for the latest month |
| GET | `/priorities/{priority_id}` | priorities.py | Full evidence detail for one priority |
| GET | `/benchmark/{asset}/{metric}` | benchmark.py | 12-month benchmark time series for one metric |
| GET | `/signals` | signals.py | All validated leading indicator signals |
| GET | `/events` | events.py | All events with optional ?category= and ?year= filters |
| GET | `/events/{month}` | events.py | Events for a specific month (format: YYYY-MM) |
| POST | `/events` | events.py | Create a new event |
| DELETE | `/events/{event_id}` | events.py | Delete an event |
| GET | `/events/near/{asset}/{metric}/{month}` | events.py | Events within 30 days of metric month for chart annotation |
| GET | `/briefing/latest` | briefing.py | Monthly briefing executive summary |
| GET | `/refresh/status` | refresh.py | Pipeline data quality and freshness status |
| GET | `/analytics/seasonal/{asset}/{metric}` | analytics.py | Full 12-month seasonal baseline for a metric (V1.5.3) |
| GET | `/social/summary` | social.py | Latest month social media summary (V1.6.1) |
| GET | `/social/monthly` | social.py | 12-month social media trend data (V1.6.1) |
| GET | `/social/platforms/{month}` | social.py | Per-platform breakdown for specific month (V1.6.1) |
| GET | `/social/content/{month}` | social.py | Content type performance for specific month (V1.6.1) |
| GET | `/social/content-intelligence` | social.py | All content-to-commercial correlations (V1.6.4) |
| GET | `/social/content-intelligence/summary` | social.py | Strongest content-commercial relationships (V1.6.4) |
| GET | `/social/content-intelligence/{month}` | social.py | Month-specific content analysis with commercial context (V1.6.4) |
| GET | `/social/anomalies` | social.py | All detected social media anomalies (V1.6.5) |
| GET | `/social/anomalies/unconfirmed` | social.py | Social anomalies with no matching event in calendar (V1.6.5) |
| POST | `/social/anomalies/{month}/confirm` | social.py | Confirm anomaly as event, creates event in calendar (V1.6.5) |
| POST | `/social/anomalies/{month}/dismiss` | social.py | Dismiss anomaly (mark as not a real event) (V1.6.5) |
| GET | `/social/international?month={YYYY-MM}` | social.py | Language market breakdown (Spanish, English, Arabic, French, Other) with engagement, followers, percentages (V1.6.6) |
| GET | `/social/international/trend` | social.py | 12-month trend of international audience breakdown by language market (V1.6.6) |
| GET | `/social/international/correlation` | social.py | International engagement → commercial metric correlations (streaming, ecommerce) (V1.6.6) |
| GET | `/social/international/growth` | social.py | Market growth ranking sorted by month-over-month change (V1.6.6) |
| GET | `/social/analytics/dayofweek?platform={all}&match_moment={all}` | social.py | Day of week performance analysis with best/worst days, weekly averages (V1.7.0) |
| GET | `/social/analytics/moments?platform={all}` | social.py | Match moment performance analysis (pre/during/post/non-matchday) with underutilisation detection (V1.7.0) |
| GET | `/social/analytics/formats?platform={all}&scene={scene}` | social.py | Content format performance (Reel vs standard post multipliers, recommended formats) (V1.7.0) |
| GET | `/social/analytics/hashtags?platform={all}&hashtag_type={all}&min_posts=10` | social.py | Hashtag performance ranked by engagement, filtered by type (branded/event/player/farewell) (V1.7.0) |
| GET | `/social/analytics/insights?data_month={YYYY-MM}` | social.py | Dynamically generated InsightCards from live data (auto-refreshes with new uploads) (V1.7.0) |
| GET | `/social/analytics/recommendations?team=content` | social.py | Priority-ranked actionable recommendations for content team (CONVERT/SCHEDULE/INCREASE/REDUCE) (V1.7.0) |
| GET | `/social/analytics/peer/{metric}` | social.py | Peer comparison on analytics metrics (Real Madrid vs 9 clubs on goal_celebration_avg, post_match_avg, reel_multiplier, etc.) (V1.7.0) |

**CORS**: Allowed origins — `http://localhost:5176`, `http://127.0.0.1:5176`, `http://localhost:5177`, `http://127.0.0.1:5177`, `http://localhost:5174`, `http://127.0.0.1:5174`. All methods and headers allowed.

**Interactive docs**: `GET /docs` (Swagger UI auto-generated by FastAPI).

---

### 4.2 Endpoint Schemas

#### GET `/health`

**Purpose**: Liveness probe confirming the API process is running.

**Parameters**: None.

**Response schema** (`HealthCheckResponse`):
```json
{
  "status": "ok",
  "service": "clubos-api"
}
```

**Data source**: Hardcoded constants — no table read.

**Notes**: Returns 200 immediately. Does not check database connectivity or snapshot presence.

---

#### GET `/health/summary`

**Purpose**: Returns the aggregate health status of all tracked metrics for the latest month, used by the Command Center to render the summary cards, donut chart, and deviation index.

**Parameters**: None.

**Response schema** (`HealthSummaryResponse`):
```json
{
  "latest_month": "2026-01-01",
  "metric_count": 59,
  "good_count": 23,
  "review_count": 23,
  "stable_count": 13,
  "avg_abs_deviation": 0.187
}
```

| Field | Type | Description |
|-------|------|-------------|
| `latest_month` | string (date) | ISO 8601 date of the most recent month in gold_kpi_health |
| `metric_count` | int | Total distinct metric-asset combinations in the latest month |
| `good_count` | int | Count of metric rows with `health_status = good` |
| `review_count` | int | Count of metric rows with `health_status = review` |
| `stable_count` | int | Count of metric rows with `health_status = stable` |
| `avg_abs_deviation` | float (nullable) | Average of `abs(deviation_from_seasonal_baseline)` across all metrics for the latest month |

**Data source**: `gold_kpi_health` — filters to latest month, aggregates counts and average.

---

#### GET `/priorities/latest`

**Purpose**: Returns all priority cards for the latest month, enriched with trend history, peer comparison values, and score breakdown. This is the primary data source for the Priority Board screen.

**Parameters**: None.

**Response schema** (`PriorityListResponse`):
```json
{
  "latest_month": "2026-01-01",
  "items": [
    {
      "priority_id": "2026-01-01_ecommerce_conversion_rate",
      "month": "2026-01-01",
      "title": "Conversion Rate Decline in eCommerce",
      "category": "critical",
      "score": 0.847,
      "rank": 1,
      "asset_name": "ecommerce",
      "primary_metric": "conversion_rate",
      "summary_text": "...",
      "why_it_matters": "...",
      "suggested_next_investigation": "...",
      "consecutive_declining_months": 4,
      "trend_direction": "down",
      "trend_slope": -0.002,
      "score_breakdown": {
        "severity": 0.254,
        "persistence": 0.208,
        "peer_gap": 0.180,
        "commercial": 0.135,
        "evidence": 0.070
      },
      "historical_values": [
        {"month": "2025-02-01", "value": 0.0152},
        ...
      ],
      "peer_values": [
        {"club": "Real Madrid", "value": 0.0130},
        {"club": "masia_fc", "value": 0.0182},
        ...
      ],
      "peer_median": 0.0178,
      "peer_leader_value": 0.0210
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `latest_month` | string | Yes | ISO date of the month being reported |
| `items` | list[PriorityCard] | Yes | Ordered list, rank 1 first |
| `priority_id` | string | Yes | Composite unique identifier |
| `category` | string | Yes | `critical`, `opportunity`, `benchmark underperformance`, or `warning` |
| `score` | float | Yes | Priority score 0.0–1.0 |
| `rank` | int | Yes | Rank within the month (1 = highest) |
| `consecutive_declining_months` | int | No | How many sequential months this metric has trended down |
| `trend_direction` | string | No | `up`, `down`, or `flat` |
| `trend_slope` | float | No | 6-month linear regression slope |
| `score_breakdown` | ScoreBreakdown | No | Five weighted components summing to `score` |
| `historical_values` | list[HistoricalValue] | No | Up to 12 monthly `{month, value}` pairs for sparkline |
| `peer_values` | list[PeerValue] | No | `{club, value}` for all clubs (only for 8 benchmarked metrics) |
| `peer_median` | float | No | Peer median at latest month (null for non-benchmarked metrics) |
| `peer_leader_value` | float | No | Best peer value (null for non-benchmarked metrics) |

**Data source**: `gold_priority_board` + enrichment joins to `gold_kpi_health` (historical values, trend) and `gold_peer_benchmark` (peer values).

---

#### GET `/priorities/{priority_id}`

**Purpose**: Returns the full evidence detail for one specific priority. Used by the Priority Evidence Modal. Contains everything in `PriorityCard` plus the full `supporting_metrics` dict (parsed from `supporting_metrics_json`).

**Path parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `priority_id` | string | The `priority_id` value from the list endpoint (e.g. `2026-01-01_ecommerce_conversion_rate`) |

**Response schema** (`PriorityDetailResponse`): Same fields as `PriorityCard` plus:

| Field | Type | Description |
|-------|------|-------------|
| `supporting_metrics` | dict[str, Any] | Parsed JSON object from `supporting_metrics_json`: contains `score_components`, `severity_inputs`, `persistence_inputs`, `peer_context`, `linked_signal_references`, `supporting_metric_rows` |

**Error responses**:
- `404 Not Found`: `priority_id` not found in `gold_priority_board` (KeyError raised in service, caught in router)

**Data source**: `gold_priority_board` — single row lookup by `priority_id`.

---

#### GET `/benchmark/{asset}/{metric}`

**Purpose**: Returns the full 12-month (or all available) time series of Real Madrid's benchmark position for one metric. Used by the Peer Benchmark screen to render the rank snapshot, trend chart, and recent trend table.

**Path parameters**:
| Param | Type | Valid values |
|-------|------|-------------|
| `asset` | string | `main_website`, `ecommerce`, `streaming`, `fan_app` |
| `metric` | string | One of the 8 benchmarked metrics for the given asset |

**Response schema** (`BenchmarkResponse`):
```json
{
  "asset": "ecommerce",
  "metric": "conversion_rate",
  "latest_month": "2026-01-01",
  "points": [
    {
      "month": "2017-07-01",
      "rm_value": 0.0138,
      "peer_median": 0.0176,
      "peer_leader_value": 0.0210,
      "rm_rank": 5,
      "club_count": 6,
      "gap_to_peer_median": -0.0038,
      "gap_to_leader": -0.0072,
      "rank_change_12m": null,
      "gap_change_12m": null
    },
    ...
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `asset` | string | Echo of the path parameter |
| `metric` | string | Echo of the path parameter |
| `latest_month` | string (nullable) | Most recent month in the returned points |
| `points` | list[BenchmarkPoint] | All historical rows for this asset-metric pair, ordered chronologically |
| `rank_change_12m` | int (nullable) | Null for the first 12 months (no 12-month prior available) |
| `gap_change_12m` | float (nullable) | Null for the first 12 months |

**Data source**: `gold_peer_benchmark` — filtered to `(asset_name, metric_name)`.

**Notes**: Returns all historical months (up to 103), not just the last 12. Frontend slices to the last 12 for chart rendering. Frontend defaults to `ecommerce:conversion_rate` on first load.

---

#### GET `/signals`

**Purpose**: Returns all validated leading indicator signals, enriched with current source/target metric values and their connection to active priorities. Used by the Signal Engine screen.

**Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `signal_type` | string (query) | No | Filter signals by type. Options: `internal` (traditional cross-platform signals), `social_to_commercial` (social media as leading indicator for commercial outcomes), or omit for all signals (V1.6.2) |

**Response schema** (`SignalResponse`):
```json
{
  "latest_validated_month": "2026-01-01",
  "items": [
    {
      "signal_id": "main_website__unique_visitors__ecommerce__net_sales__1",
      "source_asset": "main_website",
      "source_metric": "unique_visitors",
      "target_asset": "ecommerce",
      "target_metric": "net_sales",
      "lag_months": 1,
      "relationship_direction": "positive",
      "strength_score": 0.699,
      "validation_status": "active",
      "business_interpretation": "Top-of-funnel traffic volume strongly leads ecommerce net_sales shortly after.",
      "last_validated_month": "2026-01-01",
      "current_status": "firing_positive",
      "status_meaning": "Source metric is rising; target expected to rise in 1 month.",
      "source_trend_direction": "up",
      "source_current_trend": 0.021,
      "source_trend_pct_change": 3.2,
      "source_current_value": 1840000,
      "target_current_value": 285000,
      "target_health_status": "review",
      "priority_connection": {
        "has_connection": true,
        "metric": "net_sales",
        "rank": 2,
        "score": 0.731,
        "interpretation": "This signal feeds Priority #2 on the board.",
        "border_color": "critical"
      }
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `latest_validated_month` | string (nullable) | Most recent validation month across all signals |
| `signal_id` | string | Composite key (not stored in table — computed by service) |
| `current_status` | string (nullable) | `firing_positive`, `firing_negative`, `neutral`, or `unknown` — derived from current source metric trend |
| `source_trend_pct_change` | float (nullable) | Month-over-month percentage change in source metric |
| `priority_connection` | PriorityConnection (nullable) | Whether this signal's target metric appears in the current Priority Board |

**Data source**: `gold_signal_relationships` + enrichment from `gold_kpi_health` (current values, trends) and `gold_priority_board` (priority connections).

---

#### GET `/briefing/latest`

**Purpose**: Returns the complete Monthly Briefing executive summary for the latest month. Aggregates all briefing inputs into typed sub-objects. Used by the Monthly Briefing screen.

**Parameters**: None.

**Response schema** (`BriefingResponse`):
```json
{
  "month": "2026-01-01",
  "top_priorities": [
    {
      "priority_id": "2026-01-01_ecommerce_conversion_rate",
      "priority_rank": 1,
      "priority_title": "Conversion Rate Decline in eCommerce",
      "priority_category": "critical",
      "priority_score": 0.847
    }
  ],
  "top_anomalies": [
    {
      "anomaly_rank": 1,
      "asset_name": "streaming",
      "metric_name": "daily_users",
      "metric_value": 5275.2,
      "deviation_from_seasonal_baseline": -0.293
    }
  ],
  "strongest_signals": [
    {
      "signal_rank": 1,
      "signal_id": "main_website__unique_visitors__ecommerce__net_sales__1",
      "source_asset": "main_website",
      "source_metric": "unique_visitors",
      "target_asset": "ecommerce",
      "target_metric": "net_sales",
      "lag_months": 1,
      "relationship_direction": "positive",
      "strength_score": 0.699
    }
  ],
  "benchmark_summary": {
    "benchmarked_metric_count": 8,
    "benchmark_underperformance_count": 5,
    "avg_gap_to_peer_median": -12450.3,
    "worst_gap_to_peer_median": -38054.4
  },
  "health_summary": {
    "metric_count": 59,
    "good_count": 23,
    "review_count": 23,
    "stable_count": 13,
    "avg_abs_deviation": 0.187
  }
}
```

**Data source**: `gold_monthly_brief_inputs` (latest month row) — JSON fields are parsed and then joined to `gold_priority_board` for priority titles/categories, `gold_signal_relationships` for signal details, and `gold_kpi_health` for anomaly metric values.

**Notes**: `benchmark_summary` and `health_summary` are nullable — returned as null if the briefing inputs row lacks these JSON blobs (can occur in the earliest months of the dataset before all pipeline stages ran).

---

#### GET `/refresh/status`

**Purpose**: Returns the current pipeline data quality status. Used by operators and could be wired to a frontend status indicator. Reads from the `silver_data_quality_checks` snapshot.

**Parameters**: None.

**Response schema** (`RefreshStatusResponse`):
```json
{
  "status": "ok",
  "last_run_timestamp": "2026-01-15T03:00:00Z",
  "latest_gold_month": "2026-01-01",
  "required_failed_checks_count": 0,
  "message": "All required checks passed."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `ok`, `warning`, or `error` |
| `last_run_timestamp` | string (nullable) | ISO timestamp of most recent quality check run |
| `latest_gold_month` | string (nullable) | Most recent month present in Gold tables |
| `required_failed_checks_count` | int | Count of `REQUIRED` severity checks that returned `FAIL` |
| `message` | string | Human-readable summary of pipeline health |

**Data source**: `silver_data_quality_checks` (CSV snapshot).

---

## 5. Pydantic Models

All models use Pydantic v2 (`pydantic==2.8.2`). FastAPI validates all responses against these schemas at runtime before returning JSON.

### 5.1 ScoreBreakdown

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `severity` | float | Yes | Weighted severity contribution (max 0.30) |
| `persistence` | float | Yes | Weighted persistence contribution (max 0.25) |
| `peer_gap` | float | Yes | Weighted peer gap contribution (max 0.20) |
| `commercial` | float | Yes | Weighted commercial weight contribution (max 0.15) |
| `evidence` | float | Yes | Weighted supporting evidence contribution (max 0.10) |

### 5.2 HistoricalValue

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `month` | str | Yes | ISO date string (YYYY-MM-DD) |
| `value` | float | Yes | Metric value for this month |

### 5.3 PeerValue

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `club` | str | Yes | Club name (e.g. `Real Madrid`, `masia_fc`, `merseyside_red`) |
| `value` | float | Yes | Club's metric value for the latest month |

### 5.4 PriorityCard

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `priority_id` | str | Yes | Composite unique ID |
| `month` | str | Yes | Reporting month (ISO date) |
| `title` | str | Yes | Human-readable priority headline |
| `category` | str | Yes | `critical`, `opportunity`, `benchmark underperformance`, `warning` |
| `score` | float | Yes | Priority score 0.0–1.0 |
| `rank` | int | Yes | Ordinal rank within the month |
| `asset_name` | str | Yes | Digital platform |
| `primary_metric` | str | Yes | Canonical metric name |
| `summary_text` | str | Yes | One-sentence metric status summary |
| `why_it_matters` | str | Yes | Commercial significance explanation |
| `suggested_next_investigation` | str | Yes | Recommended next step |
| `consecutive_declining_months` | int | No | Months of consecutive decline (nullable) |
| `trend_direction` | str | No | `up`, `down`, or `flat` (nullable) |
| `trend_slope` | float | No | 6-month regression slope (nullable) |
| `score_breakdown` | ScoreBreakdown | No | Five score components (nullable) |
| `historical_values` | list[HistoricalValue] | No | Sparkline data (nullable) |
| `peer_values` | list[PeerValue] | No | Per-club comparison (nullable; benchmarked metrics only) |
| `peer_median` | float | No | Peer median at latest month (nullable) |
| `peer_leader_value` | float | No | Best peer value (nullable) |
| `seasonal_context` | dict[str, Any] | No | Seasonal baseline intelligence (V1.5.3): seasonal_mean, seasonal_std, z_score, is_within_normal_range, interpretation, etc. (nullable) |
| `conversion_context` | dict[str, Any] | No | Conversion rate + volume pairing (V1.5.4): quadrant, label, interpretation, color, conversion_rate_value, visitors_value, etc. Only populated for conversion_rate metric (nullable) |

### 5.5 PriorityListResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `latest_month` | str | Yes | Most recent month in the priority dataset |
| `items` | list[PriorityCard] | Yes | All priority cards, ordered by rank ascending |

### 5.6 PriorityDetailResponse

Same fields as `PriorityCard` plus:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `supporting_metrics` | dict[str, Any] | Yes | Parsed supporting_metrics_json object — contains score_components, severity_inputs, persistence_inputs, peer_context, linked_signal_references, supporting_metric_rows |

### 5.7 HealthCheckResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | str | Yes | Always `"ok"` for liveness |
| `service` | str | Yes | Always `"clubos-api"` |

### 5.8 HealthSummaryResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `latest_month` | str | Yes | ISO date of latest month in health data |
| `metric_count` | int | Yes | Total metric-asset pairs tracked |
| `good_count` | int | Yes | Metrics with `health_status = good` |
| `review_count` | int | Yes | Metrics with `health_status = review` |
| `stable_count` | int | Yes | Metrics with `health_status = stable` |
| `avg_abs_deviation` | float | No | Average absolute deviation from seasonal baseline (nullable) |

### 5.9 BenchmarkPoint

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `month` | str | Yes | ISO date |
| `rm_value` | float | Yes | Real Madrid's value |
| `peer_median` | float | Yes | Peer median (excluding Real Madrid) |
| `peer_leader_value` | float | Yes | Best-in-class value |
| `rm_rank` | int | Yes | Real Madrid's rank (1 = best) |
| `club_count` | int | Yes | Total clubs in comparison |
| `gap_to_peer_median` | float | Yes | Polarity-adjusted gap (positive = ahead) |
| `gap_to_leader` | float | Yes | Polarity-adjusted gap to leader |
| `rank_change_12m` | int | No | Rank delta vs 12 months prior (nullable) |
| `gap_change_12m` | float | No | Gap delta vs 12 months prior (nullable) |

### 5.10 BenchmarkResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `asset` | str | Yes | Asset name echo |
| `metric` | str | Yes | Metric name echo |
| `latest_month` | str | No | Most recent month in points (nullable) |
| `points` | list[BenchmarkPoint] | Yes | All historical data points, chronological |

### 5.11 PriorityConnection

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `has_connection` | bool | Yes | Whether signal target metric appears in Priority Board |
| `metric` | str | No | Connected metric name (nullable if no connection) |
| `rank` | int | No | Priority rank of the connection (nullable) |
| `score` | float | No | Priority score of the connection (nullable) |
| `interpretation` | str | Yes | Plain-English description of the connection |
| `border_color` | str | Yes | UI colour token: `critical`, `good`, or `neutral` |

### 5.12 SignalItem

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signal_id` | str | Yes | Composite key (computed) |
| `source_asset` | str | Yes | Source platform |
| `source_metric` | str | Yes | Source metric name |
| `target_asset` | str | Yes | Target platform |
| `target_metric` | str | Yes | Target metric name |
| `lag_months` | int | Yes | 1, 2, or 3 |
| `relationship_direction` | str | Yes | `positive` or `negative` |
| `strength_score` | float | Yes | Pearson r, 0.6–1.0 |
| `validation_status` | str | Yes | `active` or `inactive` |
| `business_interpretation` | str | Yes | Plain-English signal explanation |
| `last_validated_month` | str | Yes | ISO date of last successful validation |
| `current_status` | str | No | `firing_positive`, `firing_negative`, `neutral`, `unknown` (nullable) |
| `status_meaning` | str | No | Human-readable status description (nullable) |
| `source_trend_direction` | str | No | `up`, `down`, `flat` (nullable) |
| `source_current_trend` | float | No | Trend slope value (nullable) |
| `source_trend_pct_change` | float | No | Month-over-month % change in source (nullable) |
| `source_current_value` | float | No | Latest source metric value (nullable) |
| `target_current_value` | float | No | Latest target metric value (nullable) |
| `target_health_status` | str | No | `good`, `review`, `stable` (nullable) |
| `priority_connection` | PriorityConnection | No | Priority Board link (nullable) |
| `driver_label` | str | Yes | "Independent Variable (Driver)" — label for source metric role (V1.5.5) |
| `outcome_label` | str | Yes | "Dependent Variable (Outcome)" — label for target metric role (V1.5.5) |
| `causal_direction_statement` | str | No | Plain-English explanation of causality direction (V1.5.5, nullable) |
| `action_statement` | str | No | Recommended action based on current signal status (V1.5.5, nullable) |
| `relationship_type` | str | No | `leading_indicator`, `concurrent`, or `unclear` — based on lag (V1.5.5, nullable) |
| `signal_type` | str | No | Signal classification: `internal` (cross-platform) or `social_to_commercial` (V1.6.2, default: "internal") |

### 5.13 SignalResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `latest_validated_month` | str | No | Most recent validation month (nullable) |
| `items` | list[SignalItem] | Yes | All signals (active and inactive) |

### 5.14 BriefingPriority

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `priority_id` | str | Yes | Priority identifier |
| `priority_rank` | int | Yes | Rank within the month |
| `priority_title` | str | Yes | Priority headline |
| `priority_category` | str | Yes | Category label |
| `priority_score` | float | Yes | Priority score 0.0–1.0 |

### 5.15 BriefingAnomaly

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `anomaly_rank` | int | Yes | Rank by absolute deviation magnitude |
| `asset_name` | str | Yes | Digital platform |
| `metric_name` | str | Yes | Metric displaying anomalous behaviour |
| `metric_value` | float | Yes | Actual metric value this month |
| `deviation_from_seasonal_baseline` | float | Yes | Signed percentage deviation (negative = below baseline) |

### 5.16 BriefingSignal

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signal_rank` | int | Yes | Rank by strength_score descending |
| `signal_id` | str | Yes | Composite signal identifier |
| `source_asset` | str | Yes | Source platform |
| `source_metric` | str | Yes | Source metric |
| `target_asset` | str | Yes | Target platform |
| `target_metric` | str | Yes | Target metric |
| `lag_months` | int | Yes | Lag window |
| `relationship_direction` | str | Yes | `positive` or `negative` |
| `strength_score` | float | Yes | Pearson r |

### 5.17 BriefingBenchmarkSummary

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `benchmarked_metric_count` | int | Yes | Number of metrics with peer benchmark data |
| `benchmark_underperformance_count` | int | Yes | Metrics where gap_to_peer_median < 0 |
| `avg_gap_to_peer_median` | float | Yes | Average gap across all benchmarked metrics (polarity-adjusted) |
| `worst_gap_to_peer_median` | float | Yes | Worst single gap to peer median |

### 5.18 BriefingHealthSummary

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `metric_count` | int | Yes | Total metrics tracked |
| `good_count` | int | Yes | Good health count |
| `review_count` | int | Yes | Review needed count |
| `stable_count` | int | Yes | Stable count |
| `avg_abs_deviation` | float | Yes | Average absolute seasonal deviation |

### 5.19 BriefingResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `month` | str | Yes | Reporting month (ISO date) |
| `top_priorities` | list[BriefingPriority] | Yes | Top-ranked priorities (ordered) |
| `top_anomalies` | list[BriefingAnomaly] | Yes | Top anomalies by absolute deviation |
| `strongest_signals` | list[BriefingSignal] | Yes | Signals ordered by strength_score descending |
| `benchmark_summary` | BriefingBenchmarkSummary | No | Benchmark aggregate (nullable) |
| `health_summary` | BriefingHealthSummary | No | Health aggregate (nullable) |

### 5.20 RefreshStatusResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | str | Yes | `ok`, `warning`, or `error` |
| `last_run_timestamp` | str | No | ISO timestamp of last quality check run (nullable) |
| `latest_gold_month` | str | No | Most recent Gold month (nullable) |
| `required_failed_checks_count` | int | Yes | Count of failed REQUIRED checks (default 0) |
| `message` | str | Yes | Human-readable pipeline status summary |

### 5.21 MessageResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | str | Yes | Generic message string for simple responses |

### 5.22 ContentSignal (V1.6.4)

Represents a validated correlation between a social media content type and a commercial metric.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content_type` | str | Yes | Content type identifier: `goal_celebration`, `training`, `score_graphic`, `player_arrival`, `lineup_graphic`, `birthday`, `game_preview` |
| `commercial_metric` | str | Yes | Commercial metric name: `net_sales`, `conversion_rate`, `unique_visitors`, `visits`, `subscriptions`, `daily_users`, `matchday_visits` |
| `commercial_asset` | str | Yes | Commercial asset: `ecommerce`, `main_website`, `streaming`, `fan_app` |
| `correlation` | float | Yes | Pearson correlation coefficient (-1 to 1) |
| `lag_months` | int | Yes | Time lag between content and commercial metric (0, 1, or 2 months) |
| `direction` | str | Yes | Relationship direction: `"positive"` or `"negative"` |
| `interpretation` | str | Yes | Business-readable explanation of the correlation |
| `strength_label` | str | Yes | Correlation strength: `"Strong"` (>0.65), `"Moderate"` (0.55-0.65), `"Weak"` (0.45-0.55) |
| `confidence_note` | str | Yes | Statistical confidence note: `"Based on 12 months of data — provisional"` |
| `avg_content_engagement` | float | Yes | Average engagement per post for this content type |
| `sample_size_months` | int | Yes | Number of months used in correlation analysis (min 6) |

**Validation rules**:
- Correlation threshold: `abs(correlation) >= 0.45` (lower than internal signals' 0.60 because content correlations are inherently noisier)
- Sample size: minimum 6 months of overlapping data
- Content types are from gold_social_metrics content performance columns
- Commercial metrics are from gold_kpi_health asset performance rows

### 5.23 ContentCommercialSummary (V1.6.4)

Summary of strongest content-to-commercial relationships.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strongest_signal` | ContentSignal | No | The strongest correlation found (nullable if no correlations found) |
| `total_correlations_found` | int | Yes | Total number of correlations exceeding threshold |
| `avg_correlation_strength` | float | Yes | Average absolute correlation across all signals |
| `most_predictive_content_type` | str | Yes | Content type appearing in most correlations |
| `most_influenced_commercial_metric` | str | Yes | Commercial metric appearing in most correlations |

### 5.24 ContentMonthlyPerformance (V1.6.4)

Content type performance for a specific month with commercial context.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `month` | str | Yes | Month in ISO format (YYYY-MM-DD) |
| `content_performances` | list[dict] | Yes | List of `{content_type: str, avg_engagement: float}` sorted by engagement |
| `commercial_outcomes` | list[dict] | Yes | List of `{metric: str, asset: str, value: float, vs_baseline_pct: float | null}` for the month |
| `matching_correlations` | list[str] | Yes | Interpretations of active correlations this month |

### 5.25 ContentIntelligenceResponse (V1.6.4)

Full response for GET /social/content-intelligence endpoint.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `latest_month` | str | Yes | Latest month in social media data (ISO format) |
| `signals` | list[ContentSignal] | Yes | All computed content-to-commercial correlations |
| `summary` | ContentCommercialSummary | Yes | Aggregate statistics and strongest signal |

### 5.26 SocialAnomaly (V1.6.5)

Detected social media anomaly (spike/drop >2 std from mean). Used for event confirmation workflow.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `month` | str | Yes | Month of anomaly (ISO date YYYY-MM-DD) |
| `metric` | str | Yes | Metric that showed anomaly (e.g., "total_engagement", "goal_celebration_avg_engagement") |
| `actual_value` | float | Yes | Actual metric value in this month |
| `mean_value` | float | Yes | Mean value across all 12 months |
| `std_value` | float | Yes | Standard deviation across all months |
| `z_score` | float | Yes | Z-score (how many std deviations from mean). Abs value must be >2.0 |
| `direction` | str | Yes | `"spike"` (above mean) or `"drop"` (below mean) |
| `likely_cause` | str | Yes | Classified cause: `match_result_win`, `match_result_loss`, `trophy_win`, `media_event`, `player_signing`, `injury_news`, `poor_match_result` |
| `candidate_event_name` | str | Yes | Auto-generated event name for confirmation: `"{YYYY-MM} Social {Spike|Drop} — {Likely Cause}"` |
| `candidate_category` | str | Yes | Suggested event category (maps to EventCategory enum) |
| `is_confirmed` | bool | Yes | Whether anomaly has been confirmed as an event (always `false` for unconfirmed list) |
| `confidence_level` | str | Yes | `"high"` (abs z_score > 3.0), `"medium"` (> 2.5), `"low"` (> 2.0) |

**Detection logic**:
- Computes mean/std for 8 social metrics across all 12 months
- Flags months where abs(value - mean) > 2.0 * std
- Classifies likely cause based on metric combination (e.g., goal_celebration spike + total_engagement spike = match_result_win)

### 5.27 SocialAnomalyListResponse (V1.6.5)

Response for anomaly list endpoints.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_count` | int | Yes | Total number of anomalies |
| `items` | list[SocialAnomaly] | Yes | List of detected anomalies |

### 5.28 ConfirmAnomalyRequest (V1.6.5)

Request body for POST /social/anomalies/{month}/confirm.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `confirmed_name` | str | Yes | Event name (user can edit from candidate_event_name) |
| `confirmed_category` | str | Yes | Event category (user can edit from candidate_category) |
| `description` | str | Yes | Event description (auto-generated from anomaly details, editable) |
| `impact_magnitude` | str | Yes | `"high"`, `"medium"`, or `"low"` |
| `affected_assets` | str | Yes | Comma-separated asset names (default: `"social_media"`) |

**Workflow**: When confirmed, creates a new event in gold_events.csv via event_service.create_event(). The anomaly then disappears from GET /social/anomalies/unconfirmed response.

### 5.29 LanguageBreakdown (V1.6.6)

Language market engagement breakdown for international audience analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `language` | str | Yes | Language market: Spanish, English, Arabic, French, Other |
| `account_username` | str \| None | No | Primary account username for this market (e.g., "realmadriden") |
| `monthly_engagement` | float | Yes | Total engagement from this market |
| `follower_count` | int \| None | No | Follower count for this market account (if known) |
| `engagement_per_follower` | float \| None | No | Engagement divided by follower count |
| `pct_of_total_engagement` | float | Yes | Percentage of total engagement from this market |
| `mom_change` | float \| None | No | Month-over-month percentage change (None for first month) |

### 5.30 InternationalBreakdownResponse (V1.6.6)

Response from GET /social/international.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `month` | str | Yes | Month ISO date YYYY-MM-DD |
| `language_markets` | list[LanguageBreakdown] | Yes | Breakdown by language market (5 markets) |
| `total_international_engagement` | float | Yes | Sum of all non-Spanish engagement |
| `international_engagement_ratio` | float | Yes | Non-Spanish / total (value in [0,1]) |

### 5.31 InternationalTrendPoint (V1.6.6)

Single month data point in international audience trend.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `month` | str | Yes | Month ISO date YYYY-MM-DD |
| `spanish_engagement` | float | Yes | Spanish account engagement |
| `english_engagement` | float | Yes | English account engagement |
| `arabic_engagement` | float | Yes | Arabic account engagement |
| `french_engagement` | float | Yes | French account engagement |
| `other_engagement` | float | Yes | Other language accounts engagement |
| `international_ratio` | float | Yes | Non-Spanish / total |

### 5.32 InternationalTrendResponse (V1.6.6)

Response from GET /social/international/trend.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trend` | list[InternationalTrendPoint] | Yes | 12-month time series |

### 5.33 MarketGrowthRanking (V1.6.6)

Market growth ranking entry.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market` | str | Yes | Language market name |
| `this_month` | float | Yes | Current month engagement |
| `prior_month` | float | Yes | Prior month engagement |
| `mom_change_pct` | float | Yes | Month-over-month percentage change |

### 5.34 MarketGrowthRankingResponse (V1.6.6)

Response from GET /social/international/growth.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `month` | str | Yes | Current month ISO date YYYY-MM-DD |
| `rankings` | list[MarketGrowthRanking] | Yes | Markets sorted by MoM change descending |

### 5.35 InternationalCommercialCorrelation (V1.6.6)

Correlation between international_engagement_ratio and a commercial metric.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `commercial_metric` | str | Yes | Commercial metric name (e.g., "active_subscriptions") |
| `commercial_asset` | str | Yes | Asset name (e.g., "streaming") |
| `correlation` | float | Yes | Pearson correlation coefficient |
| `lag_months` | int | Yes | Lag in months (0-3) |
| `direction` | str | Yes | Relationship direction: "positive" or "negative" |
| `strength_label` | str | Yes | Strength label: "Strong", "Moderate", "Weak" |
| `interpretation` | str | Yes | Human-readable interpretation of relationship |
| `passes_threshold` | bool | Yes | Whether correlation >= 0.45 |

### 5.36 InternationalCommercialCorrelationResponse (V1.6.6)

Response from GET /social/international/correlation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `correlations` | list[InternationalCommercialCorrelation] | Yes | All correlations found |
| `strongest_correlation` | InternationalCommercialCorrelation \| None | Yes | Strongest correlation if any pass threshold |

---

## 6. Dual-Mode Architecture

### 6.1 Snapshot Mode (default for local development and demos)

In snapshot mode the backend serves all API responses from pre-exported CSV files stored locally in `data/gold_snapshots/`. No Databricks credentials are required.

**How it works**:
1. `DatabricksClient.__init__` reads `CLUBOS_GOLD_SNAPSHOT_DIR` from settings (defaults to the absolute path of `data/gold_snapshots/` relative to the repository root, if that directory exists)
2. `_live_mode_enabled()` returns `False` (no host/token/path/catalog/schema configured)
3. `read_table(table_name)` calls `_read_snapshot(table_name)`
4. `_read_snapshot` looks for `{snapshot_dir}/{table_name}.json`, then `.csv`, then `.parquet` — first match wins
5. CSV files are read with `pandas.read_csv()`, converted to `list[dict]` via `.to_dict(orient="records")`
6. Service functions receive the list of dicts and filter/aggregate in Python (no SQL)

**Current snapshot files**:
- `gold_priority_board.csv`
- `gold_kpi_health.csv`
- `gold_peer_benchmark.csv`
- `gold_signal_relationships.csv`
- `gold_monthly_brief_inputs.csv`
- `silver_data_quality_checks.csv` (for refresh status)

**Staleness risk**: Snapshot CSVs must be manually refreshed when Gold table schemas change (column adds, renames). No automatic sync. A schema drift between CSVs and Pydantic models will surface as a runtime validation error when FastAPI validates the response.

---

### 6.2 Live Databricks Mode

In live mode the backend queries Delta Lake tables directly via a Databricks SQL Warehouse using `databricks-sql-connector`.

**How it works**:
1. All five env vars are set: `CLUBOS_DATABRICKS_HOST`, `CLUBOS_DATABRICKS_TOKEN`, `CLUBOS_DATABRICKS_HTTP_PATH`, `CLUBOS_DATABRICKS_CATALOG`, `CLUBOS_DATABRICKS_SCHEMA`
2. `_live_mode_enabled()` returns `True`
3. `read_table(table_name)` calls `_read_live(table_name)`
4. `_read_live` constructs `SELECT * FROM {catalog}.{schema}.{table_name}` and executes it against the SQL Warehouse
5. Results are returned as `list[dict]` — column names from `cursor.description`, values from row tuples
6. Service functions receive the same `list[dict]` structure as in snapshot mode — identical downstream processing

**Connection**: One connection opened per API request via `sql.connect()` context manager. No connection pooling in the current MVP (single-threaded backend).

**Fallback**: If `databricks-sql-connector` is not installed, `_read_live` raises `SnapshotAccessError` with a descriptive message. FastAPI catches this via the registered `SnapshotAccessError` exception handler and returns HTTP 503.

---

### 6.3 Mode Detection Logic

Mode is determined at call time (not at startup) by `DatabricksClient._live_mode_enabled()`:

```python
def _live_mode_enabled(self) -> bool:
    return bool(
        self.host        # CLUBOS_DATABRICKS_HOST
        and self.token   # CLUBOS_DATABRICKS_TOKEN
        and self.http_path   # CLUBOS_DATABRICKS_HTTP_PATH
        and self.catalog     # CLUBOS_DATABRICKS_CATALOG
        and self.schema      # CLUBOS_DATABRICKS_SCHEMA
    )
```

**Decision tree**:
1. All five Databricks env vars set and non-empty → **Live Databricks mode**
2. Any of the five missing → `_live_mode_enabled()` returns `False`
3. `CLUBOS_GOLD_SNAPSHOT_DIR` set and points to a directory containing CSV/JSON/Parquet files → **Snapshot mode**
4. `CLUBOS_GOLD_SNAPSHOT_DIR` not set or empty → `SnapshotAccessError` raised → HTTP 503 returned to frontend

**Default behaviour** (no env vars set, running from repository root): `CLUBOS_GOLD_SNAPSHOT_DIR` defaults to the absolute path of `data/gold_snapshots/` in the repository. If that directory exists and contains CSVs, snapshot mode activates automatically with no configuration required. If the directory is missing, every API call returns 503.

---

## 7. Environment Variables

All variables are read by `pydantic_settings.BaseSettings` from the environment or from a `.env` file at the working directory where uvicorn is launched.

| Variable | Required | Mode | Default | Description |
|----------|----------|------|---------|-------------|
| `CLUBOS_API_HOST` | No | Both | `0.0.0.0` | Host address for the uvicorn server |
| `CLUBOS_API_PORT` | No | Both | `8000` | Port for the uvicorn server |
| `CLUBOS_DATABRICKS_HOST` | No | Live only | None | Databricks workspace URL (e.g. `https://adb-xxx.azuredatabricks.net`) |
| `CLUBOS_DATABRICKS_TOKEN` | No | Live only | None | Databricks personal access token for authentication |
| `CLUBOS_DATABRICKS_HTTP_PATH` | No | Live only | None | SQL Warehouse HTTP path (e.g. `/sql/1.0/warehouses/xxx`) |
| `CLUBOS_DATABRICKS_CATALOG` | No | Live only | None | Unity Catalog name containing the Gold tables |
| `CLUBOS_DATABRICKS_SCHEMA` | No | Live only | None | Schema/database name within the catalog (e.g. `gold`) |
| `CLUBOS_GOLD_SNAPSHOT_DIR` | No | Snapshot only | `data/gold_snapshots/` (auto-detected) | Absolute or relative path to directory containing Gold CSV/JSON/Parquet snapshot files |
| `CLUBOS_AI_PROVIDER` | No | Both | None | AI provider name (reserved for future briefing generation — not used in current MVP) |
| `CLUBOS_AI_API_KEY` | No | Both | None | API key for AI provider (reserved — not used in current MVP) |

**Startup behaviour**: `Settings` is instantiated once at module import time (`settings = Settings()`). The `DatabricksClient` is instantiated by service modules when they first need data. No startup lifespan hook — the app does not pre-load data into memory.

**Security note**: `.env` files are in `.gitignore`. `CLUBOS_DATABRICKS_TOKEN` must never be committed to version control.

---

## 8. Runtime Versions

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.11.x | `requires-python = ">=3.11"` in pyproject.toml |
| FastAPI | 0.115.0 | Web framework + automatic OpenAPI doc generation |
| Uvicorn | 0.30.6 | ASGI server (`uvicorn[standard]` — includes watchfiles for `--reload`) |
| Pydantic | 2.8.2 | Response schema validation (v2 API — uses `model_config`, not `class Config`) |
| pydantic-settings | 2.3.4 | Environment variable loading via `BaseSettings` |
| pandas | 2.2.2 | CSV snapshot reading and in-memory data manipulation |
| httpx | 0.27.2 | HTTP client (used in test suite — not in production request handling) |
| openpyxl | 3.1.5 | Excel file reading (available for ingestion — not used in current API) |
| databricks-sql-connector | — | Optional; not in pyproject.toml — must be installed separately for live mode |
| Node.js | 20.16.0 | Frontend runtime (pinned in `.nvmrc`) |
| Vite | 5.x | Frontend build tool (dev server port 5176) |

---
