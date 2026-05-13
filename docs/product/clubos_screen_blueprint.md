# ClubOS Screen-by-Screen Product Blueprint

## Purpose

This document defines the screen-level structure of ClubOS.

It should be used by design, frontend, and product logic work together so that:

- the app feels like a real operating product
- the pages reflect recurring monthly workflow
- the product emphasizes priorities over passive exploration

The blueprint is written at the level needed to build the MVP interface and demo flow.

## 1. Product Navigation

Recommended primary navigation:

1. Priority Board
2. Command Center
3. Peer Benchmark
4. Signal Engine
5. Monthly Briefing

Secondary or later:

6. Event Intelligence
7. Settings / Data Refresh

Priority Board must be the default landing page.

## 2. Screen 1: Priority Board

### Goal

Show the most important issues and opportunities for the latest month.

### Main User Question

What deserves attention first right now?

### Layout

#### Top Header

- product name: ClubOS
- selected reporting month
- last data refresh timestamp
- quick status badge:
  - healthy
  - warning
  - action needed

#### Top Summary Strip

Include 4 compact summary cards:

- number of critical priorities
- number of opportunities
- number of benchmark underperformances
- number of strong leading signals active

#### Main Body: Priority Cards

Show top 5 ranked cards.

Each card should include:

- title
- category
- priority score
- why this matters
- supporting KPIs
- peer context badge if relevant
- trend direction
- one suggested next investigation

Each card should have a CTA:

- `View evidence`

### Supporting Right Panel

Optional side panel:

- top benchmark change
- top anomaly
- top signal to watch

### Interaction

Clicking a card opens Priority Detail.

## 3. Screen 2: Priority Detail

### Goal

Explain why a priority is ranked highly and show the evidence chain.

### Main User Question

Why is this important, and what is the supporting evidence?

### Layout

#### Header

- priority title
- category
- current score
- reporting month

#### Section A: Score Breakdown

Show component breakdown:

- severity
- persistence
- peer gap
- commercial weight
- supporting evidence

Use a stacked bar or score decomposition display.

#### Section B: Historical Trend

Show:

- metric over time
- seasonal baseline
- current deviation highlight

#### Section C: Peer Evidence

Only if benchmark exists:

- current rank
- peer median gap
- 12-month rank movement

#### Section D: Related Signals

Show:

- supporting internal metrics
- whether signals are confirming or conflicting

#### Section E: Suggested Investigation

Show structured next step:

- what team should look at this
- what likely issue/opportunity type it represents
- what evidence supports that interpretation

This must remain grounded and not overstate certainty.

## 4. Screen 3: Command Center

### Goal

Provide a one-page monthly overview of all four digital businesses.

### Main User Question

How is the overall digital ecosystem performing this month?

### Layout

#### Top Row

4 business health cards:

- Main Website
- eCommerce
- Streaming
- Fan App

Each card should include:

- primary KPI
- change vs previous month
- change vs same month last season
- indicator vs seasonal expectation
- one-line status summary

#### Mid Section: Cross-Asset Overview

Show a matrix or compact network view indicating:

- where strong or weak movement is concentrated
- which assets are improving together
- which asset is most commercially exposed

Keep this high-level. Detailed logic belongs in Signal Engine.

#### Bottom Section: Monthly Notes

Show three compact blocks:

- biggest improvement
- biggest decline
- one thing to watch next month

### Interaction

Each asset card links to its corresponding evidence context or benchmark detail.

## 5. Screen 4: Peer Benchmark

### Goal

Show how Real Madrid compares with peer clubs on the selected benchmark-supported KPIs.

### Main User Question

Where are we ahead, where are we behind, and how is that changing?

### Layout

#### KPI Selector

Allow switching across benchmark-supported KPIs.

Suggested grouped categories:

- Website
- eCommerce
- Streaming
- Fan App

#### Main Panel A: Rank Snapshot

Show:

- current rank among six clubs
- current value
- peer median
- leader value

Use a rank bar or ranked card layout.

#### Main Panel B: Gap Trend

Line or band chart for:

- Real Madrid
- peer median
- leader

Highlight:

- widening gap
- narrowing gap
- crossover points

#### Main Panel C: Divergence Events

Show the months where the gap changed most sharply.

Each divergence event should include:

- month
- direction of change
- size of gap movement

#### Supporting Panel: Resilience View

For a selected shared shock such as COVID:

- show decline depth
- time to recovery
- peer comparison

This gives the benchmark screen an executive angle, not just a ranking angle.

## 6. Screen 5: Commercial Signal Engine

### Goal

Show the few internal signals that consistently matter most for commercial outcomes.

### Main User Question

Which digital behaviors tend to precede stronger or weaker commercial performance?

### Layout

#### Top Overview

List the 2-3 validated leading indicators.

Each signal card should include:

- source metric
- target metric
- lag window
- direction
- confidence label

#### Main Detail Area

When a signal is selected, show:

- source metric trend
- target metric trend shifted by lag
- signal explanation in plain English
- where this relationship held or broke

#### Supporting Section: Business Interpretation

Translate the signal into business meaning:

- why this matters
- what a rise or decline may indicate
- how it should be used in monthly planning

### Important UX Rule

This screen should feel evidence-based and calm, not flashy or magical.

## 7. Screen 6: Monthly Briefing

### Goal

Deliver a concise leadership-ready summary after each monthly data refresh.

### Main User Question

What happened this month that matters to leadership?

### Layout

#### Section A: Executive Summary

Short text block with:

- overall health statement
- biggest business concern
- biggest opportunity

#### Section B: Top 3 Priorities

Summarize the top three Priority Board cards.

#### Section C: Peer Position Summary

Short block on:

- best benchmark area
- worst benchmark area
- one notable benchmark movement

#### Section D: Signals And Watchlist

Short block on:

- strongest leading signal
- one thing to watch next month

#### Section E: Download / Export

Optional button:

- export summary for presentation or reporting use

## 8. Screen 7: Event Intelligence

This is stretch or phase-two depending on time.

### Goal

Add football-native historical context to the product.

### Main User Question

How did our digital ecosystem respond to major known events?

### Layout

#### Event Selector

Manual list of curated events:

- COVID
- major signings
- major exits
- trophy moments

#### Main Response View

Show month-level pre/post windows across the four assets.

#### Peer Comparison View

Only where credible:

- shared-shock comparison
- similar-event comparison

### UX Rule

This screen supports storytelling and trust. It should not dominate the MVP.

## 9. Global Interaction Patterns

### Filters

MVP filters should include:

- reporting month
- season
- digital asset
- benchmark KPI

Avoid overloading the product with too many filters.

### Tooltips

Every metric and score should have:

- short definition
- business interpretation

### Drill Path

Preferred drill path:

Priority Board -> Priority Detail -> supporting evidence module

This creates an operational workflow instead of random exploration.

## 10. Visual Language Principles

The interface should feel like a serious internal business product.

Recommended principles:

- strong hierarchy
- clean information density
- high-contrast KPI cards
- controlled use of emphasis colors for warnings and opportunities
- avoid generic “dashboard grid” feel
- use motion lightly and only to support transitions or focus

The most important thing is clarity, trust, and decision support.

## 11. Demo Flow

Recommended live demo flow:

1. Open Priority Board
2. Explain top-ranked issue or opportunity
3. Open Priority Detail and show score logic
4. Move to Peer Benchmark to show competitive context
5. Move to Signal Engine to show what tends to precede the outcome
6. End on Monthly Briefing to show the recurring leadership output

This flow demonstrates that ClubOS is a monthly operating system, not just a collection of pages.
