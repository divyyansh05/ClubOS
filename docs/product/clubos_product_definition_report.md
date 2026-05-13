# ClubOS Product Definition Report

## Executive Summary

This document defines the final product direction for the Real Madrid internship project as a SaaS-grade internal product, not as a one-off dashboard.

The product is **ClubOS**, a monthly digital business operating system for elite football clubs. It is designed to ingest recurring monthly digital business datasets, standardize them through a Databricks pipeline, and produce a repeatable decision workflow for club business teams.

ClubOS is built around one core promise:

**When the next month of data arrives, the system automatically tells the club what changed, what matters, how it compares to peers, and what deserves attention next.**

This is the difference between a project and a product. The current files are the first operating snapshot. The product is designed so that the same workflow continues every time the next monthly files are uploaded.

The primary value is not better charts. The primary value is a recurring decision system for digital and commercial leadership.

## 1. Strategic Context

Real Madrid's official brief asks for a digital analytics visualization tool built on Databricks, with a visualization layer and optional AI-based insight support. That brief is the formal assignment baseline.

The opportunity is larger than the brief.

The provided datasets show that the club tracks four digital businesses over 103 months:

- main website
- eCommerce
- streaming
- fan app

There is also a peer benchmark dataset with selected metrics for five competitor clubs across the same monthly period.

This creates the basis for a more serious product:

- recurring monthly data intake
- standardized KPI calculation
- cross-asset business intelligence
- peer benchmarking
- ranked priorities for the digital and commercial teams

Therefore, the correct product framing is not "visualization tool" but **digital business operating system**.

## 2. Product Definition

### 2.1 Product Name

**ClubOS**

Subtitle:

**A monthly digital business operating system for elite football clubs**

### 2.2 Product Category

Internal SaaS / decision-support platform for club business teams.

### 2.3 Product Promise

ClubOS turns recurring monthly digital business files into an always-updated decision system that:

- shows the health of the club's digital businesses
- benchmarks selected KPIs against peer clubs
- detects the internal signals that matter most commercially
- ranks the issues and opportunities that deserve attention next

### 2.4 Product Principle

**Same app, same workflow, new data in, new business answers out.**

The app is not tied to this specific static snapshot. It is designed to keep working as future versions of the same monthly files are uploaded.

## 3. The Business Problem

### 3.1 What the club says it needs

The club states that analysts currently work from spreadsheets and spend significant effort manually reviewing, comparing, and summarizing historical digital data.

### 3.2 What the deeper business problem actually is

The real business problem is broader:

- four digital businesses are reviewed separately instead of as one system
- peer comparison exists but is not operationalized into a recurring decision process
- analysts spend time retrieving and formatting data instead of prioritizing action
- leadership lacks one recurring monthly view of what matters most
- potentially useful leading signals are buried inside disconnected asset-level reporting

### 3.3 Why generic dashboards are not enough

A generic dashboard answers:

- what happened
- what changed
- what the charts look like

ClubOS must answer:

- what changed this month that matters
- where Real Madrid is ahead or behind peers
- which signals are likely to matter commercially
- what the team should investigate first

That is an operating product, not a reporting surface.

## 4. Users And Jobs To Be Done

### 4.1 Primary Users

- Digital business lead
- Commercial lead
- Digital analyst

### 4.2 Secondary Users

- Marketing lead
- eCommerce manager
- Streaming/content lead
- Presentation and reporting stakeholders

### 4.3 Core Jobs To Be Done

For the digital business lead:

- understand overall digital health in one place
- know where the club is outperforming or underperforming peers
- know what deserves attention first this month

For the commercial lead:

- identify which digital behaviors tend to precede stronger or weaker commercial outcomes
- understand whether current issues are temporary or persistent
- see which gaps are most commercially important

For the analyst:

- reduce time spent manually producing monthly reports
- use one system to refresh benchmark and business views after each data upload
- generate structured monthly summaries and evidence packs

## 5. Data Foundation

### 5.1 Data Assumption

The current files are treated as the first delivery of a recurring monthly data feed.

The product is built on the assumption that future files will preserve the same broad structure:

- monthly cadence
- same digital assets
- same or similar schemas
- same benchmark logic on the peer file

### 5.2 Current Data Assets

Internal dataset:

