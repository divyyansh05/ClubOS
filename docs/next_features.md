# ClubOS — Upcoming Features

> This document describes everything being built next for ClubOS.
> Written for anyone — no technical knowledge required.
> Each feature includes what it does, why it matters, and what it enables.

---

## Category 1 — AI Intelligence

Features that make ClubOS answer questions, explain findings,
and work autonomously — turning data into conversation.

---

### AI Scout Assistant
**What it is:** A natural language interface inside ClubOS.
Type a question in plain English — "Why is conversion rate
the top priority?" or "Which signal should we act on first?"
— and ClubOS answers using the actual data it holds.

**What it adds:** No more needing to know which screen to look at
or which metric to find. Anyone on the team can ask a question
and get a grounded, specific answer in seconds.

**What it enables:** Non-technical stakeholders — commercial
directors, marketing leads, the CEO — can interrogate the data
directly without needing an analyst to translate it.

**How it will be built:** A new /assistant page with a text input
and streaming response. The backend calls the Claude AI API,
injects the current Gold table data as context, and returns
an answer that cites the specific data it used. Temperature
set low for factual consistency. Guardrails prevent invented
metrics.

---

### Historical Briefing Intelligence (RAG)
**What it is:** The ability to ask ClubOS questions about the past.
"How does this January compare to last January?" or "When was
the last time streaming subscriptions were this low?"

**What it adds:** Context that currently does not exist anywhere
in the tool. Right now ClubOS shows what is happening now.
This feature adds the ability to compare against any prior period.

**What it enables:** Longitudinal analysis without spreadsheets.
A commercial director preparing a board presentation can ask
ClubOS to compare this quarter to the same quarter two years ago
and get a structured, cited answer in under ten seconds.

**How it will be built:** Monthly briefings are chunked, embedded,
and stored in a vector database (Chroma). When a question is asked,
the system retrieves the most relevant historical briefing chunks
and injects them as context for the AI response. This is called
RAG — Retrieval Augmented Generation.

---

### Semantic Metric Search
**What it is:** Search for metrics by meaning, not by name.
Type "fan loyalty" and get heavy_users, video_recurrence,
session_time_avg returned — even though none of them contain
the word "loyalty."

**What it adds:** Discoverability. Right now finding the right
metric requires knowing its exact technical name. Semantic search
understands intent.

**What it enables:** Any team member can find relevant metrics
without knowing the data dictionary. The tool becomes self-guided.

**How it will be built:** All 52 metric definitions are converted
to numerical vector representations (embeddings). When a user
searches, their query is converted the same way and the closest
matching metrics are returned. Built with OpenAI embeddings and
Chroma vector database.

---

### ClubOS MCP Server
**What it is:** A connection layer that lets any AI assistant
(Claude, ChatGPT, Microsoft Copilot) query ClubOS data directly
in a conversation.

**What it adds:** ClubOS data becomes accessible from wherever
the team already works — not just from the ClubOS URL.

**What it enables:** A club analyst using Claude or Copilot can
ask "what are Real Madrid's top priorities this month?" and get
a live answer from ClubOS without opening a browser.

**How it will be built:** An MCP (Model Context Protocol) server
that exposes ClubOS tools: get_priorities(), get_signals(),
get_peer_benchmark(), get_metric_history(). Any MCP-compatible
AI client connects and queries live data.

---

### Monthly Analysis Agent
**What it is:** An autonomous AI agent that runs automatically
every time new data is uploaded. It analyses what changed,
drafts the monthly briefing narrative, flags anomalies, and
presents a draft for human review and approval.

**What it adds:** The monthly briefing goes from a structured
data summary to a full narrative analysis — automatically.

**What it enables:** Cuts monthly reporting preparation from
hours to minutes. The analyst reviews and approves rather than
writing from scratch.

**How it will be built:** A multi-step AI agent using the ReAct
pattern — it calls ClubOS data tools, reasons about the results,
calls more tools, and iterates until it has enough to write a
complete briefing. Every step is logged. Human approval required
before the briefing is published.

---

### Slack Stage 2 — AI Agent in Channel
**What it is:** An upgrade to the existing Slack alerts.
When an alert fires in the #clubos-alerts channel, an AI agent
joins the thread. The team can ask it questions — "explain this",
"is this seasonal?", "draft a note for the eCommerce lead" —
and it responds with live ClubOS data.

**What it adds:** The alert becomes a conversation, not a
notification. The team can investigate and act without leaving Slack.

**What it enables:** Faster response to priorities. The loop
from "alert received" to "action taken" shrinks from days to
minutes.

**How it will be built:** The ClubOS MCP server (above) connects
to a Claude bot configured as a Slack app. When mentioned in
the alert thread, the agent calls MCP tools for live data and
responds in the thread.

---

## Category 2 — Production & Scale

Features that make ClubOS deployable to real club infrastructure,
at scale, with proper security and automation.

---

### Authentication & Role-Based Access
**What it is:** Login system with different permission levels.
Viewer (read-only), Analyst (can upload data), Admin
(can configure weights and settings).

