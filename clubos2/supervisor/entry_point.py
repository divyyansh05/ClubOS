from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta

from pydantic import BaseModel

from clubos2.briefer.agent_schemas import BriefingInput, BriefingType
from clubos2.observability.tracing import get_current_langsmith_trace_url, traced
from clubos2.supervisor.classifier import AgentType, ClassificationResult, classify_query

logger = logging.getLogger(__name__)


class SupervisorRequest(BaseModel):
    query: str
    user_id: str | None = None


class SupervisorResponse(BaseModel):
    query: str
    classification: dict
    dispatch_path: str  # 'direct_scout' / 'direct_investigator' / 'direct_briefer' / 'langgraph_supervisor'
    result: dict
    latency_seconds: float
    trace_url: str | None
    error: str | None


def _infer_briefing_input_from_query(query: str, classification: ClassificationResult) -> BriefingInput:
    """Best-effort inference of briefing scope from query text."""
    now = datetime.utcnow()

    if re.search(r"last month", query, re.I):
        first_of_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_of_prev = first_of_this - timedelta(seconds=1)
        first_of_prev = last_of_prev.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return BriefingInput(
            briefing_type=BriefingType.MONTHLY_SCHEDULED,
            scope_key=f"monthly:{first_of_prev.strftime('%Y-%m')}",
            period_start=first_of_prev,
            period_end=last_of_prev,
            triggered_by="supervisor:query_inferred",
        )

    # Default: this month so far
    first_of_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return BriefingInput(
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key=f"monthly:{first_of_this.strftime('%Y-%m')}",
        period_start=first_of_this,
        period_end=now,
        triggered_by="supervisor:query_inferred",
    )


@traced(name="supervisor:handle_query", run_type="chain")
async def handle_query(request: SupervisorRequest) -> SupervisorResponse:
    """Unified entry point for all natural-language queries.

    Step 1: deterministic classifier (zero LLM cost).
    Step 2: direct dispatch if high/medium confidence.
    Step 3: fall through to LangGraph supervisor for complex/ambiguous queries.
    """
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput
    from clubos2.briefer.orchestrator import run_briefing
    from clubos2.supervisor.graph import SupervisorState, build_supervisor_graph

    started_at = time.perf_counter()
    classification = classify_query(request.query)

    try:
        # --- Direct Scout ---
        if classification.agent == AgentType.SCOUT and classification.confidence in ("high", "medium"):
            answer = await run_scout(ScoutInput(question=request.query))
            return SupervisorResponse(
                query=request.query,
                classification=classification.model_dump(),
                dispatch_path="direct_scout",
                result=answer.model_dump(mode="json"),
                latency_seconds=time.perf_counter() - started_at,
                trace_url=get_current_langsmith_trace_url(),
                error=None,
            )

        # --- Direct Investigator (only when alert_id extracted, high confidence) ---
        if classification.agent == AgentType.INVESTIGATOR and classification.confidence == "high":
            alert_id = classification.extracted_params.get("alert_id")
            if alert_id:
                from clubos2.investigator.orchestrator import run_investigation
                from clubos2.investigator.agent_schemas import InvestigatorInput
                from clubos2.watchdog.alerts_repo import AlertsRepository

                alerts_repo = AlertsRepository()
                alert = await alerts_repo.get_by_id(alert_id)
                if alert:
                    inv_result = await run_investigation(InvestigatorInput(
                        alert_id=alert_id,
                        metric_name=alert.metric_name,
                        triggered_by=f"supervisor:{request.user_id or 'unknown'}",
                    ))
                    return SupervisorResponse(
                        query=request.query,
                        classification=classification.model_dump(),
                        dispatch_path="direct_investigator",
                        result=inv_result.model_dump(mode="json"),
                        latency_seconds=time.perf_counter() - started_at,
                        trace_url=get_current_langsmith_trace_url(),
                        error=None,
                    )
            # No alert_id or alert not found → fall through to LangGraph

        # --- Direct Briefer ---
        if classification.agent == AgentType.BRIEFER and classification.confidence == "high":
            brf_input = _infer_briefing_input_from_query(request.query, classification)
            brf_result = await run_briefing(brf_input)
            return SupervisorResponse(
                query=request.query,
                classification=classification.model_dump(),
                dispatch_path="direct_briefer",
                result=brf_result.model_dump(mode="json"),
                latency_seconds=time.perf_counter() - started_at,
                trace_url=get_current_langsmith_trace_url(),
                error=None,
            )

        # --- LangGraph supervisor (complex / ambiguous / low confidence) ---
        graph = build_supervisor_graph()
        initial_state: SupervisorState = {
            "user_query": request.query,
            "messages": [],
            "plan": None,
            "step_index": 0,
            "step_results": [],
            "final_synthesis": None,
            "finished": False,
        }
        final_state = await graph.ainvoke(initial_state)
        return SupervisorResponse(
            query=request.query,
            classification=classification.model_dump(),
            dispatch_path="langgraph_supervisor",
            result={
                "plan": final_state.get("plan"),
                "step_results": final_state.get("step_results"),
                "final_synthesis": final_state.get("final_synthesis"),
            },
            latency_seconds=time.perf_counter() - started_at,
            trace_url=get_current_langsmith_trace_url(),
            error=None,
        )

    except Exception as e:
        logger.exception(f"Supervisor failed for query: {request.query!r}")
        return SupervisorResponse(
            query=request.query,
            classification=classification.model_dump(),
            dispatch_path="error",
            result={},
            latency_seconds=time.perf_counter() - started_at,
            trace_url=get_current_langsmith_trace_url(),
            error=str(e),
        )
