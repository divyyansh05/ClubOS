# ─────────────────────────────────────────
# Stage 1 — Build React frontend
# ─────────────────────────────────────────
FROM node:20-slim AS frontend

WORKDIR /build

# Install deps (separate layer for caching)
COPY apps/clubos-web/package.json \
     apps/clubos-web/package-lock.json* \
     ./
RUN npm ci --silent

# Copy source
COPY apps/clubos-web/ ./

# .env.production sets VITE_API_BASE_URL=""
# Vite picks it up automatically during build
RUN npm run build

# ─────────────────────────────────────────
# Stage 2 — Python backend + data + frontend
# ─────────────────────────────────────────
FROM python:3.11-slim AS production

WORKDIR /app

# System deps for pandas/numpy + sqlite (for LangGraph checkpointer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

# ── v1 Python dependencies (cached layer — rarely changes) ──────────────────
COPY requirements/base.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ── CPU-only PyTorch (installed FIRST, before v2-runtime) ──────────────────
# sentence-transformers (via chromadb / rag reranker) transitively pulls torch.
# Without this pre-install, pip resolves to GPU-enabled torch + CUDA libs
# (~900 MB). We only need CPU inference in Cloud Run — this cuts image size
# by ~700 MB and speeds Docker builds by ~5x.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch

# ── v2 Python dependencies (langchain, langgraph, chromadb, duckdb, etc.) ──
# Installed via pyproject.toml optional group [v2-runtime] to keep the group
# definition single-sourced. Own layer for build caching.
COPY pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e ".[v2-runtime]"

# Backend application (v1)
COPY backend/ ./backend/

# Connectors and integrations
COPY integrations/ ./integrations/

# ── v2 packages ─────────────────────────────────────────────────────────────
COPY clubos2/ ./clubos2/
COPY eval/ ./eval/
COPY prompts/ ./prompts/
COPY scripts/ ./scripts/

# Gold snapshots (data source for both v1 and v2)
COPY data/gold_snapshots/ ./data/gold_snapshots/

# Metric dictionary and scoring config
COPY databricks/seeds/ ./databricks/seeds/

# React build output from Stage 1
COPY --from=frontend /build/dist ./apps/clubos-web/dist

# Environment
# PYTHONPATH: /app first so `clubos2.*` and `eval.*` resolve; backend/api second
# so `app.*` imports keep working.
ENV PYTHONPATH=/app:/app/backend/api
ENV CLUBOS_SNAPSHOT_DIR=/app/data/gold_snapshots
ENV CLUBOS_FRONTEND_DIST=/app/apps/clubos-web/dist
ENV GOLD_SNAPSHOTS_DIR=/app/data/gold_snapshots
ENV CHROMA_PERSIST_DIR=/app/var/chroma
ENV SEMANTIC_DB_URL=duckdb:////app/var/clubos_semantic.duckdb
ENV WEB_SEARCH_PROVIDER=none
ENV SCOUT_PROMPT_VERSION=v6
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ── Bake seeded state into the image ────────────────────────────────────────
# Runs bootstrap_db + registry seed at build time. RAG ingest is skipped here
# (needs OPENAI_API_KEY, which is a runtime secret) — it runs on first cold
# start via the FastAPI lifespan handler.
RUN mkdir -p /app/var && python /app/scripts/startup_init.py

EXPOSE 8080

# Set working directory to backend/api to match local behavior
WORKDIR /app/backend/api

# Verify directory structure
RUN echo "=== Verifying container structure ===" && \
    ls -la /app/ && \
    echo "=== v2 packages ===" && \
    ls -d /app/clubos2 /app/eval /app/prompts && \
    echo "=== Seeded state ===" && \
    ls -la /app/var/ 2>/dev/null || echo "(no var/ yet)" && \
    echo "=== Backend directory ===" && \
    ls -la /app/backend/api/app/ && \
    echo "=== Frontend dist ===" && \
    ls -la /app/apps/clubos-web/dist/ && \
    echo "=== Verification complete ==="

# Cloud Run injects PORT — read it at startup
CMD ["sh", "-c", \
     "echo 'Starting uvicorn...' && \
      uvicorn app.main:app \
      --host 0.0.0.0 \
      --port ${PORT:-8080} \
      --workers 1 \
      --log-level debug"]