**What it adds:** The ability to give different team members
different levels of access. Currently anyone with the URL
can see and do everything.

**What it enables:** Safe deployment to a full department.
The commercial director sees the tool. The data team manages it.
Leadership sees a read-only view on their phones.

**How it will be built:** SSO via Google Workspace or Okta.
JWT tokens. Role middleware in FastAPI. Frontend routes protected
by role checks.

---

### Automated Data Ingestion
**What it is:** Automatic data collection that replaces the
current manual CSV upload process. Data arrives in ClubOS
nightly without anyone doing anything.

**What it adds:** Monthly reporting becomes automatic.
No more exporting CSVs, uploading files, waiting for processing.

**What it enables:** Weekly or even daily data updates become
feasible. The tool goes from a monthly review to a continuous
monitoring system.

**How it will be built:** API connectors (GA4, YouTube, Adobe
Analytics) pull data on a Cloud Scheduler nightly job. The
existing connector architecture (YouTube, Wikipedia connectors
already built) is extended for each data source.

---

### PDF Export
**What it is:** A single button on the Monthly Briefing screen
that generates a board-ready PDF of the full briefing.

**What it adds:** The briefing can be sent to leadership,
printed, or attached to a meeting agenda without screenshots
or manual formatting.

**What it enables:** ClubOS output goes directly into board
meetings, investor presentations, and department reviews.

**How it will be built:** ReportLab or WeasyPrint Python library
renders the Monthly Briefing screen content into a structured
PDF with the ClubOS design system applied.

---

### Multi-Club Support
**What it is:** One deployment of ClubOS that serves multiple
clubs simultaneously, with full data isolation between them.

**What it adds:** ClubOS becomes a commercial SaaS product.
Any elite club can be onboarded onto the same infrastructure.

**What it enables:** The business model shifts from a custom
implementation to a scalable platform. Each club sees only
their own data.

**How it will be built:** A club_id dimension is added to all
Gold tables. Each API request is scoped to the authenticated
club. The data pipeline processes multiple clubs in parallel.
Pricing, billing, and onboarding flows are added.

---

### Weekly Data Cadence
**What it is:** Upgrade from monthly data updates to weekly,
for the most commercially critical metrics.

**What it adds:** Issues are detected 3 weeks earlier than
the current monthly cycle. A conversion rate problem that
starts in week 1 of the month is visible in week 1, not
at month end.

**What it enables:** Faster intervention. The Priority Board
becomes a weekly operational tool, not just a monthly review.

**How it will be built:** Requires GA4 connector (above) to
be live first. The data pipeline adds weekly aggregation.
The frontend adds granularity toggles: Monthly / Weekly.

---

## Category 3 — Analytics Depth

Features that make the existing analytics richer,
more accurate, and more actionable.

---

### Revenue Forecasting Module
**What it is:** Predicted values for next month's key metrics,
based on the validated signal relationships already in ClubOS.

**What it adds:** ClubOS currently shows what happened and
what is happening. Forecasting shows what is likely to happen.

**What it enables:** Proactive commercial planning. If ClubOS
predicts eCommerce revenue will drop 15% next month based on
current website traffic signals, the team can act now.

**How it will be built:** The 22 validated signals are used
as the prediction engine. Source metric current trends are
extrapolated through the validated lag relationships to
produce outcome metric forecasts. Confidence intervals shown.

---

### Custom Priority Weight Adjustment
**What it is:** A settings panel where club analysts can adjust
the five components of the priority scoring formula — Severity,
Persistence, Peer Gap, Commercial Impact, Evidence — to reflect
what matters most to their club.

**What it adds:** Different clubs have different strategic priorities.
A club focused on growing streaming revenue weights that dimension
higher. A club focused on market share weights peer benchmarking higher.

**What it enables:** ClubOS becomes club-specific rather than
generic. The priorities it surfaces reflect each club's actual
strategy.

**How it will be built:** The scoring_config.json weights are
exposed in a Settings screen with sliders. Changes rebuild the
priority scores live. Audit trail shows when weights were changed
and by whom.

---

### Historical Briefing Archive
**What it is:** Every monthly briefing stored and searchable.
Browse back through any prior month. Compare two months
side by side.

**What it adds:** Institutional memory. The team can see exactly
what was flagged 6 months ago and whether it was resolved.

**What it enables:** Year-over-year analysis, trend tracking
over multiple seasons, and accountability for whether
recommendations were acted on.

**How it will be built:** Monthly briefings written to a
briefings archive table with full timestamp and metadata.
A searchable index on the Monthly Briefing screen. The
RAG system (above) uses this archive as its knowledge base.

---

### Champions League & Competition Event Overlays
**What it is:** Automatic annotation of all metric charts
with Real Madrid's competition schedule — UCL group stage,
knockout rounds, El Clásico dates, La Liga title run-ins.

**What it adds:** Every spike and dip in the data is immediately
contextualised by what was happening on the pitch. No more
asking "why did streaming spike in March?"

**What it enables:** Pattern recognition across seasons.
The team can see that UCL knockout stages always drive
a streaming spike, and calibrate expectations accordingly.

