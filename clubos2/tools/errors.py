"""Error types for ClubOS tool calls.

Keeping errors in a separate module prevents circular imports between
registry.py (which raises them) and any module that catches them.
"""

from __future__ import annotations


class MetricNotFoundError(Exception):
    """Raised when query_metrics is called with an unknown metric name.

    Carries two suggestion lists so callers can craft helpful messages:
    - suggestions_from_registry: close matches from the semantic layer registry
      (metric may exist conceptually but be named differently)
    - suggestions_from_gold: metrics that DO exist in the Gold CSVs but have
      no registry entry (governance gap — a human needs to define them)

    This split is intentional: a metric can exist in the registry but be
    missing from Gold (data gap), or exist in Gold but not the registry
    (governance gap). The error message surfaces both.
    """

    def __init__(
        self,
        metric_name: str,
        suggestions_from_registry: list[str],
        suggestions_from_gold: list[str],
    ) -> None:
        self.metric_name = metric_name
        self.suggestions_from_registry = suggestions_from_registry
        self.suggestions_from_gold = suggestions_from_gold
        registry_hint = ", ".join(suggestions_from_registry[:3]) or "(no close matches)"
        gold_hint = ", ".join(suggestions_from_gold[:3]) or "(none)"
        super().__init__(
            f"Metric '{metric_name}' not in semantic_layer registry. "
            f"Did you mean: {registry_hint}? "
            f"Or in Gold but unregistered: {gold_hint}"
        )
