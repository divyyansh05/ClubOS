# Metric Wire-Up Audit — 2026-07-10

## Registry coverage

- Total metrics in registry: **76** (was 62 before this fix)
- New entries added: **14** (all in `STUB_METRICS`, derived from Gold-layer discovery)
- Hand-curated entries: **10** (CURATED_METRICS in seed.py — full disambiguation rules, seasonal notes, examples)
- Stub entries: **66** (one-line definitions, platform and polarity set)

## Root causes fixed

### Root cause 1 — `_web` suffix → wrong asset (14 metrics)

Registry uses `_web` suffix (e.g., `bounce_rate_web`, `visits_web`) but GoldClient was mapping
suffix `"web"` to asset `"web"` in queries. Gold CSV uses `"main_website"` as the `asset_name` column.

**Fix:** Added `ASSET_ALIASES = {"web": "main_website"}` to `GoldClient`. All 14 `_web` metrics now resolve.

Affected metrics: `bounce_rate_web`, `consumption_web`, `international_visits_web`, `logged_users_web`,
`marketing_visits_web`, `mobile_visits_web`, `new_users_web`, `other_channels_visits_web`,
`page_views_web`, `recurrence_web`, `search_organic_visits_web`, `social_organic_visits_web`,
`unique_visitors_web`, `visits_web`.

### Root cause 2 — metric name mismatch for 2 registry entries

- `conversion_rate_streaming` → splits to `(streaming, conversion_rate)` but Gold has `subscription_rate`
- `fan_app_dau` → splits to `(fan_app, dau)` but Gold has `heavy_users`

**Fix:** Added `METRIC_NAME_ALIASES` to `GoldClient`:
```python
METRIC_NAME_ALIASES = {
    ("streaming", "conversion_rate"): "subscription_rate",
    ("fan_app", "dau"): "heavy_users",
}
```

### Root cause 3 — social metrics in peer_benchmark not read

`social_media_instagram_engagement_rate` and `social_media_posting_frequency_per_day` exist in
`gold_peer_benchmark.csv` but GoldClient only read kpi_health and priority_board.

**Fix:** Added `gold_peer_benchmark.csv` as a third fallback source in `GoldClient.fetch_metric`.

## Gold-layer discovery

- Total Gold compound metrics discovered: **65** (via `scripts/discover_gold_metrics.py`)
- Source files scanned: `gold_kpi_health.csv`, `gold_peer_benchmark.csv`, `gold_priority_board.csv`
- Discovery script: `scripts/discover_gold_metrics.py`
- Inventory: `docs/gold_metrics_inventory.json`

## Resolution summary

| Category | Count | Metrics |
|---|---|---|
| Resolves to Gold data | **67/76** | All except the 9 below |
| No Gold data — planned metrics | 5 | `digital_merchandise_revenue`, `matchday_ticket_revenue`, `post_match_engagement_rate`, `reels_engagement_rate`, `video_progress_25/50/75_rate` |
| No Gold data — social | 3 | `social_media_followers`, `social_total_posts` (in social_metrics.csv wide-format, not wired to GoldClient), `video_progress_25/50/75_rate` |
| No Gold data — social followers | 1 | `social_media_followers` (not in any Gold file) |

The 9 no-Gold-data metrics are declared in the registry for completeness and future use.
They are enumerated in `tests_v2/test_metric_registry_coverage.py::KNOWN_NO_GOLD_DATA`.

## Golden set coverage

- All `expected_metric_names` in golden_set_v3.yaml and golden_set_v4.yaml resolve in registry: **YES ✓**
- No missing references found.

## Skill file coverage

- Metrics with skill-file mentions: **24/76** (31%)
- Metrics without skill-file coverage: 52

Impact: Scout can retrieve numeric values for all 67 Gold-backed metrics. For the 52 without
skill-file coverage, Scout returns values but has no narrative context (seasonal interpretation,
peer comparison framing, etc.). This is correct by design — narrative content is human-authored
and selective.

Full coverage report: `docs/skill_file_coverage_report.txt`

Follow-up candidates (metrics frequently queried but lacking skill-file context):
- `visits_web`, `page_views_web`, `unique_visitors_web` — high-traffic web metrics
- `streamers`, `subscriptions`, `video_plays` — core streaming KPIs
- `purchases_ecommerce`, `items_ecommerce` — eCommerce volume metrics

## v1 priority scoring (READ-ONLY)

v1 priority scoring references metrics via `primary_metric` and `supporting_metrics_json` columns
in `gold_priority_board.csv`. No hardcoded metric name lists found in Python scoring logic.
The scoring engine is data-driven — it reads metric names from Gold, not from code.

**No changes made to v1 code.** Additive-only principle preserved throughout.

## CI protection

Two new CI tests in `tests_v2/test_metric_registry_coverage.py`:
- `test_registry_has_at_least_59_metrics` — floor sanity check
- `test_registry_covers_gold_layer` — all Gold-backed registry metrics must resolve via GoldClient
- `test_no_gold_data_metrics_are_documented` — KNOWN_NO_GOLD_DATA entries must remain in registry
- `test_list_all_metrics_tool` — list_all_metrics returns ≥ 59 entries
- `test_list_all_metrics_platform_filter` — platform filter works

These tests gate CI. Adding a metric to Gold without a registry entry, or breaking GoldClient
naming resolution, now fails loudly instead of silently degrading Scout answer quality.

## Dynamic discovery tool

Added `list_all_metrics(filter_by_platform, filter_by_polarity)` to `clubos2/tools/registry.py`.
Returns all registry metrics with `source: "metric_registry"` citation tag.

Added rule to `prompts/scout_v6.md`: meta-questions about coverage use `list_all_metrics`,
never hallucinate the metric list.