- Main Website
- eCommerce
- Streaming Website
- Fan App

Benchmark dataset:

- selected monthly metrics for five peer clubs:
  - masia_fc
  - merseyside_red
  - gunners_fc
  - fc_baviera
  - citizens

### 5.3 Important Constraint

The data is monthly, not daily.

This means ClubOS must produce:

- monthly health views
- monthly trend diagnostics
- 1-3 month signal relationships
- month-level pre/post event analysis

It should not pretend to support:

- daily action timing
- short-window campaign optimization
- precise day-level prediction

### 5.4 Benchmark Coverage Reality

The peer benchmark layer is valuable but selective.

Benchmark-supported metrics currently include:

- Main Website:
  - unique_visitors
  - visits
  - bounce_rate
  - recurrence
- eCommerce:
  - unique_visitors
  - visits
  - conversion_rate
  - cart_value
- Streaming:
  - unique_visitors
  - daily_users
  - streamers_rate
  - video_play_rate
- Fan App:
  - unique_visitors
  - visits
  - matchday_visits
  - app_downloads
  - recurrence
  - heavy_users
  - user_rating

This constraint should shape product design. ClubOS should benchmark only what the benchmark file actually supports.

## 6. Product Value Proposition

### 6.1 Immediate Value To Real Madrid

ClubOS gives Real Madrid:

- one recurring monthly operating view across all four digital businesses
- peer comparison on selected normalized KPIs
- transparent ranked priorities instead of disconnected charts
- a faster analyst workflow after each monthly data upload

### 6.2 Why This Is More Valuable Than A Static Dashboard

The product is built to keep working every month, not just to demonstrate historical insight once.

The recurring value loop is:

1. upload new month
2. pipeline validates and recalculates
3. benchmark and signal layers refresh
4. Priority Board updates
5. monthly briefing is generated
6. teams act on the outputs

### 6.3 Why This Can Become A SaaS Product

The product is modular and repeatable:

- common data contract
- recurring refresh cycle
- reusable benchmark model
- reusable scoring logic
- role-based monthly workflow

With broader market adoption, the peer benchmark layer could become the basis of a larger club intelligence network. That is a future commercial thesis, not the MVP promise.

## 7. Product Modules

ClubOS should be built around five core product modules.

### 7.1 Module 1: Command Center

Purpose:

- provide one monthly operating view across the club's four digital businesses

Core outputs:

- health status of each asset
- trend versus seasonal expectation
- trend versus prior month and prior season
- key benchmark status where available

What this module is:

- the front door of the product
- the first screen leadership opens

What it is not:

- the main product differentiator

### 7.2 Module 2: Peer Benchmark Engine

Purpose:

- show where Real Madrid stands against peer clubs on the benchmark-supported KPIs

Core outputs:

- current rank
- gap versus peer median
- 12-month gap movement
- divergence points
- resilience comparison on shared shocks such as COVID

Why it matters:

- peer context is one of the strongest commercial value layers in the current data

### 7.3 Module 3: Commercial Signal Engine

Purpose:

- detect which internal digital signals tend to precede stronger or weaker commercial performance

Focus:

- eCommerce net_sales
- eCommerce conversion_rate
- subscriptions or growth-related asset metrics where appropriate

Core outputs:

- 2-3 stable leading indicators
- direction of relationship
- lag window in months
- plain-English interpretation

Important rule:

- only retain signal relationships that are stable, explainable, and repeatable

### 7.4 Module 4: Event Intelligence Lab

Purpose:

- add football-native context by showing how the club's digital ecosystem behaved around major known events

Inputs:

- manually annotated event timeline

Core outputs:

- pre/post event asset response
- cross-asset response order
- peer comparison for shared or similar event classes where possible

Role in the product:

- evidence layer
- context layer
- trust-building layer

### 7.5 Module 5: Priority Board

Purpose:

- rank the issues and opportunities that deserve attention first

This is the product hero.

It is the feature that moves ClubOS from analytics tool to operating system.

Each priority card should answer:

- what is happening
- why it matters
- how severe it is
- whether it is persistent
- whether peers outperform Real Madrid
- which supporting signals confirm the issue
- which team should investigate it

## 8. The Hero Product Capability: Priority Board

### 8.1 Why This Is The Hero