**How it will be built:** Competition fixture data ingested
from a football data API (Sofascore or football-data.org).
The existing Event Calendar (already built) is extended
to auto-populate from the fixture feed.

---

### Expanded Peer Benchmark Coverage
**What it is:** Expanding from 8 benchmarked metrics to
the top 20, across more competitor clubs.

**What it adds:** A fuller competitive picture. Currently
only 8 metrics can be compared to peers. The most commercially
important 20 will be benchmarked.

**What it enables:** More precise competitive intelligence.
The club can identify gaps in areas not currently visible
in the benchmark.

**How it will be built:** Peer dataset extended. Additional
metrics mapped to canonical names. The benchmark pipeline
extended to process the larger dataset.

---

## Category 4 — Social Media Intelligence

Features that turn the social media analytics layer
into a full content strategy intelligence engine.

---

### Optimal Posting Schedule — Day & Time Analysis
**What it is:** A heatmap showing which days of the week
generate the highest engagement on each platform.
Current data shows Thursday Instagram posts generate
426,000 avg engagement — 17% above the weekly average.

**What it adds:** Data-driven posting schedule for the
social media team. No more posting by gut feel or habit.

**What it enables:** Immediate engagement improvement
with zero additional content production — just post the
same content on better days.

**How it will be built:** The 55,598-post dataset is
analysed by day of week × platform × content type.
A 7×5 heatmap is added to the Social Intelligence screen.
Auto-generated recommendation: "Post key content on
Thursdays for Instagram, Wednesdays for TikTok."

---

### Match Moment Content Intelligence
**What it is:** Performance analysis of content posted
before, during, and after matches. Current data shows
post-match content generates 2.1× more engagement
than non-matchday content — but represents only 0.5%
of all posts.

**What it adds:** The biggest untapped opportunity in
Real Madrid's current social content strategy, quantified
and made visible.

**What it enables:** A clear case for the content team
to increase post-match content volume. Each additional
post-match piece is worth approximately 131,000 engagement
units based on current averages.

**How it will be built:** Scenes field in the post dataset
is used as a match timing proxy. Pre/During/Post/Non-matchday
categories are computed and visualised as a bar chart with
underutilisation alerts.

---

### Content Format Intelligence — Reels vs Standard Posts
**What it is:** Performance comparison across content formats —
Reels, standard images, videos, YouTube Shorts, Stories.
Current data: Instagram Reels generate 522,000 avg engagement
vs 67,000 for standard posts — a 7.8× multiplier.

**What it adds:** Quantified evidence for a Reels-first
content strategy. Currently only 1,296 Reels vs 48,661
standard posts in 2025.

**What it enables:** A format strategy shift that could
multiply total engagement without increasing posting frequency.

**How it will be built:** Media Type and Variety fields
analysed by platform. Format multiplier table added to
Social Intelligence screen. Underutilised high-performers
highlighted with amber callout boxes.

---

### Hashtag Performance Index
**What it is:** A ranked index of every hashtag Real Madrid
uses, showing which ones correlate with higher engagement.
#GraciasLuka averaged 896,000 engagement per post.
#ElClásico averaged 633,000. Branded hashtags average 45,000.

**What it adds:** Data-driven hashtag strategy. The content
team knows which hashtags amplify reach and which are noise.

**What it enables:** Higher organic reach from the same content,
by pairing posts with the highest-performing relevant hashtags.

**How it will be built:** Text field from all 55,598 posts
parsed for hashtags. Performance indexed by avg engagement
per post. Categorised as event, player, branded, or farewell.
Leaderboard added to Social Intelligence screen.

---

### Dynamic Insights Panel
**What it is:** An auto-generated panel of plain-English
findings that updates every time new data arrives.
Example: "Instagram Reels generate 7.8× more engagement
than standard posts. Despite this, Reels represent only
2.6% of posts in 2025."

**What it adds:** The most important findings surface
automatically — no analyst needed to spot them.

**What it enables:** A first-time user opening ClubOS
immediately sees the three most actionable insights
without having to explore every chart.

**How it will be built:** A template engine generates
insight strings from live computed statistics. Priority
score assigned to each insight. Top insights rendered
as cards at the top of the Social Intelligence screen.
Updates dynamically when new data is loaded.

---

### Content Team Recommendation Engine
**What it is:** A ranked list of specific, actionable
recommendations for the social media content team,
generated from the data automatically.
Example: "#1 Convert standard image posts to Reels.
Impact: +7.8× engagement per post. Effort: Low."

**What it adds:** ClubOS becomes a decision-support tool
for the content team, not just an analytics viewer.

**What it enables:** Direct connection between data
analysis and content strategy decisions.
Recommendations update as the data changes.

**How it will be built:** Insight templates generate
recommendations with effort estimates and impact
projections. Sorted by impact-to-effort ratio.
Rendered as a numbered priority list on the Social
Intelligence screen.

---

*Document maintained by ClubOS development.
Last updated: automatically on feature completion.
Questions: reply to divyyansh99@gmail.com*
