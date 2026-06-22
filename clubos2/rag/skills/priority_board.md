# Priority Board

## Purpose
The Priority Board is the operational homepage of ClubOS. It displays a dynamically calculated, ranked list of monthly business priorities (critical issues and opportunities) across all digital platforms (eCommerce, Streaming, Social, Web, and Fan App). It answers the core business question: "Given the latest monthly data upload, what are the top 3-5 high-priority areas we must address immediately to maximize digital growth and mitigate operational risks?"

## Metrics on this screen
- `net_sales`
- `conversion_rate_ecommerce`
- `bounce_rate_web`

## Valid queries
- "What are our top priorities for this month?"
- "Which digital platforms have the highest priority score?"
- "Show me the critical opportunities on the Priority Board."
- "Why is eCommerce conversion rate marked as a high priority?"
- "What is the score breakdown of the number one priority?"
- "List the priority cards ranked by importance."

## Invalid queries
- "Which Instagram Reel had the highest view count last week?" (Requires Social Intelligence screen)
- "What is the two-month lag correlation between web visits and eCommerce sales?" (Requires Signal Engine screen)
- "Compare our eCommerce conversion rate directly with Masia FC's average." (Requires Peer Benchmark screen)

## Known gotchas
- January net sales post-holiday dip: eCommerce net sales always drop 12-18% in January following the holiday season. The system's seasonal Z-score scoring adjusts for this pattern automatically so that standard post-holiday sales drops are not flagged as crises. If you see `net_sales` ranked as the #1 priority in January, investigate whether the rolling-average calculation bug has returned.
- Fixed 5-component scoring weights: The Priority Score (0.00 to 1.00) is calculated using a fixed formula with weights: 30 (severity), 25 (persistence), 20 (peer gap), 15 (commercial weight), and 10 (supporting evidence). Do not attempt to dynamically recalculate or normalize these weights on a per-question basis.

## Stakeholder language
- Stakeholders say "priority list" or "what is on the agenda" → we mean the Priority Board.
- Stakeholders say "the conversion problem" → we mean `conversion_rate_ecommerce` (specifically when it displays a low score/high priority on the Board).
- Stakeholders say "sales drop" → we refer to the `net_sales` priority status.

## What the Scout should NEVER do with this screen
- Never invent a metric value or priority score not present in the registry or Gold layer tables.
- Never compute "what-if" projection scenarios (e.g. "What would our score be if sales rose 10%?"). The Investigator agent handles scenarios; the Scout only reports.
- Never rank metrics or priorities using any formula other than the existing 5-component priority score.

## References
- Gold table: `gold_priority_board`
- Design doc: [priority_board_logic.md](file:///Users/divyanshshrivastava/RE%20Internship%20project/docs/architecture/priority_board_logic.md)
- Metric registry: `metric_registry` table
