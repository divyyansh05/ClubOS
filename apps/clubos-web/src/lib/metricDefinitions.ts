export interface MetricDefinition {
  label: string;
  definition: string;
  formula?: string;
  polarity: 1 | -1 | 0;
  polarityLabel: string;
  example: string;
  benchmarked: boolean;
  asset: string;
  commercialImpact: string;
}

export const METRIC_DEFINITIONS: Record<string, MetricDefinition> = {
  // Main Website Metrics
  unique_visitors: {
    label: "Unique Visitors",
    definition: "The number of distinct individuals who visited the website at least once during the month, counted once regardless of how many times they returned.",
    formula: "COUNT(DISTINCT user_id WHERE visit_date IN month)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "If 150,000 unique visitors accessed realmadrid.com in January, this is the top-of-funnel metric showing total audience reach.",
    benchmarked: true,
    asset: "main_website",
    commercialImpact: "The primary driver of all downstream conversions - more visitors means more potential customers, content consumers, and brand engagement."
  },

  visits: {
    label: "Visits",
    definition: "The total number of browsing sessions on the website, where a session ends after 30 minutes of inactivity. One person can generate multiple visits.",
    formula: "COUNT(session_id WHERE session_start IN month)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "If 150,000 unique visitors generated 640,000 visits, the average visitor returned 4.3 times during the month.",
    benchmarked: true,
    asset: "main_website",
    commercialImpact: "Measures engagement intensity - higher visit counts relative to unique visitors indicates strong content pull and repeat interest."
  },

  page_views: {
    label: "Page Views",
    definition: "The total number of pages loaded across all visits. Each time a page is loaded or reloaded, it counts as one page view.",
    formula: "COUNT(page_load_event WHERE timestamp IN month)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "If 640,000 visits generated 3.2 million page views, visitors viewed an average of 5 pages per visit.",
    benchmarked: false,
    asset: "main_website",
    commercialImpact: "Indicates depth of engagement - more page views per visit means users are exploring content rather than bouncing immediately."
  },

  international_visits: {
    label: "International Visits",
    definition: "The proportion of website visits originating from IP addresses outside Spain, expressed as a decimal between 0 and 1.",
    formula: "(visits WHERE country != 'Spain') / total_visits",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.65 means 65% of website traffic comes from outside Spain, indicating strong global brand reach.",
    benchmarked: false,
    asset: "main_website",
    commercialImpact: "Measures global brand penetration - higher international traffic indicates successful expansion beyond domestic market and global fanbase growth."
  },

  mobile_visits: {
    label: "Mobile Visits",
    definition: "The proportion of website visits from mobile devices (smartphones and tablets) rather than desktop computers.",
    formula: "(visits WHERE device_type IN ('mobile', 'tablet')) / total_visits",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.72 means 72% of traffic is mobile, reflecting modern browsing habits and mobile-first content consumption.",
    benchmarked: false,
    asset: "main_website",
    commercialImpact: "Critical for user experience optimization - mobile traffic dominance requires mobile-optimized design and fast load times to prevent bounce."
  },

  search_organic_visits: {
    label: "Search Organic Visits",
    definition: "The proportion of visits that arrived via unpaid search engine results (Google, Bing, etc.) rather than paid ads or direct navigation.",
    formula: "(visits WHERE traffic_source = 'organic_search') / total_visits",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.42 means 42% of traffic comes from organic search, indicating strong SEO performance and brand discoverability.",
    benchmarked: false,
    asset: "main_website",
    commercialImpact: "Free, high-intent traffic with no acquisition cost - improvements in organic search drive sustainable long-term traffic growth."
  },

  social_organic_visits: {
    label: "Social Organic Visits",
    definition: "The proportion of visits that arrived via unpaid social media referrals (Facebook, Twitter, Instagram, etc.) rather than paid social ads.",
    formula: "(visits WHERE traffic_source = 'organic_social') / total_visits",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.18 means 18% of traffic comes from organic social, showing viral content spread and fan engagement on social platforms.",
    benchmarked: false,
    asset: "main_website",
    commercialImpact: "Reflects brand virality and social community strength - high organic social traffic indicates content is being shared naturally without paid promotion."
  },

  marketing_visits: {
    label: "Marketing Visits",
    definition: "The proportion of visits that arrived via paid marketing campaigns including display ads, paid search, and paid social media.",
    formula: "(visits WHERE traffic_source LIKE '%paid%') / total_visits",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.25 means 25% of traffic is driven by paid marketing, showing effectiveness of advertising spend.",
    benchmarked: false,
    asset: "main_website",
    commercialImpact: "Measures marketing efficiency - high marketing traffic relative to spend indicates strong ROI on advertising campaigns."
  },

  other_channels_visits: {
    label: "Other Channels Visits",
    definition: "The proportion of visits from traffic sources that don't fit other categories, including email campaigns, affiliates, and referral partners.",
    formula: "(visits WHERE traffic_source NOT IN standard_categories) / total_visits",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.05 means 5% of traffic comes from email newsletters, partner sites, and other miscellaneous sources.",
    benchmarked: false,
    asset: "main_website",
    commercialImpact: "Captures diversification of traffic sources - healthy mix prevents over-dependence on any single channel."
  },

  consumption: {
    label: "Consumption",
    definition: "The average number of pages viewed per visit, measuring depth of content engagement during each session.",
    formula: "SUM(page_views) / COUNT(visits)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 5.2 means the average visitor views 5.2 pages per session, indicating strong content discovery and navigation.",
    benchmarked: false,
    asset: "main_website",
    commercialImpact: "Indicates content stickiness - higher consumption means users find content valuable enough to explore multiple pages rather than leaving immediately."
  },

  bounce_rate: {
    label: "Bounce Rate",
    definition: "The percentage of visits where the user viewed only one page and left without any interaction, indicating immediate exit.",
    formula: "(visits WHERE page_views = 1 AND session_duration < 10s) / total_visits",
    polarity: -1,
    polarityLabel: "Lower is better",
    example: "A bounce rate of 0.42 (42%) means 42% of visitors left after viewing just one page, suggesting content or UX issues.",
    benchmarked: true,
    asset: "main_website",
    commercialImpact: "High bounce rates indicate lost conversion opportunities - reducing bounce rate directly increases the pool of engaged users who might convert."
  },

  recurrence: {
    label: "Recurrence",
    definition: "The average number of visits per unique visitor during the month, measuring how often users return.",
    formula: "COUNT(visits) / COUNT(DISTINCT unique_visitors)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A recurrence of 4.1 means the average visitor returned 4.1 times during the month, showing strong repeat engagement.",
    benchmarked: true,
    asset: "main_website",
    commercialImpact: "Measures brand loyalty and content pull - higher recurrence indicates users find value and return frequently, increasing conversion chances."
  },

  new_users: {
    label: "New Users",
    definition: "The proportion of unique visitors who are visiting the website for the first time, never seen in previous months.",
    formula: "(unique_visitors WHERE first_visit_month = current_month) / total_unique_visitors",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.35 means 35% of this month's visitors are brand new, indicating successful audience expansion and acquisition.",
    benchmarked: false,
    asset: "main_website",
    commercialImpact: "Measures brand growth - consistent new user acquisition is essential for expanding market reach and offsetting natural churn."
  },

  logged_users: {
    label: "Logged Users",
    definition: "The proportion of unique visitors who logged into a user account during their visit, indicating authenticated engagement.",
    formula: "(unique_visitors WHERE logged_in = true) / total_unique_visitors",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.18 means 18% of visitors logged in, showing a subset of highly engaged users willing to create accounts.",
    benchmarked: false,
    asset: "main_website",
    commercialImpact: "Logged-in users provide first-party data, enable personalization, and show higher purchase intent - critical for CRM and retention strategies."
  },

  // eCommerce Metrics
  purchases: {
    label: "Purchases",
    definition: "The total number of completed transactions in the online store during the month, counting each order once.",
    formula: "COUNT(DISTINCT order_id WHERE status = 'completed')",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "If 14,500 purchases were completed in January, this is the total volume of orders processed through the eCommerce platform.",
    benchmarked: false,
    asset: "ecommerce",
    commercialImpact: "Direct revenue driver - more purchases means more revenue, assuming stable average order values."
  },

  items: {
    label: "Items",
    definition: "The total number of individual products sold across all orders, where one order can contain multiple items.",
    formula: "SUM(quantity) FROM order_items WHERE order_status = 'completed'",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "If 14,500 orders contained 23,200 items, the average order had 1.6 items, indicating some cross-selling success.",
    benchmarked: false,
    asset: "ecommerce",
    commercialImpact: "Measures basket size and cross-sell effectiveness - higher items per order increases revenue per transaction without additional acquisition cost."
  },

  net_sales: {
    label: "Net Sales",
    definition: "The total revenue generated from completed orders after deducting returns, refunds, and discounts, expressed in Euros.",
    formula: "SUM(order_total - returns - discounts) WHERE status = 'completed'",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "Net sales of €1,704,370 represents the actual revenue earned from eCommerce after all adjustments.",
    benchmarked: true,
    asset: "ecommerce",
    commercialImpact: "The primary commercial outcome of all digital activity - improvements in net sales directly impact bottom-line revenue."
  },

  search_organic_purchases: {
    label: "Search Organic Purchases",
    definition: "The proportion of eCommerce purchases where the customer's visit originated from unpaid search engine results.",
    formula: "(purchases WHERE last_touch_source = 'organic_search') / total_purchases",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.40 means 40% of store purchases came from visitors who found the site via Google, Bing, or other organic search.",
    benchmarked: false,
    asset: "ecommerce",
    commercialImpact: "Free customer acquisition - high organic search conversion means strong SEO drives direct revenue with no ad spend."
  },

  social_organic_purchases: {
    label: "Social Organic Purchases",
    definition: "The proportion of eCommerce purchases where the customer's visit originated from unpaid social media referrals.",
    formula: "(purchases WHERE last_touch_source = 'organic_social') / total_purchases",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.16 means 16% of purchases came from visitors referred by Facebook, Instagram, or Twitter posts (not ads).",
    benchmarked: false,
    asset: "ecommerce",
    commercialImpact: "Shows social community's commercial value - high organic social purchases indicate engaged fans who buy after seeing content organically."
  },

  marketing_purchases: {
    label: "Marketing Purchases",
    definition: "The proportion of eCommerce purchases where the customer's visit originated from paid marketing campaigns.",
    formula: "(purchases WHERE last_touch_source LIKE '%paid%') / total_purchases",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.41 means 41% of purchases came from paid ads, showing direct ROI on advertising spend.",
    benchmarked: false,
    asset: "ecommerce",
    commercialImpact: "Measures marketing effectiveness - high marketing purchases relative to spend indicates positive ROI on paid acquisition."
  },

  other_channels_purchases: {
    label: "Other Channels Purchases",
    definition: "The proportion of eCommerce purchases from traffic sources outside standard categories (email, affiliates, direct, etc.).",
    formula: "(purchases WHERE last_touch_source NOT IN standard_categories) / total_purchases",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.03 means 3% of purchases came from email campaigns, partner referrals, and other miscellaneous sources.",
    benchmarked: false,
    asset: "ecommerce",
    commercialImpact: "Captures non-standard revenue sources - email and affiliate channels often have high conversion rates with low acquisition cost."
  },

  cart_value: {
    label: "Cart Value",
    definition: "The average monetary value of each completed eCommerce order, calculated as total revenue divided by number of orders.",
    formula: "SUM(net_sales) / COUNT(purchases)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A cart value of €117.26 means the average customer spends €117.26 per order in the online store.",
    benchmarked: true,
    asset: "ecommerce",
    commercialImpact: "Direct multiplier on revenue - increasing average cart value by 10% increases total revenue by 10% without acquiring more customers."
  },

  product_views_rate: {
    label: "Product Views Rate",
    definition: "The proportion of eCommerce visits where the user viewed at least one product detail page.",
    formula: "(visits WHERE product_page_views > 0) / total_ecommerce_visits",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.45 means 45% of store visitors viewed at least one product, indicating browse-to-interest conversion.",
    benchmarked: false,
    asset: "ecommerce",
    commercialImpact: "Top-of-funnel conversion - getting more visitors to view products is the first step toward purchase and drives down-funnel metrics."
  },

  card_addition_rate: {
    label: "Card Addition Rate",
    definition: "The proportion of eCommerce visits where the user added at least one item to their shopping cart.",
    formula: "(visits WHERE cart_additions > 0) / total_ecommerce_visits",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A card addition rate of 0.14 means 14% of store visitors added something to cart, indicating purchase intent.",
    benchmarked: false,
    asset: "ecommerce",
    commercialImpact: "Mid-funnel intent signal - cart additions indicate serious purchase consideration and are a leading indicator of conversion rate."
  },

  checkout_rate: {
    label: "Checkout Rate",
    definition: "The proportion of eCommerce visits where the user initiated the checkout process (entered payment/shipping info).",
    formula: "(visits WHERE checkout_initiated = true) / total_ecommerce_visits",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A checkout rate of 0.069 means 6.9% of visitors started checkout, showing strong purchase intent and funnel progression.",
    benchmarked: false,
    asset: "ecommerce",
    commercialImpact: "Bottom-of-funnel signal - users who reach checkout are very close to purchase, making checkout optimization high-leverage for revenue."
  },

  conversion_rate: {
    label: "Conversion Rate",
    definition: "The percentage of eCommerce visitors who complete a purchase. If 1,000 people visit the store and 13 buy something, conversion rate is 1.3%.",
    formula: "(completed purchases / unique visitors) × 100",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A conversion rate of 1.3% means 13 out of every 1,000 visitors to the online store complete a purchase.",
    benchmarked: true,
    asset: "ecommerce",
    commercialImpact: "The primary multiplier between website traffic and revenue - small improvements drive large revenue gains without additional acquisition cost."
  },

  // Streaming Metrics
  daily_users: {
    label: "Daily Users",
    definition: "The average number of unique individuals who accessed the streaming platform each day during the month.",
    formula: "AVG(COUNT(DISTINCT user_id) per day) over month",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "5,275 daily users means on an average day in the month, 5,275 distinct people watched streaming content.",
    benchmarked: true,
    asset: "streaming",
    commercialImpact: "Measures platform engagement and content pull - higher daily users indicates strong habitual viewership and content quality."
  },

  video_plays: {
    label: "Video Plays",
    definition: "The total number of video playback sessions initiated across all content during the month, counting each start as one play.",
    formula: "COUNT(video_play_event WHERE timestamp IN month)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "47,586 video plays means users pressed play on streaming videos 47,586 times during the month.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Direct measure of content consumption - more plays indicates higher engagement and validates content investment."
  },

  streamers: {
    label: "Streamers",
    definition: "The total number of unique users who watched at least one video on the streaming platform during the month.",
    formula: "COUNT(DISTINCT user_id WHERE video_plays > 0)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "20,040 streamers means 20,040 distinct people watched at least one video this month, showing active viewership base.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Measures active audience size - growing streamer count indicates platform health and content market fit."
  },

  subscriptions: {
    label: "Subscriptions",
    definition: "The total number of users who hold an active paid subscription to the streaming platform at month-end.",
    formula: "COUNT(DISTINCT user_id WHERE subscription_status = 'active' AND billing_date <= month_end)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "6,012 subscriptions means 6,012 users are paying for premium streaming access, generating recurring revenue.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Direct recurring revenue stream - subscription growth directly increases monthly recurring revenue (MRR) and lifetime value (LTV)."
  },

  search_organic_plays: {
    label: "Search Organic Plays",
    definition: "The proportion of video plays that originated from visits arriving via unpaid search engine results.",
    formula: "(plays WHERE visit_source = 'organic_search') / total_plays",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.25 means 25% of video plays came from viewers who found the streaming platform through Google or Bing organic search.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Free viewer acquisition - high organic search plays means strong SEO drives content consumption without paid promotion."
  },

  social_organic_plays: {
    label: "Social Organic Plays",
    definition: "The proportion of video plays that originated from visits arriving via unpaid social media referrals.",
    formula: "(plays WHERE visit_source = 'organic_social') / total_plays",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.38 means 38% of plays came from viewers referred by social media posts (not ads), showing viral content spread.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Shows social content's reach - high organic social plays indicate videos are being shared and discovered organically on social platforms."
  },

  marketing_plays: {
    label: "Marketing Plays",
    definition: "The proportion of video plays that originated from visits arriving via paid marketing campaigns.",
    formula: "(plays WHERE visit_source LIKE '%paid%') / total_plays",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.09 means 9% of plays came from paid advertising, showing direct content consumption ROI from ad spend.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Measures marketing effectiveness for content - high marketing plays relative to spend indicates ads successfully drive viewership."
  },

  other_traffic_plays: {
    label: "Other Traffic Plays",
    definition: "The proportion of video plays from traffic sources outside standard categories (email, affiliates, direct navigation, etc.).",
    formula: "(plays WHERE visit_source NOT IN standard_categories) / total_plays",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.13 means 13% of plays came from email newsletters, partner sites, and other miscellaneous sources.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Captures non-standard viewer acquisition - email and direct traffic often indicate highly engaged repeat viewers."
  },

  subscription_rate: {
    label: "Subscription Rate",
    definition: "The proportion of unique streaming viewers who hold an active paid subscription.",
    formula: "COUNT(subscriptions) / COUNT(streamers)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A subscription rate of 0.039 means 3.9% of viewers are paying subscribers, showing monetization effectiveness.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Monetization efficiency - higher subscription rate means more free viewers convert to paying customers, increasing revenue without acquisition cost."
  },

  streamers_rate: {
    label: "Streamers Rate",
    definition: "The proportion of unique platform visitors who actually watched at least one video, measuring view-through rate.",
    formula: "COUNT(streamers) / COUNT(unique_visitors)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A streamers rate of 0.131 means 13.1% of platform visitors watched at least one video, showing content engagement rate.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Measures content pull - higher rate means visitors are converting to viewers, validating content strategy and platform UX."
  },

  video_recurrence: {
    label: "Video Recurrence",
    definition: "The average number of video plays per unique streamer during the month, measuring viewing intensity.",
    formula: "COUNT(video_plays) / COUNT(streamers)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A recurrence of 2.37 means the average viewer watched 2.37 videos during the month, indicating repeat engagement.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Indicates content stickiness and binge-ability - higher recurrence means viewers return for multiple videos, increasing retention and conversion."
  },

  video_play_rate: {
    label: "Video Play Rate",
    definition: "The proportion of streaming platform visits where at least one video was played, measuring click-to-play conversion.",
    formula: "(visits WHERE video_plays > 0) / total_visits",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A play rate of 0.311 means 31.1% of platform visits resulted in at least one video being played.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Measures content discovery and platform UX - higher rate means visitors easily find and start watching content, reducing bounce."
  },

  video_progress_25_rate: {
    label: "Video Progress 25% Rate",
    definition: "The proportion of started videos where the viewer watched at least 25% of the total duration before stopping or exiting.",
    formula: "(plays WHERE max_progress >= 0.25) / total_plays",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A rate of 0.85 means 85% of viewers who pressed play watched at least the first quarter of the video.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Early engagement signal - high 25% completion indicates content hooks viewers in the opening, reducing early abandonment."
  },

  video_progress_50_rate: {
    label: "Video Progress 50% Rate",
    definition: "The proportion of started videos where the viewer watched at least 50% of the total duration, reaching the midpoint.",
    formula: "(plays WHERE max_progress >= 0.50) / total_plays",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A rate of 0.68 means 68% of viewers reached the video's midpoint, showing sustained engagement.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Mid-content engagement - reaching 50% indicates content holds attention through the middle, a strong quality signal."
  },

  video_progress_75_rate: {
    label: "Video Progress 75% Rate",
    definition: "The proportion of started videos where the viewer watched at least 75% of the total duration, nearing completion.",
    formula: "(plays WHERE max_progress >= 0.75) / total_plays",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A rate of 0.52 means 52% of viewers watched three-quarters of the video, indicating high content value.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Late-stage engagement - high 75% completion shows content delivers value to the end, driving retention and subscription intent."
  },

  video_complete_rate: {
    label: "Video Complete Rate",
    definition: "The proportion of started videos where the viewer watched 100% of the total duration, completing the entire video.",
    formula: "(plays WHERE max_progress >= 1.00) / total_plays",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A complete rate of 0.122 means 12.2% of viewers finished the entire video, showing strong content satisfaction.",
    benchmarked: false,
    asset: "streaming",
    commercialImpact: "Ultimate engagement metric - completion indicates maximum content value delivery and strongly predicts subscription conversion."
  },

  // Fan App Metrics
  app_downloads: {
    label: "App Downloads",
    definition: "The total number of new installations of the fan mobile app during the month across iOS and Android.",
    formula: "COUNT(install_event WHERE timestamp IN month)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "2,145 app downloads means 2,145 users installed the fan app for the first time this month.",
    benchmarked: false,
    asset: "fan_app",
    commercialImpact: "Growing installed base - each download represents a potential long-term engaged fan with direct notification access."
  },

  matchday_visits: {
    label: "Matchday Visits",
    definition: "The number of app sessions that occurred within 3 hours before or after a scheduled match kickoff time.",
    formula: "COUNT(app_session WHERE abs(kickoff_time - session_start) <= 3 hours)",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "156,849 matchday visits means users opened the app 156,849 times around match times, showing live-event engagement.",
    benchmarked: false,
    asset: "fan_app",
    commercialImpact: "Measures live engagement - high matchday usage indicates app is the go-to companion for match experiences, driving retention."
  },

  pct_android: {
    label: "Percent Android",
    definition: "The proportion of app users on Android devices rather than iOS, showing platform mix.",
    formula: "COUNT(users WHERE platform = 'android') / total_users",
    polarity: 0,
    polarityLabel: "Neutral",
    example: "A value of 0.57 means 57% of app users are on Android, 43% on iOS, informing platform investment priorities.",
    benchmarked: false,
    asset: "fan_app",
    commercialImpact: "Platform distribution insight - no direct commercial impact but guides development resource allocation between iOS and Android."
  },

  organic_launch_visits: {
    label: "Organic Launch Visits",
    definition: "The proportion of app sessions started by the user directly opening the app icon, rather than via push notification or deeplink.",
    formula: "(sessions WHERE launch_type = 'organic') / total_sessions",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.68 means 68% of app opens were intentional, showing habitual usage without external prompting.",
    benchmarked: false,
    asset: "fan_app",
    commercialImpact: "Measures organic engagement - high organic launches indicate the app is a habit, reducing dependence on push notifications to drive usage."
  },

  app_push_visits: {
    label: "App Push Visits",
    definition: "The proportion of app sessions started by the user tapping a push notification rather than opening the app directly.",
    formula: "(sessions WHERE launch_type = 'push_notification') / total_sessions",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.10 means 10% of sessions came from push notifications, showing re-engagement campaign effectiveness.",
    benchmarked: false,
    asset: "fan_app",
    commercialImpact: "Measures notification effectiveness - high push visit rate indicates strong notification strategy driving user return and preventing churn."
  },

  deeplink_visits: {
    label: "Deeplink Visits",
    definition: "The proportion of app sessions started by clicking a URL link (email, SMS, web) that opens specific app content.",
    formula: "(sessions WHERE launch_type = 'deeplink') / total_sessions",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.04 means 4% of sessions came from deeplinks in emails or web content, showing cross-channel integration.",
    benchmarked: false,
    asset: "fan_app",
    commercialImpact: "Enables cross-channel journeys - deeplinks allow email and web campaigns to drive app engagement, increasing omnichannel conversion."
  },

  other_channel_visits: {
    label: "Other Channel Visits",
    definition: "The proportion of app sessions from launch methods outside standard categories (widgets, handoff, shortcuts, etc.).",
    formula: "(sessions WHERE launch_type NOT IN standard_categories) / total_sessions",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.18 means 18% of sessions came from widgets, Siri shortcuts, and other miscellaneous app entry points.",
    benchmarked: false,
    asset: "fan_app",
    commercialImpact: "Captures non-standard engagement - widget and shortcut usage indicates power users with high investment in app ecosystem."
  },

  session_time_avg: {
    label: "Average Session Time",
    definition: "The average duration of each app session in minutes, measuring how long users stay engaged per visit.",
    formula: "AVG(session_end_time - session_start_time) in minutes",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "An average session time of 6.8 minutes means users spend nearly 7 minutes in the app each time they open it.",
    benchmarked: false,
    asset: "fan_app",
    commercialImpact: "Indicates app stickiness and content depth - longer sessions mean users find value, increasing retention and monetization opportunities."
  },

  heavy_users: {
    label: "Heavy Users",
    definition: "The proportion of monthly active app users who had 10 or more sessions during the month, indicating power user status.",
    formula: "(users WHERE monthly_sessions >= 10) / total_active_users",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A value of 0.080 means 8% of users are heavy users with 10+ sessions, showing a core engaged segment.",
    benchmarked: true,
    asset: "fan_app",
    commercialImpact: "Identifies most engaged fans - heavy users have highest lifetime value and are prime candidates for premium features and monetization."
  },

  user_rating: {
    label: "User Rating",
    definition: "The average star rating (1 to 5) given by users in app store reviews, reflecting overall satisfaction.",
    formula: "AVG(star_rating) FROM app_store_reviews WHERE review_date IN month",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A user rating of 4.3 out of 5 stars indicates high satisfaction, helping with app store visibility and trust.",
    benchmarked: false,
    asset: "fan_app",
    commercialImpact: "Drives acquisition - higher ratings improve app store ranking and conversion rate, lowering cost per install for new user acquisition."
  },
  // Social Media Metrics
  total_engagement: {
    label: "Total Engagement",
    definition: "Total interactions (likes, comments, shares, etc.) across all social media platforms during the month.",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "1M total engagements indicates a large volume of audience interaction.",
    benchmarked: true,
    asset: "social_media",
    commercialImpact: "Drives top-of-funnel brand awareness and sponsorship value."
  },
  avg_engagement_per_post: {
    label: "Avg Engagement Per Post",
    definition: "The average number of interactions per post across social media platforms.",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "50K avg engagement per post shows high content quality.",
    benchmarked: true,
    asset: "social_media",
    commercialImpact: "Indicates content resonance and audience connection."
  },
  engagement_rate: {
    label: "Engagement Rate",
    definition: "The percentage of followers who engage with the content.",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "A 3% engagement rate means 3 out of 100 followers interacted with the post.",
    benchmarked: true,
    asset: "social_media",
    commercialImpact: "Measures audience health and content relevance."
  },
  international_engagement_ratio: {
    label: "International Engagement Ratio",
    definition: "The proportion of total engagement coming from audiences outside the primary domestic market.",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "An 80% international ratio indicates strong global brand appeal.",
    benchmarked: true,
    asset: "social_media",
    commercialImpact: "Highlights global reach and potential for international merchandising and broadcasting."
  },
  total_estimated_views: {
    label: "Total Estimated Views",
    definition: "The estimated total number of views for social media content, particularly video content.",
    polarity: 1,
    polarityLabel: "Higher is better",
    example: "10M estimated views indicates a large audience reach.",
    benchmarked: false,
    asset: "social_media",
    commercialImpact: "Reflects broad reach for sponsor visibility."
  }
};

export function getMetricDef(metricName: string): MetricDefinition | null {
  return METRIC_DEFINITIONS[metricName] ?? null;
}

// Helper to get polarity symbol
export function getPolaritySymbol(polarity: 1 | -1 | 0): string {
  if (polarity === 1) return "↑";
  if (polarity === -1) return "↓";
  return "→";
}

// Helper to get unit type
export function getMetricUnit(metricName: string): string {
  const def = getMetricDef(metricName);
  if (!def) return "";

  // Determine unit based on metric characteristics
  if (metricName.includes("rate") || metricName.includes("pct_") || metricName.includes("_rate") ||
      metricName === "bounce_rate" || metricName === "conversion_rate") {
    return "%";
  }
  if (metricName === "net_sales" || metricName === "cart_value") {
    return "€";
  }
  if (metricName === "user_rating") {
    return "★";
  }
  if (metricName === "session_time_avg") {
    return "min";
  }
  if (metricName === "recurrence" || metricName === "video_recurrence" || metricName === "consumption") {
    return "×";
  }
  return "count";
}
