export type FeatureStatus = 'planned' | 'in_progress' | 'research';

export type FeatureCategory =
  | 'AI Intelligence'
  | 'Production & Scale'
  | 'Analytics Depth'
  | 'Social Media Intelligence';

export interface UpcomingFeature {
  id: string;
  name: string;
  category: FeatureCategory;
  status: FeatureStatus;
  tagline: string;
  whatItIs: string;
  whatItAdds: string;
  whatItEnables: string;
  howItWillBeBuilt: string;
}

export const CATEGORY_COLORS: Record<FeatureCategory, {
  bg: string;
  text: string;
  border: string;
  dot: string;
}> = {
  'AI Intelligence': {
    bg: 'bg-purple-50 dark:bg-purple-950/30',
    text: 'text-purple-700 dark:text-purple-300',
    border: 'border-purple-200 dark:border-purple-800',
    dot: 'bg-purple-500'
  },
  'Production & Scale': {
    bg: 'bg-blue-50 dark:bg-blue-950/30',
    text: 'text-blue-700 dark:text-blue-300',
    border: 'border-blue-200 dark:border-blue-800',
    dot: 'bg-blue-500'
  },
  'Analytics Depth': {
    bg: 'bg-amber-50 dark:bg-amber-950/30',
    text: 'text-amber-700 dark:text-amber-300',
    border: 'border-amber-200 dark:border-amber-800',
    dot: 'bg-amber-500'
  },
  'Social Media Intelligence': {
    bg: 'bg-green-50 dark:bg-green-950/30',
    text: 'text-green-700 dark:text-green-300',
    border: 'border-green-200 dark:border-green-800',
    dot: 'bg-green-500'
  }
};

export const STATUS_LABELS: Record<FeatureStatus, { label: string; color: string }> = {
  planned: { label: 'Planned', color: 'text-stone-600 dark:text-stone-400' },
  in_progress: { label: 'In Progress', color: 'text-blue-600 dark:text-blue-400' },
  research: { label: 'Research', color: 'text-amber-600 dark:text-amber-400' }
};

