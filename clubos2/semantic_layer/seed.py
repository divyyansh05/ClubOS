from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from typing import Any

from clubos2.semantic_layer.db import bootstrap_db, get_session
from clubos2.semantic_layer.schema import MetricRegistry

# Top 10 Curated Metrics
CURATED_METRICS: list[dict[str, Any]] = [
    {
        "metric_name": "streaming_daily_users",
        "business_name": "Streaming Daily Active Users",
        "definition": (
            "The average number of unique users who stream content or log "
            "into the streaming platform daily."
        ),
        "platform": "streaming",
        "polarity": "positive",
        "unit": "users",
        "ambiguous_with": "fan_app_dau",
        "disambiguation_rule": (
            "Measures daily active users on the streaming site. For mobile app "
            "daily active users, use fan_app_dau."
        ),
        "seasonal_note": (
            "Holiday seasons and major matchdays usually see peak active " "streaming users."
        ),
        "typical_range": "50,000 - 100,000",
        "valid_query_examples": (
            '["What is the streaming daily active users?", '
            '"Did streaming daily active users grow this month?", '
            '"Compare streaming DAU to last year"]'
        ),
        "invalid_query_examples": '["How many users logged into the fan app?"]',
        "skill_file_path": "packages/rag/skills/peer_benchmark.md",
        "owned_by": "Streaming Product Team",
        "last_reviewed": datetime.now(UTC),
    },
    {
        "metric_name": "conversion_rate_ecommerce",
        "business_name": "eCommerce Conversion Rate",
        "definition": (
            "The percentage of unique visits to the eCommerce store " "that result in a purchase."
        ),
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "%",
        "ambiguous_with": "conversion_rate_streaming",
        "disambiguation_rule": (
            "Measures ecommerce purchase conversions. If conversion rate is "
            "queried without specifying platform, default to ecommerce and "
            "state assumption."
        ),
        "seasonal_note": "November and December usually see significant holiday shopping spikes.",
        "typical_range": "1.5% - 3.5%",
        "valid_query_examples": (
            '["What is the current eCommerce conversion rate?", '
            '"Has conversion rate improved this quarter?", '
            '"How does our conversion rate compare to peer average?"]'
        ),
        "invalid_query_examples": '["What is the conversion rate of our streaming product?"]',
        "skill_file_path": "packages/rag/skills/priority_board.md",
        "owned_by": "eCommerce Analytics Team",
        "last_reviewed": datetime.now(UTC),
    },
    {
        "metric_name": "conversion_rate_streaming",
        "business_name": "Streaming Conversion Rate",
        "definition": (
            "The conversion rate of streaming site visitors who "
            "subscribe to a paid streaming plan."
        ),
        "platform": "streaming",
        "polarity": "positive",
        "unit": "%",
        "ambiguous_with": "conversion_rate_ecommerce",
        "disambiguation_rule": (
            "Specifically measures the conversion rate of streaming site visitors "
            "to subscribers. If the user asks for 'streaming conversion rate' "
            "or 'subscription rate', map to this metric."
        ),
        "seasonal_note": "Peaks during pre-season and major tournament starts.",
        "typical_range": "2.0% - 5.0%",
        "valid_query_examples": (
            '["What is the conversion rate of our streaming product?", '
            '"Is the streaming subscription rate higher this month?", '
            '"Compare streaming conversion rate to masia_fc"]'
        ),
        "invalid_query_examples": '["What is the conversion rate of our ecommerce store?"]',
        "skill_file_path": "packages/rag/skills/peer_benchmark.md",
        "owned_by": "Streaming Product Team",
        "last_reviewed": datetime.now(UTC),
    },
    {
        "metric_name": "net_sales",
        "business_name": "eCommerce Net Sales",
        "definition": (
            "Total sales revenue generated from eCommerce purchases, "
            "net of returns and discounts."
        ),
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "EUR",
        "ambiguous_with": "cart_value",
        "disambiguation_rule": (
            "Represents absolute sales revenue. Do not confuse with cart value "
            "which is average value per transaction."
        ),
        "seasonal_note": "January always dips 15-20% post-holiday — not a crisis.",
        "typical_range": "100,000 EUR - 500,000 EUR",
        "valid_query_examples": (
            '["What is our ecommerce net sales?", '
            '"Did sales dip in January?", '
            '"Show net sales trend for eCommerce"]'
        ),
        "invalid_query_examples": '["What is the average cart value of a purchase?"]',
        "skill_file_path": "packages/rag/skills/priority_board.md",
        "owned_by": "eCommerce Commercial Team",
        "last_reviewed": datetime.now(UTC),
    },
    {
        "metric_name": "unique_visitors_web",
        "business_name": "Web Unique Visitors",
        "definition": (
            "The number of distinct individual users visiting the main "
            "club website during the reporting month."
        ),
        "platform": "web",
        "polarity": "positive",
        "unit": "users",
        "ambiguous_with": (
            "unique_visitors_ecommerce," "unique_visitors_streaming," "unique_visitors_fan_app"
        ),
        "disambiguation_rule": (
            "Refers to unique visitors of the main website only. If platform is "
            "unspecified and context suggests general web traffic, default to main website."
        ),
        "seasonal_note": "Fluctuates with match calendars, transfer news, and pre-season activity.",
        "typical_range": "1,000,000 - 3,000,000",
        "valid_query_examples": (
            '["How many unique visitors visited the website?", '
            '"Show website unique visitors trend", '
            '"Compare web visitors to peer average"]'
        ),
        "invalid_query_examples": '["How many unique visitors did the fan app have?"]',
        "skill_file_path": "packages/rag/skills/peer_benchmark.md",
        "owned_by": "Digital Media Team",
        "last_reviewed": datetime.now(UTC),
    },
    {
        "metric_name": "post_match_engagement_rate",
        "business_name": "Post-Match Fan Engagement Rate",
        "definition": (
            "The engagement rate on social media posts published " "immediately following matches."
        ),
        "platform": "social",
        "polarity": "positive",
        "unit": "%",
        "ambiguous_with": "reels_engagement_rate",
        "disambiguation_rule": (
            "Applies to post-match context only. If generic engagement is queried, "
            "distinguish from video-specific metrics."
        ),
        "seasonal_note": "Significantly higher during championship runs and post-derby wins.",
        "typical_range": "3.0% - 8.0%",
        "valid_query_examples": (
            '["What is the post-match engagement rate?", '
            '"Does post-match engagement drop after losses?", '
            '"Compare post-match engagement with peers"]'
        ),
        "invalid_query_examples": '["What is the engagement rate on our reels?"]',
        "skill_file_path": "packages/rag/skills/social_intelligence.md",
        "owned_by": "Social Media Team",
        "last_reviewed": datetime.now(UTC),
    },
    {
        "metric_name": "reels_engagement_rate",
        "business_name": "Instagram Reels Engagement Rate",
        "definition": "The average engagement rate specifically for Instagram Reels content.",
        "platform": "social",
        "polarity": "positive",
        "unit": "%",
        "ambiguous_with": "post_match_engagement_rate",
        "disambiguation_rule": (
            "Measures short-form video engagement on Instagram specifically. "
            "Do not confuse with overall social engagement rate."
        ),
        "seasonal_note": "Higher during summer breaks and player transfer announcements.",
        "typical_range": "5.0% - 15.0%",
        "valid_query_examples": (
            '["What is our reels engagement rate?", '
            '"Are reels outperforming standard posts?", '
            '"Show reels engagement rate by month"]'
        ),
        "invalid_query_examples": '["What is the overall engagement rate on Twitter?"]',
        "skill_file_path": "packages/rag/skills/social_intelligence.md",
        "owned_by": "Social Media Team",
        "last_reviewed": datetime.now(UTC),
    },
    {
        "metric_name": "fan_app_dau",
        "business_name": "Fan App Daily Active Users",
        "definition": (
            "The average number of unique users active on the fan app "
            "on matchdays or general days."
        ),
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "users",
        "ambiguous_with": "streaming_daily_users",
        "disambiguation_rule": (
            "Measures unique active users on the mobile fan app. "
            "Distinguish from streaming daily active users."
        ),
        "seasonal_note": "Matchdays see massive spikes, sometimes 5-10x the daily average.",
        "typical_range": "30,000 - 80,000",
        "valid_query_examples": (
            '["What is the fan app DAU?", '
            '"Show fan app active users on matchdays", '
            '"Compare fan app DAU to streaming DAU"]'
        ),
        "invalid_query_examples": '["How many users stream daily on the web?"]',
        "skill_file_path": "packages/rag/skills/command_center.md",
        "owned_by": "Fan App Product Team",
        "last_reviewed": datetime.now(UTC),
    },
    {
        "metric_name": "social_total_posts",
        "business_name": "Social Total Posts",
        "definition": (
            "The total number of posts published across all official "
            "social media channels during the month."
        ),
        "platform": "social",
        "polarity": "positive",
        "unit": "count",
        "ambiguous_with": "posting_frequency_per_day",
        "disambiguation_rule": (
            "Measures total volume of posts rather than daily frequency. "
            "Neutral polarity in analysis, but stored as positive for DB check."
        ),
        "seasonal_note": "Increases during active match periods and transfer windows.",
        "typical_range": "500 - 1,500",
        "valid_query_examples": (
            '["How many posts did we publish this month?", '
            '"Is posting volume higher than last season?", '
            '"Show total posts across social channels"]'
        ),
        "invalid_query_examples": '["What is our average daily posting frequency?"]',
        "skill_file_path": "packages/rag/skills/social_intelligence.md",
        "owned_by": "Social Content Team",
        "last_reviewed": datetime.now(UTC),
    },
    {
        "metric_name": "bounce_rate_web",
        "business_name": "Web Bounce Rate",
        "definition": (
            "The percentage of visitors to the main club website who "
            "navigate away after viewing only one page."
        ),
        "platform": "web",
        "polarity": "negative",
        "unit": "%",
        "ambiguous_with": "recurrence_web",
        "disambiguation_rule": (
            "Negative polarity: lower bounce rate is better. "
            "Specifically measures single-page sessions on the main website."
        ),
        "seasonal_note": (
            "Usually stable, but can rise if traffic spikes on simple " "news landing pages."
        ),
        "typical_range": "35.0% - 55.0%",
        "valid_query_examples": (
            '["What is our website bounce rate?", '
            '"Did web bounce rate improve this month?", '
            '"Compare bounce rate with competitor median"]'
        ),
        "invalid_query_examples": '["What is the recurrence rate on the website?"]',
        "skill_file_path": "packages/rag/skills/peer_benchmark.md",
        "owned_by": "Digital Media Team",
        "last_reviewed": datetime.now(UTC),
    },
]

