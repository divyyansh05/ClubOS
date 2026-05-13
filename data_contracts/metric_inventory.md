# Metric Inventory

This inventory documents all metrics available in the internal source file, whether they are supported by peer benchmarking, and if they are required for the MVP scope.

| Asset | Metric Name | Source File | Benchmark Available | Product Module Usage | MVP | Notes / Caveats |
|---|---|---|---|---|---|---|
| Main_Website | unique_visitors | Internal | Yes | Command Center, Peer Benchmark | Yes | Core volume MVP metric. |
| Main_Website | visits | Internal | Yes | Command Center, Peer Benchmark | Yes | Core volume MVP metric. |
| Main_Website | page_views | Internal | No | None | No | Not benchmarked. |
| Main_Website | international_visits | Internal | No | None | No | Geographic drill-down not in MVP. |
| Main_Website | mobile_visits | Internal | No | None | No | Device split not in MVP. |
| Main_Website | search_organic_visits | Internal | No | None | No | Traffic source drill-down. |
| Main_Website | social_organic_visits | Internal | No | None | No | Traffic source drill-down. |
| Main_Website | marketing_visits | Internal | No | None | No | Traffic source drill-down. |
| Main_Website | other_channels_visits | Internal | No | None | No | Traffic source drill-down. |
| Main_Website | consumption | Internal | No | None | No | Wait for clearer business definition. |
| Main_Website | bounce_rate | Internal | Yes | Command Center, Peer Benchmark | Yes | Core quality MVP metric. |
| Main_Website | recurrence | Internal | Yes | Command Center, Peer Benchmark | Yes | Core loyalty MVP metric. |
| Main_Website | new_users | Internal | No | None | No | |
| Main_Website | logged_users | Internal | No | None | No | |
| eCommerce | unique_visitors | Internal | Yes | Peer Benchmark | No | Benchmarked but not an explicitly requested MVP KPI per spec. |
| eCommerce | visits | Internal | Yes | Peer Benchmark | No | Benchmarked but not explicitly in MVP KPI list. |
| eCommerce | purchases | Internal | No | None | No | |
| eCommerce | items | Internal | No | None | No | |
| eCommerce | net_sales | Internal | No | Command Center | Yes | Primary commercial metric. Absolute revenue not available for peers. |
| eCommerce | search_organic_purchases | Internal | No | None | No | |
| eCommerce | social_organic_purchases | Internal | No | None | No | |
| eCommerce | marketing_purchases | Internal | No | None | No | |
| eCommerce | other_channels_purchases | Internal | No | None | No | |
| eCommerce | cart_value | Internal | Yes | Command Center, Peer Benchmark | Yes | Core eCommerce MVP metric. |
| eCommerce | product_views_rate | Internal | No | None | No | |
| eCommerce | card_addition_rate | Internal | No | None | No | |
| eCommerce | checkout_rate | Internal | No | Command Center | Yes | Conversion funnel MVP metric. Not available in benchmark. |
| eCommerce | conversion_rate | Internal | Yes | Command Center, Peer Benchmark | Yes | Core eCommerce MVP metric. |
| eCommerce | recurrence | Internal | No | None | No | |
| Streaming | unique_visitors | Internal | Yes | Peer Benchmark | No | Benchmarked but not MVP KPI. |
| Streaming | daily_users | Internal | Yes | Peer Benchmark | No | Benchmarked but not MVP KPI. |
| Streaming | video_plays | Internal | No | None | No | |
| Streaming | streamers | Internal | No | None | No | |
| Streaming | subscriptions | Internal | No | Command Center | Yes | Core volume MVP metric. Not available in benchmark. |
| Streaming | search_organic_plays | Internal | No | None | No | |
| Streaming | social_organic_plays | Internal | No | None | No | |
| Streaming | marketing_plays | Internal | No | None | No | |
| Streaming | otherl_traffic_plays | Internal | No | None | No | Typo in source file; map to 'other_traffic_plays' in Silver. |
| Streaming | subscription_rate | Internal | No | Command Center | Yes | Core conversion MVP metric. Not available in benchmark. |
| Streaming | streamers_rate | Internal | Yes | Command Center, Peer Benchmark | Yes | Core engagement MVP metric. |
| Streaming | video_recurrence | Internal | No | None | No | |
| Streaming | video_play_rate | Internal | Yes | Command Center, Peer Benchmark | Yes | Core engagement MVP metric. |
| Streaming | video_progress_25_rate | Internal | No | None | No | |
| Streaming | video_progress_50_rate | Internal | No | None | No | |
| Streaming | video_progress_75_rate | Internal | No | None | No | |
| Streaming | video_complete_rate | Internal | No | None | No | |
| Fan_App | unique_visitors | Internal | Yes | Peer Benchmark | No | Benchmarked but not MVP KPI. |
| Fan_App | visits | Internal | Yes | Peer Benchmark | No | Benchmarked but not MVP KPI. |
| Fan_App | app_downloads | Internal | Yes | Command Center, Peer Benchmark | Yes | Core volume MVP metric. |
| Fan_App | matchday_visits | Internal | Yes | Command Center, Peer Benchmark | Yes | Core engagement MVP metric. |
| Fan_App | %android | Internal | No | None | No | Inconsistent naming in source; map to 'pct_android' in Silver. |
| Fan_App | organic_launch_visits | Internal | No | None | No | |
| Fan_App | app_push_visits | Internal | No | None | No | |
| Fan_App | deeplink_visits | Internal | No | None | No | |
| Fan_App | marketing_visits | Internal | No | None | No | |
| Fan_App | other_channel_visits | Internal | No | None | No | |
| Fan_App | recurrence | Internal | Yes | Command Center, Peer Benchmark | Yes | Core loyalty MVP metric. |
| Fan_App | session_time_avg | Internal | No | None | No | |
| Fan_App | new_users | Internal | No | None | No | |
| Fan_App | logged_users | Internal | No | None | No | |
| Fan_App | heavy_users | Internal | Yes | Command Center, Peer Benchmark | Yes | Core MVP metric. |
| Fan_App | user_rating | Internal | Yes | None | No | Benchmarked, but not in MVP KPI set. |