Senior leadership does not buy a dashboard because it has better charts.

They buy a system that helps them focus.

The Priority Board should be the core reason to use ClubOS every month.

### 8.2 Priority Scoring Logic

Each priority should be scored using transparent components:

- **Severity**
  - how far the metric is from its seasonal norm
- **Persistence**
  - how many consecutive months the signal has remained weak or strong
- **Peer Gap**
  - how far Real Madrid is from peer median or top peer, where benchmark exists
- **Commercial Weight**
  - how close the metric is to commercial value such as sales, conversion, or subscription
- **Supporting Evidence**
  - whether related metrics reinforce the same story

### 8.3 Example Priority Cards

- eCommerce conversion has underperformed peer median for four straight months
- streaming engagement is rising, but subscription conversion is not following
- fan app heavy users are weakening while matchday visits remain high
- website traffic remains strong, but recurrence is slipping versus seasonal norm

### 8.4 What Makes It Credible

Every priority card must include:

- the score
- the reason for the score
- the metrics used
- the peer context if available
- the trend window considered
- a plain-English suggested next investigation

This should be rules-based first, with AI used only for explanation.

## 9. KPI Framework

### 9.1 MVP KPI Set

The MVP should use a limited KPI set that is strong enough to support the core modules.

Recommended KPI set:

- Main Website:
  - unique_visitors
  - visits
  - bounce_rate
  - recurrence
- eCommerce:
  - net_sales
  - conversion_rate
  - cart_value
  - checkout_rate
- Streaming:
  - subscriptions
  - subscription_rate
  - streamers_rate
  - video_play_rate
- Fan App:
  - app_downloads
  - matchday_visits
  - heavy_users
  - recurrence

### 9.2 KPI Classes

- **Health KPIs**
  - what is happening now
- **Benchmark KPIs**
  - how Real Madrid compares to peers
- **Signal KPIs**
  - what tends to move before commercial outcomes
- **Evidence KPIs**
  - what supports a ranked priority

## 10. Monthly Product Workflow

The recurring operating workflow should be:

1. New monthly data files are uploaded
2. Databricks validates file structure and schema
3. Bronze layer stores raw inputs
4. Silver layer standardizes and cleans data
5. Gold layer recalculates KPIs, peer gaps, signal outputs, and priority scores
6. Command Center refreshes
7. Priority Board refreshes
8. Monthly briefing refreshes
9. Users review top issues and drill into evidence

This recurring workflow is what makes ClubOS SaaS-shaped.

## 11. Product Outputs After Each Monthly Refresh

Every monthly refresh should produce the same structured outputs:

- updated health overview
- updated benchmark positions
- updated leading signal diagnostics
- updated priority ranking
- updated event-aware context, where relevant
- updated monthly business briefing

The outputs should not depend on custom manual storytelling. They should be system-generated from stable logic.

## 12. Analytics Logic

### 12.1 Benchmark Logic

For benchmark-supported metrics, ClubOS should calculate:

- current rank among the six clubs
- peer median
- gap to peer median
- gap trend
- momentum of rank movement

### 12.2 Signal Logic

For internal cross-asset analysis, ClubOS should test 1-3 month lag relationships only.

The target is not high-complexity prediction.

The target is:

- defensible pattern recognition
- stable lead indicators
- plain-English business interpretation

### 12.3 Event Logic

Event analysis should use manually curated football and business milestones, such as:

- COVID
- major signings
- major exits
- trophy moments

The product should analyze month-level pre/post windows, not daily tactical timing.

### 12.4 AI Logic

AI should be used only to:

- summarize what happened
- explain why a priority is ranked highly
- generate a monthly business briefing

AI should not be used as the core logic for ranking or scoring.

## 13. User Experience Principles

ClubOS should feel operational, not exploratory.

### 13.1 UX Rules

- the homepage must start with ranked priorities, not a gallery of charts
- every visual must answer a business question
- every score must be decomposable
- every recommendation must show supporting evidence
- the product must reduce decision overload, not create it

### 13.2 Page Flow

Recommended page structure:

1. **Priority Board**
   - top 5 issues and opportunities
2. **Priority Detail**
   - supporting metrics, benchmark status, and signal logic
3. **Peer Benchmark**
   - rank, gap, divergence, resilience
