# Real Madrid Internship Project — Full Decision Brief
**Purpose:** Feed this to any AI to get questions, challenges, and gap analysis on what has been decided so far.

---

## 1. Project Context

- Student internship project at Real Madrid / Universidad Europea de Madrid
- Team size: 2–3 people
- Timeline: 4–6 weeks (flexible with extra time if needed)
- Format: Build a solution, present as a consultancy pitch to Real Madrid
- Requirement from institution: Original ideas, fresh thinking, something that could be integrated into Real Madrid's actual data operations
- Personal goal: Project strong enough to result in a job offer or integration into Real Madrid's data team, and strong enough to be a star portfolio project on GitHub

---

## 2. Theme Selected

**Group E — Dashboard for Historical Digital Business Data**

Supervisor: Rodrigo Valcárcel (rvalcarcel@realmadrid.es)

Other available themes (not selected):
- Group A — Prediction of Acute vs Chronic Workload Ratio for Players
- Group B — Refereeing Analysis Tool for Champions League vs La Liga
- Group C — Pricing Benchmark for Official Shirt of LaLiga Teams
- Group D — Social Media Analytics for Elite Sports Clubs

**Why Group E was selected:**
- Highest ceiling for original work
- Direct connection to business revenue decisions
- Can absorb elements of Group C (kit pricing) and Group D (social media) as supporting layers
- Aligns with data engineering background — pipeline quality is a differentiator
- Business data + forward-looking analysis = consultancy-style pitch

---

## 3. Data Availability

### What Real Madrid will provide
- Production-shaped business data (privacy-safe, not raw real data)
- Schema, column types, behavioral structure, and relative movement patterns expected to reflect real environment
- Names and exact values may be altered for privacy
- Social media data — real data, good size
- Some synthetic player data

### What must be sourced independently
- YouTube Data API — Real Madrid channel history, video metrics, comment data (free, available historically)
- Reddit API — football mentions, cross-club sentiment
- API-Sports — match calendar, results, competition history (public)
- LaLiga kit prices — scrape official club stores weekly
- Deloitte Money League reports — public commercial revenue benchmarks for calibration

### Critical data unknowns (must confirm before building)
- Exact fields in the production-shaped business data
- Granularity (daily? weekly? monthly?)
- Time range covered (how many years of history?)
- How many distinct major events with clean timestamps are anchored in the data?
- Whether the event calendar is clean enough to anchor archetype windows

---

## 4. Technology Stack

### Confirmed
- **Databricks** — pipeline and processing (Real Madrid uses this internally, non-negotiable)
- **Delta Lake** — medallion architecture (Bronze / Silver / Gold)
- **React** — frontend (custom web app, not Tableau or Power BI)
- **Python / PySpark** — analytical engine

### Flexible / To Decide
- AI layer: OpenAI API or open-source (LangChain + RAG pattern over Gold tables)
- Sentiment model: cardiffnlp/twitter-xlm-roberta (multilingual, football-appropriate)
- Forecasting: Prophet or DTW (Dynamic Time Warping) for archetype matching
- Visualization: Recharts or D3 inside React
- API middleware: FastAPI

---

## 5. Product Concept — What We Are Building

### One-line pitch
A commercial decision engine that tells Real Madrid's business team what is likely to happen next commercially — and exactly what to do about it, with historical evidence behind every recommendation.

### Full CEO pitch
We built a commercial decision engine for Real Madrid that tells their business team not just what is coming, but exactly what to do about it and when. It works by connecting Real Madrid's historical business data with live social signals to detect when a proven commercial window is opening — and then it delivers a specific recommended action: launch the MENA campaign in the next 4 days, pre-position kit inventory before this signing announcement, hold the subscription push until the rivalry spillover from the Clásico settles. Every recommendation comes with the historical evidence behind it — here are the three most similar situations from the past, here is what happened commercially in each one, here is the confidence level on this recommendation — so the commercial director is not trusting a black box, they are making a faster, better-informed decision with full transparency on why the product is saying what it is saying.

### Problem being solved
Real Madrid's commercial team currently reacts to demand after it peaks. They see the jersey sales spike after a signing is announced. They run campaigns after a UCL win when the demand wave is already cresting. Every day of lead time on a commercial window is worth money in a €1.1 billion revenue operation.