# Remaining 49 metrics with basic one-line business definitions
STUB_METRICS: list[dict[str, Any]] = [
    # Web (12)
    {
        "metric_name": "visits_web",
        "business_name": "Web Visits",
        "definition": "Total number of sessions initiated on the main website.",
        "platform": "web",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "page_views_web",
        "business_name": "Web Page Views",
        "definition": "Total number of web pages loaded or refreshed.",
        "platform": "web",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "international_visits_web",
        "business_name": "Web International Visits",
        "definition": "Number of website sessions originating outside the home country.",
        "platform": "web",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "mobile_visits_web",
        "business_name": "Web Mobile Visits",
        "definition": "Number of website sessions initiated from mobile devices.",
        "platform": "web",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "search_organic_visits_web",
        "business_name": "Web Organic Search Visits",
        "definition": "Website sessions initiated via search engines without ad clicks.",
        "platform": "web",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "social_organic_visits_web",
        "business_name": "Web Organic Social Visits",
        "definition": "Website sessions initiated via organic social media links.",
        "platform": "web",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "marketing_visits_web",
        "business_name": "Web Marketing Visits",
        "definition": "Website sessions driven by paid marketing campaigns.",
        "platform": "web",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "other_channels_visits_web",
        "business_name": "Web Other Channels Visits",
        "definition": "Website sessions initiated from miscellaneous traffic channels.",
        "platform": "web",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "consumption_web",
        "business_name": "Web Consumption Rate",
        "definition": "Metric reflecting pages per session and stay duration.",
        "platform": "web",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "recurrence_web",
        "business_name": "Web Recurrence Rate",
        "definition": "Percentage of returning unique visitors to the website.",
        "platform": "web",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "new_users_web",
        "business_name": "Web New Users",
        "definition": "Count of first-time unique visitors to the website.",
        "platform": "web",
        "polarity": "positive",
        "unit": "users",
    },
    {
        "metric_name": "logged_users_web",
        "business_name": "Web Logged Users",
        "definition": "Count of logged-in unique visitors on the website.",
        "platform": "web",
        "polarity": "positive",
        "unit": "users",
    },
    # eCommerce (10)
    {
        "metric_name": "purchases_ecommerce",
        "business_name": "eCommerce Purchases",
        "definition": "Total count of completed checkout transactions.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "items_ecommerce",
        "business_name": "eCommerce Items Purchased",
        "definition": "Total number of individual items purchased across transactions.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "search_organic_purchases",
        "business_name": "eCommerce Organic Search Purchases",
        "definition": "Completed purchases driven by organic search traffic.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "social_organic_purchases",
        "business_name": "eCommerce Organic Social Purchases",
        "definition": "Completed purchases driven by organic social media traffic.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "marketing_purchases",
        "business_name": "eCommerce Marketing Purchases",
        "definition": "Completed purchases driven by paid marketing campaigns.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "other_channels_purchases",
        "business_name": "eCommerce Other Purchases",
        "definition": "Purchases driven by miscellaneous or direct traffic channels.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "cart_value",
        "business_name": "eCommerce Cart Value",
        "definition": "Average monetary value per shopping cart transaction.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "EUR",
    },
    {
        "metric_name": "product_views_rate",
        "business_name": "eCommerce Product Views Rate",
        "definition": "Percentage of store visits that include viewing a product.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "card_addition_rate",
        "business_name": "eCommerce Add to Cart Rate",
        "definition": "Percentage of store visits where items are added to the cart.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "checkout_rate",
        "business_name": "eCommerce Checkout Initiation Rate",
        "definition": "Percentage of store visits that reach checkout.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "%",
    },
    # Streaming (14)
    {
        "metric_name": "video_plays",
        "business_name": "Streaming Video Plays",
        "definition": "Total number of video streaming sessions started.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "streamers",
        "business_name": "Streaming Active Streamers",
        "definition": "Count of unique users who streamed at least one video.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "users",
    },
    {
        "metric_name": "subscriptions",
        "business_name": "Streaming Active Subscriptions",
        "definition": "Total count of active paid streaming subscribers.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "search_organic_plays",
        "business_name": "Streaming Organic Search Plays",
        "definition": "Video plays initiated via organic search engine referrals.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "social_organic_plays",
        "business_name": "Streaming Organic Social Plays",
        "definition": "Video plays initiated via organic social media links.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "marketing_plays",
        "business_name": "Streaming Marketing Plays",
        "definition": "Video plays driven by paid marketing campaigns.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "other_traffic_plays",
        "business_name": "Streaming Other Plays",
        "definition": "Video plays driven by miscellaneous or direct traffic.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "streamers_rate",
        "business_name": "Streaming Active Streamer Ratio",
        "definition": "Ratio of unique streamers to total streaming site visitors.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "video_recurrence",
        "business_name": "Streaming Video Recurrence",
        "definition": "Average recurrence of video streams per unique streamer.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "video_play_rate",
        "business_name": "Streaming Video Play Rate",
        "definition": "Average play time or streams per active visitor.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "video_progress_25_rate",
        "business_name": "Streaming Video 25% Completion Rate",
        "definition": "Percentage of streams reaching 25% progress.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "video_progress_50_rate",
        "business_name": "Streaming Video 50% Completion Rate",
        "definition": "Percentage of streams reaching 50% progress.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "video_progress_75_rate",
        "business_name": "Streaming Video 75% Completion Rate",
        "definition": "Percentage of streams reaching 75% progress.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "video_complete_rate",
        "business_name": "Streaming Video Completion Rate",
        "definition": "Percentage of streams played to the end.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "%",
    },
    # Fan App (9)
    {
        "metric_name": "app_downloads",
        "business_name": "Fan App Downloads",
        "definition": "Total number of app install events during the month.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "matchday_visits",
        "business_name": "Fan App Matchday Visits",
        "definition": "Total visits recorded on the app on matchdays.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "pct_android",
        "business_name": "Fan App Android Share",
        "definition": "Percentage of app sessions originating from Android devices.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "organic_launch_visits",
        "business_name": "Fan App Organic Launches",
        "definition": "App sessions initiated organically by opening the app directly.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "app_push_visits",
        "business_name": "Fan App Push Visits",
        "definition": "App sessions initiated by tapping push notifications.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "deeplink_visits",
        "business_name": "Fan App Deeplink Visits",
        "definition": "App sessions initiated via deep-linking URLs.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "other_channel_visits",
        "business_name": "Fan App Other Visits",
        "definition": "App sessions initiated via miscellaneous external channels.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "session_time_avg",
        "business_name": "Fan App Average Session Time",
        "definition": "The average duration of a user session in the app.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "seconds",
    },
    {
        "metric_name": "heavy_users",
        "business_name": "Fan App Heavy Users",
        "definition": "Count of power users exceeding baseline activity thresholds.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "users",
    },
    # Social (7)
    {
        "metric_name": "social_media_followers",
        "business_name": "Social Media Total Followers",
        "definition": "Total count of followers across all official social media channels.",
        "platform": "social",
        "polarity": "positive",
        "unit": "count",
    },
    # Matchday / Revenue (2)
    {
        "metric_name": "matchday_ticket_revenue",
        "business_name": "Matchday Ticket Revenue",
        "definition": "Total revenue generated from matchday ticket sales, including season tickets and single-match purchases.",
        "platform": "matchday",
        "polarity": "positive",
        "unit": "EUR",
    },
    {
        "metric_name": "digital_merchandise_revenue",
        "business_name": "Digital Merchandise Revenue",
        "definition": "Total revenue from digital merchandise sales including licensed digital products and NFTs.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "EUR",
    },
    {
        "metric_name": "total_engagement",
        "business_name": "Social Total Engagement",
        "definition": "Combined total of engagement actions across all social channels.",
        "platform": "social",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "avg_engagement_per_post",
        "business_name": "Social Avg Engagement",
        "definition": "Average engagement actions received per published post.",
        "platform": "social",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "international_engagement_ratio",
        "business_name": "Social International Ratio",
        "definition": "Ratio of non-domestic engagement to total engagement.",
        "platform": "social",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "total_estimated_views",
        "business_name": "Social Total Estimated Views",
        "definition": "Combined estimated video views across all social platforms.",
        "platform": "social",
        "polarity": "positive",
        "unit": "count",
    },
    # Metrics present in Gold layer that were absent from registry (discovered 2026-07-10)
    {
        "metric_name": "streaming_subscription_rate",
        "business_name": "Streaming Subscription Rate",
        "definition": "Percentage of streaming site visitors who convert to a paid subscription in the month.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "%",
        "ambiguous_with": "conversion_rate_streaming",
        "disambiguation_rule": (
            "Raw subscription conversion rate from Gold (streaming asset, subscription_rate column). "
            "conversion_rate_streaming is the registry alias; streaming_subscription_rate is the Gold compound name. "
            "Both refer to the same underlying metric."
        ),
    },
    {
        "metric_name": "social_media_instagram_engagement_rate",
        "business_name": "Instagram Engagement Rate",
        "definition": "Engagement rate on the club's official Instagram channel, measured as engagements divided by reach.",
        "platform": "social",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "social_media_posting_frequency_per_day",
        "business_name": "Social Posting Frequency",
        "definition": "Average number of posts published per day across all official social media channels.",
        "platform": "social",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "fan_app_user_rating",
        "business_name": "Fan App Store Rating",
        "definition": "Average user rating of the fan app in app stores (iOS App Store and Google Play), on a 1-5 scale.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "ratio",
    },
    {
        "metric_name": "streaming_unique_visitors",
        "business_name": "Streaming Unique Visitors",
        "definition": "Number of distinct users who visited the streaming platform at least once during the month.",
        "platform": "streaming",
        "polarity": "positive",
        "unit": "users",
    },
    {
        "metric_name": "ecommerce_unique_visitors",
        "business_name": "eCommerce Unique Visitors",
        "definition": "Number of distinct users who visited the eCommerce store at least once during the month.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "users",
    },
    {
        "metric_name": "ecommerce_visits",
        "business_name": "eCommerce Visits",
        "definition": "Total number of sessions initiated on the eCommerce store.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "ecommerce_recurrence",
        "business_name": "eCommerce Recurrence Rate",
        "definition": "Percentage of returning unique visitors to the eCommerce store.",
        "platform": "ecommerce",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "fan_app_recurrence",
        "business_name": "Fan App Recurrence Rate",
        "definition": "Percentage of returning unique users on the fan app.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "%",
    },
    {
        "metric_name": "fan_app_unique_visitors",
        "business_name": "Fan App Unique Visitors",
        "definition": "Number of distinct users who opened the fan app at least once during the month.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "users",
    },
    {
        "metric_name": "fan_app_visits",
        "business_name": "Fan App Total Visits",
        "definition": "Total number of app sessions on the fan app during the month.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "count",
    },
    {
        "metric_name": "fan_app_logged_users",
        "business_name": "Fan App Logged-In Users",
        "definition": "Count of logged-in unique users on the fan app during the month.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "users",
    },
    {
        "metric_name": "fan_app_new_users",
        "business_name": "Fan App New Users",
        "definition": "Count of first-time unique users on the fan app during the month.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "users",
    },
    {
        "metric_name": "fan_app_marketing_visits",
        "business_name": "Fan App Marketing Visits",
        "definition": "Fan app sessions driven by paid marketing campaigns or push-promotion links.",
        "platform": "fan_app",
        "polarity": "positive",
        "unit": "count",
    },
]

