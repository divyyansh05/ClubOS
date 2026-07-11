# Cross-Source Data Integrity Report

Sources compared: `gold.priority_board` vs `gold.kpi_health`
Tolerance: absolute 1e-06, relative 0.50%

## Summary

- Cross-source (asset, metric) pairs: **57**
- Overlapping (asset, metric, period) triples: **1020**
- **Value divergences** (same period, different value): **0**
- **Coverage gaps** (period in one source but not the other): **4851**
  - Periods only in kpi_health (missed by priority_board): **4851**
  - Periods only in priority_board (missed by kpi_health): **0**

## Value Divergences

**None.** When both sources have data for the same (asset, metric, period),
values agree within tolerance. The gold layer is internally consistent.

## Coverage Gaps — Periods only in kpi_health

These months exist in kpi_health but NOT in priority_board.
GoldClient's current priority (priority_board first) silently skips them,
returning the wrong period when only kpi_health has the requested month.

| Asset | Metric | Months missing from priority_board |
|---|---|---|
| ecommerce | recurrence | 102 months |
| main_website | mobile_visits | 102 months |
| streaming | video_recurrence | 102 months |
| ecommerce | product_views_rate | 101 months |
| main_website | new_users | 101 months |
| main_website | other_channels_visits | 101 months |
| streaming | other_traffic_plays | 101 months |
| fan_app | deeplink_visits | 100 months |
| main_website | logged_users | 100 months |
| main_website | international_visits | 99 months |
| main_website | social_organic_visits | 99 months |
| ecommerce | social_organic_purchases | 98 months |
| fan_app | logged_users | 98 months |
| fan_app | other_channel_visits | 98 months |
| ecommerce | other_channels_purchases | 97 months |
| fan_app | app_push_visits | 97 months |
| fan_app | user_rating | 97 months |
| main_website | page_views | 97 months |
| fan_app | organic_launch_visits | 96 months |
| streaming | marketing_plays | 96 months |

## Root Cause of gq_062 Failure

`ecommerce/conversion_rate` for November 2025 exists in kpi_health (0.014637) but NOT
in priority_board. GoldClient tries priority_board first and finds other months (Oct 2025,
Jan 2026) — so it returns without falling through to kpi_health. Scout receives no Nov 2025
data and returns a wrong-period value.

**Fix:** When `preferred_source = gold.kpi_health`, GoldClient tries kpi_health first.
Since kpi_health has 6× more (metric, period) coverage, preferred_source should default
to kpi_health for all 57 cross-source metrics.

## Finding for v1 pipeline session

priority_board has sporadic period gaps for many metrics. This is likely because the
priority board pipeline only writes a row when a metric exceeds the priority threshold.
Metrics that are healthy (below threshold) have no priority_board row for that month.
kpi_health is written for every metric every month regardless of health status.
This is an intentional pipeline difference, not a bug — but it means priority_board
is NOT a reliable source for absolute metric values. kpi_health is always preferred.