### Core product thesis
Social signals + historical business data → detect when a proven commercial window is opening → deliver a specific recommended action with timing, market, confidence level, and historical evidence.

---

## 6. What Makes This Novel

### Genuine novelty claims
1. **The combination** — social signals and historical business data joined into a single forward-looking commercial decision engine. No football club has built this.
2. **Event archetype matching** — reasoning from historical analog situations to project future commercial windows. Exists in financial portfolio theory. Never applied to football commercial operations.
3. **Transparent evidence layer** — every recommendation shows the historical analogs it is based on. Most predictive tools are black boxes. This one shows its work.
4. **Forward-looking framing** — the product answers "what should we do next" not "what happened last month."

### What is NOT novel (explicitly acknowledged)
- Social media analytics alone — Blinkfire, Zoomph already do this
- Business KPI dashboards — every BI tool does this
- Sentiment analysis — completely standard
- AI chat assistant — everyone is building this now
- Content calendar optimizer — commodity feature

### Novelty defense under questioning
"Can someone point to an existing product that does exactly this for a football club?" — The answer is no. Not because individual parts are new, but because no product connects these signals specifically to forward-looking commercial decisions with evidence, built for a football club's commercial team.

---

## 7. Analytical Engine — Metrics and What They Power

### The data logic
Social signals are the INPUT. Historical business data is the EVIDENCE LAYER. Commercial recommended actions are the OUTPUT.

Every social metric earns its place only if it answers: "what does this tell the commercial team to do differently?"

### Core metric families

**Attention Economy Metrics (from social data)**

| Metric | Definition | Commercial Use |
|---|---|---|
| Attention Half-Life | Decay rate of engagement after a content release or event | Optimal campaign window length |
| Content Compounding Score | Ratio of week-2-plus engagement to week-1 per content type | Where to allocate content production budget |
| Narrative Fatigue Index | Volume-engagement divergence score on rolling window | When to stop spending on a narrative before commercial value is extracted |
| Market Activation Gap | Organic engagement divided by directed content effort by language cohort | Where to launch the next geo-targeted campaign |
| Player Dependence Risk Index | Concentration of engagement across individual players | Revenue concentration risk if key players are unavailable |
| Rivalry Spillover Coefficient | Estimated attention bleed toward competitors during their major events, with recovery curve | When NOT to launch a campaign |
| Earned Reach Multiplier | Total reach of shares and reposts divided by organic reach of original post | Content efficiency, marketing spend optimisation |
| Language Asymmetry | Cross-market engagement divergence detection by language cohort | Localised commercial activation timing |

**Commercial Signal Metrics (from business data)**

| Metric | Definition | Commercial Use |
|---|---|---|
| Commercial Opportunity Index | Composite 0–100 score updated daily | Single number telling commercial team if a window is opening |
| Content-Commerce Lag | Time-lagged correlation between content type performance and commercial indicators | Which content types to prioritise for revenue impact |
| Trophy/Event Lift | Event-window analysis around major events showing commercial movement shapes | Financial planning, pre-positioning inventory |
| Event Archetype Profile | Signal fingerprint of each historical event across a standard window | Foundation of the scenario simulator |
| Projected Trajectory | Weighted average outcome across closest historical analogs | Forward-looking commercial window shape with confidence range |

---

## 8. Product Structure — 5 Views

### View 1 — Intelligence Surface (Homepage)
Not a menu. A daily briefing.
- Current Commercial Opportunity Index score (0–100) with directional indicator
- One specific recommended action with timing and confidence level
- Top forming pattern: if current signals are beginning to match a known archetype, surface it here
- Active narratives with fatigue flags
- Not a dashboard. A decision briefing.

### View 2 — Scenario Simulator (Hero interaction)
The most important view. Answers: "we are planning X — what is likely to happen and when?"
- User selects a planned event type (signing, kit launch, trophy run, rivalry match)
- Sets parameters: approximate timing, target markets, expected content volume
- System returns three closest historical analog events with their commercial trajectory shapes
- Projected trajectory shown with confidence range (direction and timing, not precise values)
- User can adjust parameters and see projection update in real time
- CRITICAL: Evidence vs simulation distinction enforced visually throughout — historical data on solid background, simulated projections on dashed border background, "simulated" label always visible