ALL_METRICS = CURATED_METRICS + STUB_METRICS


def run_seed(dry_run: bool = False, database_url: str | None = None) -> int:
    """Executes the seeding process to populate the metric_registry table.

    Returns the count of metrics inserted or updated.
    """
    if not dry_run:
        bootstrap_db(database_url)

    count = 0
    with get_session(database_url) as session:
        for metric_def in ALL_METRICS:
            # Query if metric already exists
            existing = (
                session.query(MetricRegistry)
                .filter(MetricRegistry.metric_name == metric_def["metric_name"])
                .first()
            )

            if existing:
                if not dry_run:
                    existing.business_name = metric_def["business_name"]
                    existing.definition = metric_def["definition"]
                    existing.platform = metric_def["platform"]
                    existing.polarity = metric_def["polarity"]
                    existing.unit = metric_def.get("unit")
                    existing.ambiguous_with = metric_def.get("ambiguous_with")
                    existing.disambiguation_rule = metric_def.get("disambiguation_rule")
                    existing.seasonal_note = metric_def.get("seasonal_note")
                    existing.typical_range = metric_def.get("typical_range")
                    existing.valid_query_examples = metric_def.get("valid_query_examples")
                    existing.invalid_query_examples = metric_def.get("invalid_query_examples")
                    existing.skill_file_path = metric_def.get("skill_file_path")
                    existing.owned_by = metric_def.get("owned_by")
                    existing.last_reviewed = metric_def.get("last_reviewed")
                    existing.updated_at = datetime.now(UTC)
            else:
                if not dry_run:
                    new_metric = MetricRegistry(
                        metric_name=metric_def["metric_name"],
                        business_name=metric_def["business_name"],
                        definition=metric_def["definition"],
                        platform=metric_def["platform"],
                        polarity=metric_def["polarity"],
                        unit=metric_def.get("unit"),
                        ambiguous_with=metric_def.get("ambiguous_with"),
                        disambiguation_rule=metric_def.get("disambiguation_rule"),
                        seasonal_note=metric_def.get("seasonal_note"),
                        typical_range=metric_def.get("typical_range"),
                        valid_query_examples=metric_def.get("valid_query_examples"),
                        invalid_query_examples=metric_def.get("invalid_query_examples"),
                        skill_file_path=metric_def.get("skill_file_path"),
                        owned_by=metric_def.get("owned_by"),
                        last_reviewed=metric_def.get("last_reviewed"),
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    )
                    session.add(new_metric)

            count += 1
            if dry_run:
                print(
                    f"[DRY-RUN] Metric: {metric_def['metric_name']} "
                    f"({metric_def['business_name']}) "
                    f"Platform: {metric_def['platform']} "
                    f"Polarity: {metric_def['polarity']}"
                )

        if not dry_run:
            session.commit()

    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the metric_registry table.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the metrics that would be seeded without writing to the database.",
    )
    args = parser.parse_args()

    try:
        count = run_seed(dry_run=args.dry_run)
        mode = "Dry-run completed. Found" if args.dry_run else "Successfully seeded"
        print(f"{mode} {count} rows.")
    except Exception as e:
        print(f"Error seeding database: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
