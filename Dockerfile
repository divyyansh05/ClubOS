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

# System deps for pandas/numpy if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (cached layer — rarely changes)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Backend application
COPY backend/ ./backend/

# Gold snapshots only — NOT data/source/ (too large, not needed)
COPY data/gold_snapshots/ ./data/gold_snapshots/

# Metric dictionary and scoring config
COPY databricks/seeds/ ./databricks/seeds/

# React build output from Stage 1
COPY --from=frontend /build/dist ./apps/clubos-web/dist

# Environment
ENV PYTHONPATH=/app
ENV CLUBOS_SNAPSHOT_DIR=/app/data/gold_snapshots
ENV CLUBOS_FRONTEND_DIST=/app/apps/clubos-web/dist
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Cloud Run injects PORT — read it at startup
CMD ["sh", "-c", \
     "uvicorn backend.api.app.main:app \
      --host 0.0.0.0 \
      --port ${PORT:-8080} \
      --workers 1"]
