# Benchmark Data Contract

## Purpose

Define the expected structure of the recurring peer benchmark workbook for ClubOS.

## Source File

- `data/source/GroupE.pack.english/Tema5.data_visualization.dataset/Tema5.benchmark.dataset.xlsx`

## Expected Sheets

- `Info`
- `Main_Website`
- `eCommerce`
- `Streaming`
- `Fan_App`

## Grain

- monthly
- one row per club per asset per month

## Required Common Columns

- `month`
- `digital_active`
- `club`
- `active_type`

## Supported Benchmark Metrics

### Main_Website

- `unique_visitors`
- `visits`
- `bounce_rate`
- `recurrence`

### eCommerce

- `unique_visitors`
- `visits`
- `conversion_rate`
- `cart_value`

### Streaming

- `unique_visitors`
- `daily_users`
- `streamers_rate`
- `video_play_rate`

### Fan_App

- `unique_visitors`
- `visits`
- `matchday_visits`
- `app_downloads`
- `recurrence`
- `heavy_users`
- `user_rating`

## Validation Rules

- every supported club should have one row per month
- benchmark comparisons must use only supported metrics
- source inconsistencies like the Streaming sheet bug (where `digital_active` = `main_website` but `active_type` = `streaming`) must be detected and normalized to `streaming` in Silver.

## Important Product Rule

If a metric is not supported in this contract, the product must not present it as benchmarked.
