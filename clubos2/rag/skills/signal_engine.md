# Signal Engine

## Purpose
The Signal Engine page displays validated leading indicator relationships between digital metrics, helping management anticipate shifts in business outcomes. It answers the core business question: "Which digital leading indicators statistically predict changes in our primary commercial outcomes (like net sales or streaming subscriptions) several months in advance, and what is the strength and lag of these prediction patterns?"

## Metrics on this screen
- `unique_visitors_web`
- `net_sales`

## Valid queries
- "What leading indicators predict eCommerce net sales?"
- "Which digital signals have a 2-month lag?"
- "Show me the strongest validated correlation signals."
- "How does website traffic affect eCommerce sales over time?"
- "What is the correlation coefficient of the web-to-sales signal?"
- "List the validated temporal lag relationships."

## Invalid queries
- "How many web visitors did we have in November?" (Requires Command Center or Priority Board detail view)
- "What is Masia FC's organic search visits?" (Requires Peer Benchmark screen)
- "What are our critical priorities for this month?" (Requires Priority Board screen)

## Known gotchas
- Three validation gates: For a signal relationship to be published and displayed, it must pass three strict criteria:
  1. Statistical strength: Pearson correlation coefficient $r \ge 0.60$.
  2. Temporal precedence: A lag of 1 to 3 months (the cause must precede the effect).
  3. Commercial logic: A sound business explanation connecting the metrics (no spurious correlations).
- An example is `unique_visitors_web` leading `net_sales` by a 2-month lag with a 69% ($r = 0.69$) correlation.
- Correlation is not immediate: The temporal lag is a physical customer behavior delay. Do not conflate same-month correlation with validated leading signal lags.

## Stakeholder language
- Stakeholders say "leading indicator" or "forward signals" → we mean the Signal Engine.
- Stakeholders say "visitor-to-cash delay" or "sales delay" → we mean the temporal lag of the signal.
- Stakeholders say "predictive metrics" → we mean validated signal relationships.

## What the Scout should NEVER do with this screen
- Never project future metric values or invent correlations not explicitly calculated in the database.
- Never bypass the three validation gates or report unvalidated correlations.
- Never assume a temporal lag implies a direct causal guarantee without stating the statistical correlation bounds.

## References
- Gold table: `gold_signal_relationships`
- Design doc: [signal_validation_logic.md](file:///Users/divyanshshrivastava/RE%20Internship%20project/docs/architecture/signal_validation_logic.md)
- Metric registry: `metric_registry` table
