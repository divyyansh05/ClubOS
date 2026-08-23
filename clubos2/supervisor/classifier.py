from __future__ import annotations

import logging
import re
from enum import Enum
from functools import lru_cache

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    SCOUT = "scout"
    INVESTIGATOR = "investigator"
    BRIEFER = "briefer"
    UNKNOWN = "unknown"  # falls through to LangGraph supervisor


class ClassificationResult(BaseModel):
    agent: AgentType
    confidence: str  # 'high' / 'medium' / 'low'
    rule_matched: str | None
    reasoning: str
    extracted_params: dict = {}


# ---------------------------------------------------------------------------
# Rule tables — order matters: briefing > investigation > metric > shape
# ---------------------------------------------------------------------------

_BRIEFING_PATTERNS: list[tuple[str, str]] = [
    (r"\b(monthly briefing|monthly summary|month.{0,5} report)\b", "monthly_briefing_keyword"),
    (r"\b(summar(?:y|ise|ize).{0,20}(?:month|week|period))\b", "summary_of_period"),
    (r"\b(what happened.{0,20}(?:this month|last month|march|april|may|june|july|august|september|october|november|december))\b", "what_happened_period"),
    (r"\b(brief(?:ing)?\s+(?:me|us)\b)", "brief_me_keyword"),
    (r"\bbrief(?:ing)?\b", "brief_keyword"),
]

_INVESTIGATION_PATTERNS: list[tuple[str, str]] = [
    (r"\b(investigate|why did|why is|what caused)\b", "why_causal_keyword"),
    (r"\b(root cause|explain.{0,20}alert)\b", "root_cause_keyword"),
    (r"alrt_[a-f0-9]+", "explicit_alert_id"),
]

_SCOUT_SHAPE_PATTERNS: list[tuple[str, str]] = [
    (r"\b(what is|what was|what are|how much|how many)\b", "value_question_shape"),
    (r"\b(current|latest|most recent|this month)\b", "current_value_shape"),
]


@lru_cache(maxsize=1)
def _load_known_metric_names() -> list[str]:
    """Load metric names from the registry. Cached at first call."""
    try:
        import os
        import duckdb
        # SEMANTIC_DB_URL follows SQLAlchemy convention:
        #   duckdb:///relative/path      → 3 slashes, path is relative
        #   duckdb:////absolute/path     → 4 slashes, path is absolute
        # Strip 'duckdb:///' (3 chars after 'duckdb://') to get the raw path
        # duckdb.connect() understands.
        db_url = os.environ.get("SEMANTIC_DB_URL", "duckdb:///./var/clubos_semantic.duckdb")
        db_path = db_url[len("duckdb:///"):] if db_url.startswith("duckdb:///") else db_url
        conn = duckdb.connect(db_path, read_only=True)
        rows = conn.execute("SELECT metric_name FROM metric_registry").fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        logger.warning(f"Could not load metric registry for classifier: {e}")
        return []


def _extract_alert_id(query: str) -> str | None:
    m = re.search(r"alrt_[a-f0-9]+", query)
    return m.group(0) if m else None


def classify_query(query: str) -> ClassificationResult:
    """Classify a user query to the right agent using deterministic rules.

    Order: briefing patterns → investigation patterns → known metric match →
    question shape → UNKNOWN (falls through to LangGraph supervisor).

    Returns UNKNOWN generously — false positives (wrong agent) are worse than
    false negatives (deferring to supervisor).
    """
    q = query.strip().lower()

    # RULE 1 — Briefing requests
    for pattern, name in _BRIEFING_PATTERNS:
        if re.search(pattern, q):
            return ClassificationResult(
                agent=AgentType.BRIEFER,
                confidence="high",
                rule_matched=name,
                reasoning=f"Query matched briefing pattern: {name}",
                extracted_params={"raw_query": query},
            )

    # RULE 2 — Investigation requests
    for pattern, name in _INVESTIGATION_PATTERNS:
        m = re.search(pattern, q)
        if m:
            params: dict = {"raw_query": query}
            alert_id = _extract_alert_id(query)
            if alert_id:
                params["alert_id"] = alert_id
            return ClassificationResult(
                agent=AgentType.INVESTIGATOR,
                confidence="high" if params.get("alert_id") else "medium",
                rule_matched=name,
                reasoning=f"Query matched investigation pattern: {name}",
                extracted_params=params,
            )

    # RULE 3 — Known metric referenced (Scout, high confidence)
    known_metrics = _load_known_metric_names()
    for metric in known_metrics:
        # Match underscore form or space form
        if metric in q or metric.replace("_", " ") in q:
            return ClassificationResult(
                agent=AgentType.SCOUT,
                confidence="high",
                rule_matched="known_metric_referenced",
                reasoning=f"Query references known metric '{metric}'",
                extracted_params={"raw_query": query, "referenced_metric": metric},
            )

    # RULE 4 — Question shape suggesting Scout even without explicit metric
    for pattern, name in _SCOUT_SHAPE_PATTERNS:
        if re.search(pattern, q):
            return ClassificationResult(
                agent=AgentType.SCOUT,
                confidence="medium",
                rule_matched=name,
                reasoning=f"Query shape suggests Scout: {name}",
                extracted_params={"raw_query": query},
            )

    # RULE 5 — Fall through
    return ClassificationResult(
        agent=AgentType.UNKNOWN,
        confidence="low",
        rule_matched=None,
        reasoning="No deterministic rule matched with confidence — deferring to LangGraph supervisor",
        extracted_params={"raw_query": query},
    )
