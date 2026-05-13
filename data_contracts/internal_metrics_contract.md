# Internal Metrics Data Contract

## Purpose

Define the expected structure of the recurring internal workbook for ClubOS.

## Source File

- `data/source/GroupE.pack.english/Tema5.data_visualization.dataset/Tema5.internal_metrics.dataset.xlsx`

## Expected Sheets

- `Info`
- `Main_Website`
- `eCommerce`
- `Streaming_Website`
- `Fan_App`

## Grain

- monthly
- one row per asset per month

## Required Common Columns

- `month`
- `digital_active`
- `active_type`

## Sheet-Specific Required Columns

### Main_Website

- `unique_visitors`
- `visits`
- `page_views`
- `international_visits`
- `mobile_visits`
- `search_organic_visits`
- `social_organic_visits`
- `marketing_visits`
- `other_channels_visits`
- `consumption`
- `bounce_rate`
- `recurrence`
- `new_users`
- `logged_users`

### eCommerce

- `unique_visitors`
- `visits`
- `purchases`
- `items`
- `net_sales`
- `search_organic_purchases`
- `social_organic_purchases`
- `marketing_purchases`
- `other_channels_purchases`
- `cart_value`
- `product_views_rate`
- `card_addition_rate`
- `checkout_rate`
- `conversion_rate`
- `recurrence`

### Streaming_Website

- `unique_visitors`
- `daily_users`
- `video_plays`
- `streamers`
- `subscriptions`
- `search_organic_plays`
- `social_organic_plays`
- `marketing_plays`
- `otherl_traffic_plays` (typo in source)
- `subscription_rate`
- `streamers_rate`
- `video_recurrence`
- `video_play_rate`
- `video_progress_25_rate`
- `video_progress_50_rate`
- `video_progress_75_rate`
- `video_complete_rate`

### Fan_App

- `unique_visitors`
- `visits`
- `app_downloads`
- `matchday_visits`
- `%android` (bad character in source)
- `organic_launch_visits`
- `app_push_visits`
- `deeplink_visits`
- `marketing_visits`
- `other_channel_visits`
- `recurrence`
- `session_time_avg`
- `new_users`
- `logged_users`
- `heavy_users`
- `user_rating`

## Validation Rules

- `month` must parse to a valid month-start date
- no duplicate rows per asset and month
- rate fields should generally be within 0 to 1 unless explicitly ratio-like
- numeric metrics should not be unexpectedly null

## Notes

- The Silver normalize process should map `%android` to `pct_android` and `otherl_traffic_plays` to `other_traffic_plays` or standard fallback.
- Not all columns are used by the product MVP, but the Bronze layer will ingest them completely.
