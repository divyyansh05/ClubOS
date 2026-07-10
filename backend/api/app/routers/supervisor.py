from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from clubos2.supervisor.entry_point import SupervisorRequest, SupervisorResponse, handle_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai/supervisor", tags=["ai", "supervisor"])


class UnifiedQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    user_id: str | None = None


@router.post("/query", response_model=SupervisorResponse)
async def unified_query(request: UnifiedQueryRequest) -> SupervisorResponse:
    """Single entry point for all natural-language queries.

    Uses a deterministic classifier for obvious cases (fast path, zero LLM cost),
    and the LangGraph supervisor for complex or ambiguous queries.

    The `dispatch_path` field in the response indicates which route was taken:
    - `direct_scout` — simple metric question, answered by Scout directly
    - `direct_investigator` — explicit alert_id, routed straight to Investigator
    - `direct_briefer` — briefing/summary request, routed to Briefer
    - `langgraph_supervisor` — complex query handled by the multi-step supervisor
    - `error` — unhandled failure (check `error` field)
    """
    try:
        return await handle_query(SupervisorRequest(query=request.query, user_id=request.user_id))
    except Exception:
        logger.exception("Supervisor query endpoint failed")
        raise HTTPException(status_code=500, detail="Supervisor query failed")
