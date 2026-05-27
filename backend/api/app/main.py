import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Startup debugging
print(f"[STARTUP] Python version: {sys.version}", flush=True)
print(f"[STARTUP] Current working directory: {os.getcwd()}", flush=True)
print(f"[STARTUP] PYTHONPATH: {sys.path}", flush=True)
print(f"[STARTUP] PORT env var: {os.environ.get('PORT', 'NOT SET')}", flush=True)
print(f"[STARTUP] CLUBOS_SNAPSHOT_DIR: {os.environ.get('CLUBOS_SNAPSHOT_DIR', 'NOT SET')}", flush=True)
print(f"[STARTUP] CLUBOS_FRONTEND_DIST: {os.environ.get('CLUBOS_FRONTEND_DIST', 'NOT SET')}", flush=True)

from app.clients.databricks import SnapshotAccessError
from app.routers import analytics, benchmark, briefing, config, connectors, events, health, priorities, refresh, signals, social, notifications

print("[STARTUP] All imports successful", flush=True)

app = FastAPI(title="ClubOS API", version="0.1.0")

print("[STARTUP] FastAPI app created", flush=True)

# CORS middleware (configure with CLUBOS_CORS_ORIGINS env var or default to *)
_cors_origins = os.getenv("CLUBOS_CORS_ORIGINS", "*")
_origins_list = (
    ["*"] if _cors_origins == "*"
    else [o.strip() for o in _cors_origins.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", include_in_schema=False)
def health_check():
    return {"status": "ok", "mode": "snapshot"}


app.include_router(health.router)
app.include_router(priorities.router, prefix="/priorities", tags=["priorities"])
app.include_router(benchmark.router, prefix="/benchmark", tags=["benchmark"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(briefing.router, prefix="/briefing", tags=["briefing"])
app.include_router(refresh.router, prefix="/refresh", tags=["refresh"])
app.include_router(analytics.router, prefix="/analytics/seasonal", tags=["analytics"])
app.include_router(social.router, prefix="/social", tags=["social"])
app.include_router(connectors.router, prefix="/api", tags=["connectors"])
app.include_router(notifications.router, prefix="/api")
app.include_router(config.router, tags=["config"])


@app.exception_handler(SnapshotAccessError)
def snapshot_access_error_handler(_: Request, exc: SnapshotAccessError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error_code": "snapshot_unavailable",
            "message": str(exc),
        },
    )


# ── Production static file serving ──────────────────────
_DIST = os.getenv(
    "CLUBOS_FRONTEND_DIST",
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "apps", "clubos-web", "dist"
        )
    )
)

if os.path.isdir(_DIST):
    _assets = os.path.join(_DIST, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets",
                  StaticFiles(directory=_assets),
                  name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _serve_spa(request: Request, full_path: str):
        target = os.path.join(_DIST, full_path)
        if os.path.isfile(target):
            return FileResponse(target)
        return FileResponse(os.path.join(_DIST, "index.html"))
# ────────────────────────────────────────────────────────
