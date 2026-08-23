from __future__ import annotations

import logging
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# These are the v2 imports — proves the v1 backend can reach v2 code cleanly
from clubos2.agents.scout import run_scout
from clubos2.agents.scout_schemas import ScoutInput, ScoutAnswer
from clubos2.observability.tracing import get_current_langsmith_trace_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])


class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    session_id: str | None = None
    user_id: str | None = None


class AIQueryResponse(BaseModel):
    answer: str
    citations: list[dict]
    confidence: str
    assumptions_made: list[str]
    metrics_queried: list[str]
    chunks_retrieved: int
    trace_url: str | None
    latency_ms: int


@router.post("/query", response_model=AIQueryResponse)
async def query_scout(request: AIQueryRequest) -> AIQueryResponse:
    """
    ClubOS 2.0 Scout — grounded natural-language Q&A over club metrics and knowledge.
    Phase 1 endpoint. Auth and rate-limiting are deferred to Phase 6.
    """
    # TODO Phase 6: add auth and rate limiting before exposing publicly
    start = time.perf_counter()
    try:
        scout_input = ScoutInput(**request.model_dump())
        answer: ScoutAnswer = await run_scout(scout_input)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return AIQueryResponse(
            answer=answer.answer,
            citations=[c.model_dump() for c in answer.citations],
            confidence=answer.confidence.value,
            assumptions_made=answer.assumptions_made,
            metrics_queried=answer.metrics_queried,
            chunks_retrieved=answer.chunks_retrieved,
            trace_url=get_current_langsmith_trace_url(),
            latency_ms=latency_ms,
        )
    except Exception:
        # Log full detail server-side; return generic error to client
        logger.exception("Scout query failed", extra={"question_preview": request.question[:80]})
        raise HTTPException(status_code=500, detail="Internal error processing AI query")
