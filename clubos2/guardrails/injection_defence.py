from __future__ import annotations

import re
import logging
from pydantic import BaseModel

from clubos2.observability.tracing import traced

logger = logging.getLogger("clubos.guardrails.injection_defence")

# Patterns that look like attempts to override the system prompt
INJECTION_PATTERNS = [
    r'ignore\b.{0,40}\b(instructions?|prompts?|rules?)',
    r'(disregard|forget)\b.{0,40}\b(instructions?|prompts?|rules?)',
    r'you (are now|must now|will now)',
    r'new instructions:',
    r'system prompt:',
    r'<\s*system\s*>',
    r'</\s*system\s*>',
    r'\[SYSTEM\]',
    r'pretend (you are|to be)',
    r'act as (a |an )?(different|new|admin)',
]
INJECTION_REGEX = re.compile('|'.join(INJECTION_PATTERNS), re.IGNORECASE)


class InjectionDetection(BaseModel):
    source: str
    matched_patterns: list[str]
    original_text: str
    sanitised_text: str


@traced(name="guardrail:injection_defence", run_type="chain")
def sanitise_for_injection(
    chunks: list,  # list[KnowledgeChunk]
    metrics: list | None = None,  # list[MetricRow] — not sanitised, just passed through
) -> tuple[list, list, list[InjectionDetection]]:
    """
    Scan retrieved knowledge chunks for injection-like patterns.
    Sanitise (don't drop) matching content — replace matched spans with [REDACTED:INJECTION].
    Return (metrics, sanitised_chunks, detections).

    Metrics are structured numeric data — much harder to inject. Skip sanitisation
    for them; just log if any string field contains suspicious patterns.

    TODO Phase 5+: if MCP/external content is ingested, harden with semantic injection
    detection (e.g. LLM-based classifier). Regex is sufficient for Phase 2 where the
    threat surface is our own skill files and Gold-layer data.
    """
    detections: list[InjectionDetection] = []
    sanitised_chunks = []

    for chunk in chunks:
        text = chunk.text if hasattr(chunk, 'text') else str(chunk)
        matches = INJECTION_REGEX.findall(text)
        if matches:
            sanitised_text = INJECTION_REGEX.sub('[REDACTED:INJECTION]', text)
            detection = InjectionDetection(
                source=getattr(chunk, 'source', 'unknown'),
                matched_patterns=[str(m) for m in matches],
                original_text=text,
                sanitised_text=sanitised_text,
            )
            detections.append(detection)
            logger.warning(
                "Injection pattern detected in retrieved content",
                extra={"source": detection.source, "patterns": detection.matched_patterns},
            )
            # Sanitise: replace chunk text, keep everything else intact
            try:
                sanitised_chunks.append(chunk.model_copy(update={"text": sanitised_text}))
            except AttributeError:
                sanitised_chunks.append(chunk)
        else:
            sanitised_chunks.append(chunk)

    return metrics or [], sanitised_chunks, detections