### View 3 — Attention Health
Six attention economy metrics each with dedicated visualisation.
- Player Dependence shown as concentration risk view (portfolio-style, not bar chart)
- Market Activation Gap shown as geographic opportunity ranking
- Content Compounding shown as decay curve comparison across content types
- Narrative Fatigue shown as volume-quality divergence timeline
- Every metric includes plain-language interpretation of what it means commercially

### View 4 — Event Archive and Archetype Explorer
Historical event library made visible.
- Browse all historical events, see how they cluster into archetypes
- Select any past event and see its full signal profile
- Builds trust in the analytical engine by making underlying data visible
- Lets commercial team learn from history on their own terms

### View 5 — AI Assistant
Natural language query interface scoped to the product's data.
- Not general purpose
- Pre-engineered to handle 20 highest-value questions a commercial decision-maker would ask
- Responses include the data behind the answer, not just the answer
- This is the interface layer — not the novelty claim

---

## 9. Architecture — Databricks Medallion

### Bronze Layer (raw ingestion)
- YouTube Data API: video metadata, view counts, comment counts, like counts
- Reddit API: mentions, engagement, sentiment texture
- Production-shaped business data: loaded as-is from Real Madrid
- Match and event calendar: API-Sports
- Kit prices: weekly scrape of official LaLiga club stores

### Silver Layer (cleaned and enriched)
- Standardise all timestamps to UTC
- Attach event context to every row within configurable window (default ±30 days)
- Run multilingual sentiment scoring (cardiffnlp/twitter-xlm-roberta)
- Compute language cohort tags from comment metadata
- Join social signals to event calendar by date proximity

### Gold Layer (analytics-ready — 5 core tables)
- `gold_event_windows` — each historical event with full signal context across defined window
- `gold_content_metrics` — per-video compounding score, half-life estimate, earned reach
- `gold_market_signals` — daily engagement by language cohort
- `gold_commercial_indicators` — production-shaped business signals, temporally indexed
- `gold_competitor_context` — SOV data from YouTube for 5 competitor clubs

**All 5 views in the frontend read from these same 5 Gold tables. No view has its own data source. One spine, five lenses.**

---

## 10. Build Phases

### Phase 0 — Foundation (Days 1–5)
- Set up Databricks environment and medallion architecture
- Build Bronze ingestion for all data sources
- Build Silver transforms
- Produce all 5 Gold tables
- Validate data quality in notebooks before touching frontend
- MVP output: working pipeline only, no frontend

### Phase 1 — Analytical Engine (Days 6–18)
- Define event taxonomy (6 types: signing, trophy/win, rivalry, injury, kit launch, international break)
- Extract signal profile for each historical event across standard window
- Cluster events using DTW (dynamic time warping) for time series similarity
- Build archetype matching function with similarity scores and projected trajectory
- Compute all attention economy metrics for historical dataset
- MVP output: working archetype library, matching function, all metrics computed

### Phase 2 — Product Core (Days 19–32)
- Build React frontend with all 5 views
- Wire every view to Gold tables via FastAPI middleware
- Implement evidence vs simulation distinction throughout
- Build AI assistant with 20 pre-engineered questions
- MVP output: functional product end to end

### Phase 3 — Integration and Hardening (Days 33–40)
- End-to-end data spine test
- Archetype matching validation across edge cases
- AI assistant constrained to pre-engineered question space for demo
- Full demo scenario rehearsal from start to finish

### Phase 4 — Demo Preparation (Days 41–45+)
- Design demo scenario before the demo exists
- Rehearse complete story: intelligence surface → scenario simulator → attention health → recommendation
- Pitch opening presents a finding, not a product description

---

## 11. MVP vs Stretch

### MVP (must build)
- Databricks pipeline with 5 Gold tables
- Event archetype library with 12+ events across 6 types
- Scenario simulator with analog matching, projected trajectory, parameter adjustment
- Attention health view with at least 4 of 6 metrics
- Evidence vs simulation distinction enforced throughout
- Clean functional React frontend
- AI assistant handling 20 pre-engineered questions