4. **Command Center**
   - overall monthly digital health
5. **Event Intelligence**
   - historical context and shock response
6. **Monthly Briefing**
   - AI-generated summary for business leadership

## 14. Technical Architecture

### 14.1 Data Platform

- Databricks Free Edition
- Delta Lake
- Unity Catalog
- Python / PySpark
- notebooks for transformation and analytical logic

### 14.2 Data Layers

**Bronze**

- raw uploaded files
- file metadata
- ingestion logs

**Silver**

- standardized monthly data
- cleaned schemas
- validated metric values
- consistent asset naming
- event annotation joins

**Gold**

Recommended MVP gold tables:

- `gold_kpi_health`
- `gold_peer_benchmark`
- `gold_signal_relationships`
- `gold_priority_board`
- `gold_event_windows`
- `gold_monthly_brief_inputs`

### 14.3 Product Layer

Primary:

- React web app

Secondary:

- Tableau dashboards connected to the same Gold tables for traditional metric deep dives

### 14.4 Why Tableau Still Matters

Tableau is not the hero product.

It is the support layer that satisfies the base visualization ask and provides familiar metric drill-down capability.

ClubOS remains the strategic product.

## 15. Implementation Strategy

### 15.1 Build Principle

Build proof before polish.

The team should prove:

1. the data contract
2. the benchmark layer
3. the top 2-3 leading signals
4. the Priority Board logic

Only then should the UI be expanded.

### 15.2 Recommended Build Order

1. metric inventory and feature dependency map
2. data cleaning and schema validation
3. gold benchmark table
4. signal testing for leading indicators
5. priority scoring logic
6. minimal React shell
7. benchmark and priority views
8. event layer
9. AI summaries
10. Tableau support layer

### 15.3 MVP Boundary

The MVP should include:

- recurring monthly ingestion pipeline
- benchmark engine on supported KPIs
- 2-3 validated leading indicators
- operational Priority Board
- Command Center
- one event intelligence view
- one monthly briefing view

The MVP should not depend on:

- open-ended AI chat
- overly complex scenario simulation
- unsupported benchmark claims
- heavy visual experimentation before proof is established

## 16. Commercial Positioning

### 16.1 Why A Club Would Care

Clubs care about:

- analyst time
- peer position
- commercial performance
- leadership focus

ClubOS addresses all four.

### 16.2 Why A Club Would Buy

The most buyable version of ClubOS is not:

- "look at our charts"

It is:

- "this system gives your business team one monthly operating workflow across your digital ecosystem"

### 16.3 Why It Is Stronger Than Generic BI

Generic BI tools can show charts.

ClubOS combines:

- normalized monthly benchmark context
- cross-asset business signal logic
- ranked business priorities
- event-aware football context
- recurring monthly workflow

That combination is the commercial differentiator.

## 17. Risks And Mitigations

### 17.1 Risk: Weak or unstable signal relationships

Mitigation:

- keep only 2-3 stable indicators
- avoid overclaiming prediction
- frame outputs as evidence-backed patterns

### 17.2 Risk: Benchmark coverage is narrower than expected

Mitigation:

- benchmark only supported KPIs
- keep benchmark engine as one product module, not the whole thesis

### 17.3 Risk: Product feels like a dashboard again

Mitigation:

- put Priority Board first
- keep workflow operational
- make every page answer "what matters next"

### 17.4 Risk: AI becomes gimmicky

Mitigation:

- use AI for explanation only
- keep all critical logic deterministic and inspectable

## 18. Definition Of Success

ClubOS is successful if:

- a new monthly file can be uploaded without redesigning the app
- the system recalculates the same outputs each month
- the digital team can see peer position quickly
- the commercial team can see what deserves attention first
- analysts spend less time producing manual summaries
- leadership feels the product is operational, not just analytical

## 19. Final Product Thesis

ClubOS is a recurring monthly digital business operating system for football clubs.

It uses Databricks to convert recurring digital business files into:

- a unified monthly health view
- benchmarked peer intelligence
- evidence-backed commercial signal detection
- ranked business priorities
- structured monthly briefings

The product is designed to work not only on the current dataset, but on future deliveries of the same data structure.

That is what makes it a real SaaS-shaped product rather than a one-time internship dashboard.