export const UPCOMING_FEATURES: UpcomingFeature[] = [
  {
    id: 'ai-scout',
    name: 'AI Scout Assistant',
    category: 'AI Intelligence',
    status: 'planned',
    tagline: 'Ask ClubOS questions in plain English and get answers from the data.',
    whatItIs: 'A natural language interface inside ClubOS. Type a question in plain English — "Why is conversion rate the top priority?" or "Which signal should we act on first?" — and ClubOS answers using the actual data it holds.',
    whatItAdds: 'No more needing to know which screen to look at or which metric to find. Anyone on the team can ask a question and get a grounded, specific answer in seconds.',
    whatItEnables: 'Non-technical stakeholders — commercial directors, marketing leads, the CEO — can interrogate the data directly without needing an analyst to translate it.',
    howItWillBeBuilt: 'A new /assistant page with a text input and streaming response. The backend calls the Claude AI API, injects the current Gold table data as context, and returns an answer that cites the specific data it used. Temperature set low for factual consistency. Guardrails prevent invented metrics.'
  },
  {
    id: 'historical-rag',
    name: 'Historical Briefing Intelligence (RAG)',
    category: 'AI Intelligence',
    status: 'planned',
    tagline: 'Ask ClubOS about the past — compare any month to any prior month.',
    whatItIs: 'The ability to ask ClubOS questions about the past. "How does this January compare to last January?" or "When was the last time streaming subscriptions were this low?"',
    whatItAdds: 'Context that currently does not exist anywhere in the tool. Right now ClubOS shows what is happening now. This feature adds the ability to compare against any prior period.',
    whatItEnables: 'Longitudinal analysis without spreadsheets. A commercial director preparing a board presentation can ask ClubOS to compare this quarter to the same quarter two years ago and get a structured, cited answer in under ten seconds.',
    howItWillBeBuilt: 'Monthly briefings are chunked, embedded, and stored in a vector database (Chroma). When a question is asked, the system retrieves the most relevant historical briefing chunks and injects them as context for the AI response. This is called RAG — Retrieval Augmented Generation.'
  },
  {
    id: 'semantic-search',
    name: 'Semantic Metric Search',
    category: 'AI Intelligence',
    status: 'planned',
    tagline: 'Search for metrics by what they mean, not what they are called.',
    whatItIs: 'Search for metrics by meaning, not by name. Type "fan loyalty" and get heavy_users, video_recurrence, session_time_avg returned — even though none of them contain the word "loyalty."',
    whatItAdds: 'Discoverability. Right now finding the right metric requires knowing its exact technical name. Semantic search understands intent.',
    whatItEnables: 'Any team member can find relevant metrics without knowing the data dictionary. The tool becomes self-guided.',
    howItWillBeBuilt: 'All 52 metric definitions are converted to numerical vector representations (embeddings). When a user searches, their query is converted the same way and the closest matching metrics are returned. Built with OpenAI embeddings and Chroma vector database.'
  },
  {
    id: 'mcp-server',
    name: 'ClubOS MCP Server',
    category: 'AI Intelligence',
    status: 'research',
    tagline: 'Query ClubOS data from any AI assistant — Claude, Copilot, ChatGPT.',
    whatItIs: 'A connection layer that lets any AI assistant (Claude, ChatGPT, Microsoft Copilot) query ClubOS data directly in a conversation.',
    whatItAdds: 'ClubOS data becomes accessible from wherever the team already works — not just from the ClubOS URL.',
    whatItEnables: 'A club analyst using Claude or Copilot can ask "what are Real Madrid\'s top priorities this month?" and get a live answer from ClubOS without opening a browser.',
    howItWillBeBuilt: 'An MCP (Model Context Protocol) server that exposes ClubOS tools: get_priorities(), get_signals(), get_peer_benchmark(), get_metric_history(). Any MCP-compatible AI client connects and queries live data.'
  },
  {
    id: 'monthly-agent',
    name: 'Monthly Analysis Agent',
    category: 'AI Intelligence',
    status: 'planned',
    tagline: 'ClubOS drafts the monthly briefing automatically — you just review and approve.',
    whatItIs: 'An autonomous AI agent that runs automatically every time new data is uploaded. It analyses what changed, drafts the monthly briefing narrative, flags anomalies, and presents a draft for human review and approval.',
    whatItAdds: 'The monthly briefing goes from a structured data summary to a full narrative analysis — automatically.',
    whatItEnables: 'Cuts monthly reporting preparation from hours to minutes. The analyst reviews and approves rather than writing from scratch.',
    howItWillBeBuilt: 'A multi-step AI agent using the ReAct pattern — it calls ClubOS data tools, reasons about the results, calls more tools, and iterates until it has enough to write a complete briefing. Every step is logged. Human approval required before the briefing is published.'
  },
  {
    id: 'slack-agent',
    name: 'Slack AI Agent (Stage 2)',
    category: 'AI Intelligence',
    status: 'planned',
    tagline: 'When a Slack alert fires, an AI joins the thread to answer questions and draft responses.',
    whatItIs: 'An upgrade to the existing Slack alerts. When an alert fires in the #clubos-alerts channel, an AI agent joins the thread. The team can ask it questions — "explain this", "is this seasonal?", "draft a note for the eCommerce lead" — and it responds with live ClubOS data.',
    whatItAdds: 'The alert becomes a conversation, not a notification. The team can investigate and act without leaving Slack.',
    whatItEnables: 'Faster response to priorities. The loop from "alert received" to "action taken" shrinks from days to minutes.',
    howItWillBeBuilt: 'The ClubOS MCP server (above) connects to a Claude bot configured as a Slack app. When mentioned in the alert thread, the agent calls MCP tools for live data and responds in the thread.'
  },
  {
    id: 'auth-rbac',
    name: 'Authentication & Role-Based Access',
    category: 'Production & Scale',
    status: 'planned',
    tagline: 'Secure login with different access levels for different team members.',
    whatItIs: 'Login system with different permission levels. Viewer (read-only), Analyst (can upload data), Admin (can configure weights and settings).',
    whatItAdds: 'The ability to give different team members different levels of access. Currently anyone with the URL can see and do everything.',
    whatItEnables: 'Safe deployment to a full department. The commercial director sees the tool. The data team manages it. Leadership sees a read-only view on their phones.',
    howItWillBeBuilt: 'SSO via Google Workspace or Okta. JWT tokens. Role middleware in FastAPI. Frontend routes protected by role checks.'
  },
  {
    id: 'auto-ingestion',
    name: 'Automated Data Ingestion',
    category: 'Production & Scale',
    status: 'planned',
    tagline: 'Data arrives in ClubOS automatically every night — no manual uploads needed.',
    whatItIs: 'Automatic data collection that replaces the current manual CSV upload process. Data arrives in ClubOS nightly without anyone doing anything.',
    whatItAdds: 'Monthly reporting becomes automatic. No more exporting CSVs, uploading files, waiting for processing.',
    whatItEnables: 'Weekly or even daily data updates become feasible. The tool goes from a monthly review to a continuous monitoring system.',
    howItWillBeBuilt: 'API connectors (GA4, YouTube, Adobe Analytics) pull data on a Cloud Scheduler nightly job. The existing connector architecture (YouTube, Wikipedia connectors already built) is extended for each data source.'
  },
  {
    id: 'pdf-export',
    name: 'PDF Export',
    category: 'Production & Scale',
    status: 'planned',
    tagline: 'One click to generate a board-ready PDF of the monthly briefing.',
    whatItIs: 'A single button on the Monthly Briefing screen that generates a board-ready PDF of the full briefing.',
    whatItAdds: 'The briefing can be sent to leadership, printed, or attached to a meeting agenda without screenshots or manual formatting.',
    whatItEnables: 'ClubOS output goes directly into board meetings, investor presentations, and department reviews.',
    howItWillBeBuilt: 'ReportLab or WeasyPrint Python library renders the Monthly Briefing screen content into a structured PDF with the ClubOS design system applied.'
  },
  {
    id: 'multi-club',
    name: 'Multi-Club Support',
    category: 'Production & Scale',
    status: 'research',
    tagline: 'One ClubOS platform serving multiple clubs, each with complete data isolation.',
    whatItIs: 'One deployment of ClubOS that serves multiple clubs simultaneously, with full data isolation between them.',
    whatItAdds: 'ClubOS becomes a commercial SaaS product. Any elite club can be onboarded onto the same infrastructure.',
    whatItEnables: 'The business model shifts from a custom implementation to a scalable platform. Each club sees only their own data.',
    howItWillBeBuilt: 'A club_id dimension is added to all Gold tables. Each API request is scoped to the authenticated club. The data pipeline processes multiple clubs in parallel. Pricing, billing, and onboarding flows are added.'
  },
  {
    id: 'weekly-cadence',
    name: 'Weekly Data Cadence',
    category: 'Production & Scale',
    status: 'research',
    tagline: 'Key metrics updated weekly instead of monthly — catch problems 3 weeks earlier.',
    whatItIs: 'Upgrade from monthly data updates to weekly, for the most commercially critical metrics.',
    whatItAdds: 'Issues are detected 3 weeks earlier than the current monthly cycle. A conversion rate problem that starts in week 1 of the month is visible in week 1, not at month end.',
    whatItEnables: 'Faster intervention. The Priority Board becomes a weekly operational tool, not just a monthly review.',
    howItWillBeBuilt: 'Requires GA4 connector (above) to be live first. The data pipeline adds weekly aggregation. The frontend adds granularity toggles: Monthly / Weekly.'
  },
  {
    id: 'forecasting',
    name: 'Revenue Forecasting Module',
    category: 'Analytics Depth',
    status: 'planned',
    tagline: 'See what is likely to happen next month — based on signals already in the data.',
    whatItIs: 'Predicted values for next month\'s key metrics, based on the validated signal relationships already in ClubOS.',
    whatItAdds: 'ClubOS currently shows what happened and what is happening. Forecasting shows what is likely to happen.',
    whatItEnables: 'Proactive commercial planning. If ClubOS predicts eCommerce revenue will drop 15% next month based on current website traffic signals, the team can act now.',
    howItWillBeBuilt: 'The 22 validated signals are used as the prediction engine. Source metric current trends are extrapolated through the validated lag relationships to produce outcome metric forecasts. Confidence intervals shown.'
  },
  {
    id: 'custom-weights',
    name: 'Custom Priority Weight Adjustment',
    category: 'Analytics Depth',
    status: 'planned',
    tagline: 'Adjust the priority scoring formula to reflect what matters most to your club.',
    whatItIs: 'A settings panel where club analysts can adjust the five components of the priority scoring formula — Severity, Persistence, Peer Gap, Commercial Impact, Evidence — to reflect what matters most to their club.',
    whatItAdds: 'Different clubs have different strategic priorities. A club focused on growing streaming revenue weights that dimension higher. A club focused on market share weights peer benchmarking higher.',
    whatItEnables: 'ClubOS becomes club-specific rather than generic. The priorities it surfaces reflect each club\'s actual strategy.',
    howItWillBeBuilt: 'The scoring_config.json weights are exposed in a Settings screen with sliders. Changes rebuild the priority scores live. Audit trail shows when weights were changed and by whom.'
  },
  {
    id: 'briefing-archive',
    name: 'Historical Briefing Archive',
    category: 'Analytics Depth',
    status: 'planned',
    tagline: 'Browse and compare every monthly briefing ever generated.',
    whatItIs: 'Every monthly briefing stored and searchable. Browse back through any prior month. Compare two months side by side.',
    whatItAdds: 'Institutional memory. The team can see exactly what was flagged 6 months ago and whether it was resolved.',
    whatItEnables: 'Year-over-year analysis, trend tracking over multiple seasons, and accountability for whether recommendations were acted on.',
    howItWillBeBuilt: 'Monthly briefings written to a briefings archive table with full timestamp and metadata. A searchable index on the Monthly Briefing screen. The RAG system (above) uses this archive as its knowledge base.'
  },
  {
    id: 'competition-overlays',
    name: 'Competition Event Overlays',
    category: 'Analytics Depth',
    status: 'planned',
    tagline: 'Every metric chart annotated with match results, UCL fixtures, and La Liga milestones.',
    whatItIs: 'Automatic annotation of all metric charts with Real Madrid\'s competition schedule — UCL group stage, knockout rounds, El Clásico dates, La Liga title run-ins.',
    whatItAdds: 'Every spike and dip in the data is immediately contextualised by what was happening on the pitch. No more asking "why did streaming spike in March?"',
    whatItEnables: 'Pattern recognition across seasons. The team can see that UCL knockout stages always drive a streaming spike, and calibrate expectations accordingly.',
    howItWillBeBuilt: 'Competition fixture data ingested from a football data API (Sofascore or football-data.org). The existing Event Calendar (already built) is extended to auto-populate from the fixture feed.'
  },
  {
    id: 'expanded-benchmark',
    name: 'Expanded Peer Benchmark Coverage',
    category: 'Analytics Depth',
    status: 'planned',
    tagline: 'Compare against peers on 20 metrics instead of 8.',
    whatItIs: 'Expanding from 8 benchmarked metrics to the top 20, across more competitor clubs.',
    whatItAdds: 'A fuller competitive picture. Currently only 8 metrics can be compared to peers. The most commercially important 20 will be benchmarked.',
    whatItEnables: 'More precise competitive intelligence. The club can identify gaps in areas not currently visible in the benchmark.',
    howItWillBeBuilt: 'Peer dataset extended. Additional metrics mapped to canonical names. The benchmark pipeline extended to process the larger dataset.'
  },
  {
    id: 'posting-schedule',
    name: 'Optimal Posting Schedule',
    category: 'Social Media Intelligence',
    status: 'planned',
    tagline: 'Data-driven schedule showing best days and times to post on each platform.',
    whatItIs: 'A heatmap showing which days of the week generate the highest engagement on each platform. Current data shows Thursday Instagram posts generate 426,000 avg engagement — 17% above the weekly average.',
    whatItAdds: 'Data-driven posting schedule for the social media team. No more posting by gut feel or habit.',
    whatItEnables: 'Immediate engagement improvement with zero additional content production — just post the same content on better days.',
    howItWillBeBuilt: 'The 55,598-post dataset is analysed by day of week × platform × content type. A 7×5 heatmap is added to the Social Intelligence screen. Auto-generated recommendation: "Post key content on Thursdays for Instagram, Wednesdays for TikTok."'
  },
  {
    id: 'match-moment',
    name: 'Match Moment Content Intelligence',
    category: 'Social Media Intelligence',
    status: 'planned',
    tagline: 'Post-match content generates 2.1× more engagement but represents only 0.5% of posts.',
    whatItIs: 'Performance analysis of content posted before, during, and after matches. Current data shows post-match content generates 2.1× more engagement than non-matchday content — but represents only 0.5% of all posts.',
    whatItAdds: 'The biggest untapped opportunity in Real Madrid\'s current social content strategy, quantified and made visible.',
    whatItEnables: 'A clear case for the content team to increase post-match content volume. Each additional post-match piece is worth approximately 131,000 engagement units based on current averages.',
    howItWillBeBuilt: 'Scenes field in the post dataset is used as a match timing proxy. Pre/During/Post/Non-matchday categories are computed and visualised as a bar chart with underutilisation alerts.'
  },
  {
    id: 'content-format',
    name: 'Content Format Intelligence',
    category: 'Social Media Intelligence',
    status: 'in_progress',
    tagline: 'Instagram Reels generate 7.8× more engagement than standard posts.',
    whatItIs: 'Performance comparison across content formats — Reels, standard images, videos, YouTube Shorts, Stories. Current data: Instagram Reels generate 522,000 avg engagement vs 67,000 for standard posts — a 7.8× multiplier.',
    whatItAdds: 'Quantified evidence for a Reels-first content strategy. Currently only 1,296 Reels vs 48,661 standard posts in 2025.',
    whatItEnables: 'A format strategy shift that could multiply total engagement without increasing posting frequency.',
    howItWillBeBuilt: 'Media Type and Variety fields analysed by platform. Format multiplier table added to Social Intelligence screen. Underutilised high-performers highlighted with amber callout boxes.'
  },
  {
    id: 'hashtag-performance',
    name: 'Hashtag Performance Index',
    category: 'Social Media Intelligence',
    status: 'planned',
    tagline: 'Ranked index of every hashtag showing which ones drive the most engagement.',
    whatItIs: 'A ranked index of every hashtag Real Madrid uses, showing which ones correlate with higher engagement. #GraciasLuka averaged 896,000 engagement per post. #ElClásico averaged 633,000. Branded hashtags average 45,000.',
    whatItAdds: 'Data-driven hashtag strategy. The content team knows which hashtags amplify reach and which are noise.',
    whatItEnables: 'Higher organic reach from the same content, by pairing posts with the highest-performing relevant hashtags.',
    howItWillBeBuilt: 'Text field from all 55,598 posts parsed for hashtags. Performance indexed by avg engagement per post. Categorised as event, player, branded, or farewell. Leaderboard added to Social Intelligence screen.'
  },
  {
    id: 'dynamic-insights',
    name: 'Dynamic Insights Panel',
    category: 'Social Media Intelligence',
    status: 'planned',
    tagline: 'Auto-generated plain-English findings that update when new data arrives.',
    whatItIs: 'An auto-generated panel of plain-English findings that updates every time new data arrives. Example: "Instagram Reels generate 7.8× more engagement than standard posts. Despite this, Reels represent only 2.6% of posts in 2025."',
    whatItAdds: 'The most important findings surface automatically — no analyst needed to spot them.',
    whatItEnables: 'A first-time user opening ClubOS immediately sees the three most actionable insights without having to explore every chart.',
    howItWillBeBuilt: 'A template engine generates insight strings from live computed statistics. Priority score assigned to each insight. Top insights rendered as cards at the top of the Social Intelligence screen. Updates dynamically when new data is loaded.'
  },
  {
    id: 'recommendation-engine',
    name: 'Content Team Recommendation Engine',
    category: 'Social Media Intelligence',
    status: 'planned',
    tagline: 'Ranked actionable recommendations — "Convert posts to Reels: +7.8× engagement. Effort: Low."',
    whatItIs: 'A ranked list of specific, actionable recommendations for the social media content team, generated from the data automatically. Example: "#1 Convert standard image posts to Reels. Impact: +7.8× engagement per post. Effort: Low."',
    whatItAdds: 'ClubOS becomes a decision-support tool for the content team, not just an analytics viewer.',
    whatItEnables: 'Direct connection between data analysis and content strategy decisions. Recommendations update as the data changes.',
    howItWillBeBuilt: 'Insight templates generate recommendations with effort estimates and impact projections. Sorted by impact-to-effort ratio. Rendered as a numbered priority list on the Social Intelligence screen.'
  }
];