### Stretch (build if time allows)
- Full 6-metric attention health suite including rivalry spillover and player dependence risk
- Driver decomposition in scenario simulator (which signals carry the most weight)
- Archetype library expanded to 20+ events
- AI assistant handling open-ended questions beyond pre-engineered set
- Executive briefing generator (one-page PDF summary)

---

## 12. Demo Scenario (Locked)

"Real Madrid is planning a signing announcement in three weeks. The commercial team wants to know how to time the content rollout and which markets to prioritise."

Walk through:
1. Intelligence surface shows a forming pattern
2. Scenario simulator finds three analog signings and projects the trajectory
3. Attention health shows Arabic market has current activation gap
4. Recommendation: announce mid-week, pre-stage Arabic-language content, expect 12–18 day engagement window based on analogs

---

## 13. Pitch Structure (Locked)

Opening line is a finding, not a product description:

"We found that Real Madrid's attention from a signing announcement decays 40% faster when the announcement competes with a rival's major event in the same week. Here is the platform we built to help the commercial team avoid that timing collision — and here are two other things we found in the data that nobody has quantified before."

Then present:
1. The specific finding
2. The evidence behind it
3. The product that finds more things like it
4. What the commercial team does differently on Monday morning

---

## 14. Three Questions This Product Answers

1. **What question does it answer?** Given what our social signals are showing right now, what is the historical business data telling us will happen next commercially — and what specific action should Real Madrid take?

2. **Why does that question matter commercially?** Real Madrid's commercial team currently reacts to demand after it peaks. Lead time on a commercial window is direct revenue — pre-positioned inventory, earlier campaign deployment, geo-targeted activation before the window closes.

3. **What does the data reveal?** Unknown until the analysis runs. This is the last remaining unknown and the most important one. The product concept is strong regardless. The specific surprising finding that makes judges lean forward lives in the data.

---

## 15. Open Questions That Must Be Answered Before Implementation

1. What exact fields does the production-shaped business data contain, at what granularity, covering what time period?
2. How many distinct major events with clean timestamps are in the data? If fewer than 15, archetype clusters will be thin.
3. Which YouTube channels does Real Madrid operate and are they accessible through standard Data API v3?
4. Is Reddit API sufficient for rivalry spillover and SOV calculations, or is another social source expected?
5. What is the exact presentation format — live product demo, slides, or both — and how long is the presentation slot?
6. Who on the team owns the pipeline, who owns the frontend, who owns the analytical engine?
7. Does the institution have any restrictions on third-party API usage or scraping for academic projects?
8. Are there any other groups also selecting Group E as their theme?

---

## 16. What Has Been Explicitly Ruled Out

| Idea | Reason Dropped |
|---|---|
| Minute-level commerce heatmaps | Requires granularity that won't be available |
| Exact revenue prediction as hero | Perturbed values don't justify high-precision claims |
| Generic content calendar optimizer | Commodity feature, already exists in standard tools |
| Sponsor exposure-to-engagement bridge | No sponsor-side data available |
| Fan acquisition cost calculator | No marketing spend data, denominator undefined |
| Bernabéu Effect digital amplifier | Requires user-level ticketing-digital data linkage |
| Generic pricing benchmark as main pillar | Too narrow, too easy to replicate, not novel enough |
| Raw share of voice charts | No clear commercial action derived from them |
| Black-box composite scores | Easy to dismiss under questioning; any score must be decomposable |

---

## 17. Honest Risk Assessment

**The idea is strong. The execution risk is real.**

The novelty lives in what the data actually reveals when the analysis runs. If the archetype matching produces thin clusters with wide confidence ranges, the simulator loses credibility. If the lag correlations between social signals and commercial indicators are weak, the core thesis weakens.

Mitigation: Be honest about confidence ranges throughout. Never claim precision that the data doesn't support. Frame everything as "historical patterns suggest" not "the model predicts." The transparent evidence layer is both a design choice and a credibility mechanism.

**The product concept survives even with thin data. A strong methodology demonstration with honest uncertainty is more impressive than a confident-looking output built on weak foundations.**
