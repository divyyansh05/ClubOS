from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.clients.databricks import SnapshotAccessError
from app.routers import analytics, benchmark, briefing, events, health, priorities, refresh, signals, social

app = FastAPI(title="ClubOS API", version="0.1.0")

# CORS middleware to allow frontend (localhost:5174, 5176, 5177) to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:5176", "http://127.0.0.1:5176", "http://localhost:5177", "http://127.0.0.1:5177"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(priorities.router, prefix="/priorities", tags=["priorities"])
app.include_router(benchmark.router, prefix="/benchmark", tags=["benchmark"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(briefing.router, prefix="/briefing", tags=["briefing"])
app.include_router(refresh.router, prefix="/refresh", tags=["refresh"])
app.include_router(analytics.router, prefix="/analytics/seasonal", tags=["analytics"])
app.include_router(social.router, prefix="/social", tags=["social"])


@app.exception_handler(SnapshotAccessError)
def snapshot_access_error_handler(_: Request, exc: SnapshotAccessError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error_code": "snapshot_unavailable",
            "message": str(exc),
        },
    )
