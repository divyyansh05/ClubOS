# ClubOS Environment Setup Guide

This guide explains how to configure ClubOS for local development with Databricks connectivity and snapshot fallback.

## Quick Start

1. **Copy the example file:**
   ```bash
   cp backend/api/.env.example .env
   ```

2. **Fill in your Databricks credentials:**
   Get values from your `~/.databrickscfg` profile:
   ```bash
   cat ~/.databrickscfg
   ```

3. **Start the API:**
   ```bash
   source clubosvenv/bin/activate
   python -m uvicorn app.main:app --app-dir backend/api --reload
   ```

## Configuration Options

### Required for Live Databricks Mode

| Variable | Source | Description |
|----------|--------|-------------|
| `CLUBOS_DATABRICKS_HOST` | `~/.databrickscfg` → `host` | Databricks workspace URL (e.g., `https://dbc-xxxx.cloud.databricks.com`) |
| `CLUBOS_DATABRICKS_TOKEN` | `~/.databrickscfg` → `token` | Personal access token for authentication |
| `CLUBOS_DATABRICKS_HTTP_PATH` | SQL Warehouse | Path to your SQL warehouse (format: `/sql/1.0/warehouses/warehouse-id`) |

### Optional for Catalog/Schema Selection

| Variable | Description |
|----------|-------------|
| `CLUBOS_DATABRICKS_CATALOG` | Specific catalog to use (if not set, uses workspace default) |
| `CLUBOS_DATABRICKS_SCHEMA` | Specific schema to use (if not set, uses workspace default) |

### Optional: Local Snapshot Mode

| Variable | Description | Default |
|----------|-------------|---------|
| `CLUBOS_GOLD_SNAPSHOT_DIR` | Path to Gold snapshot CSV/Parquet/JSON files | `data/gold_snapshots` (auto-detected) |

When this is set, the API reads from local files instead of Databricks SQL. **This is the recommended development mode when you don't have live Databricks credentials.**

### API Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CLUBOS_API_HOST` | `0.0.0.0` | Listening host for FastAPI server |
| `CLUBOS_API_PORT` | `8000` | Listening port for FastAPI server |

### Optional: AI Integration

| Variable | Description |
|----------|-------------|
| `CLUBOS_AI_PROVIDER` | AI provider name (e.g., `openai`, `anthropic`) |
| `CLUBOS_AI_API_KEY` | API key for the chosen AI provider |

## How to Get Your Databricks Credentials

### From CLI Profile

If you authenticated with Databricks CLI (`databricks auth` or `databricks configure --token`):

```bash
# View your profile
cat ~/.databrickscfg

# Example output:
# [DIv-RE-Internship]
# host = https://dbc-2893ab0c-78f7.cloud.databricks.com
# token = dapi1234567890...
```

### SQL Warehouse HTTP Path

1. Go to your Databricks workspace
2. Navigate to **SQL** → **SQL Warehouses**
3. Find your warehouse and click on it
4. Copy the **Warehouse ID** from the URL or details page
5. Format as: `/sql/1.0/warehouses/{warehouse-id}`

## Connection Modes

### Mode 1: Live Databricks (Recommended for Production)

Set `CLUBOS_DATABRICKS_HOST`, `CLUBOS_DATABRICKS_TOKEN`, and `CLUBOS_DATABRICKS_HTTP_PATH`.

API will query Databricks SQL for every request.

### Mode 2: Local Snapshot (Recommended for Development)

Leave Databricks env vars empty or unset. API will auto-detect and read from `data/gold_snapshots`.

This mode requires pre-built snapshot tables. Generate them:

```bash
python scripts/build_local_snapshots.py \
  --source-dir data/source \
  --output-dir data/gold_snapshots
```

### Mode 3: Profile-Based (Profile + Serverless Compute)

Databricks SDK will auto-detect credentials from `~/.databrickscfg` if env vars are missing.

Leave Databricks env vars empty and set `DATABRICKS_SERVERLESS_COMPUTE_ID=auto` for serverless execution.

## Troubleshooting

### Error: `snapshot_unavailable`

**Cause:** Neither Databricks credentials nor local snapshots are available.

**Fix:** 
- Set `CLUBOS_DATABRICKS_HOST` and `CLUBOS_DATABRICKS_TOKEN`, OR
- Run `build_local_snapshots.py` to generate CSV/Parquet files

### Error: `DATABRICKS_TOKEN` rejected / 401 Unauthorized

**Cause:** Token is invalid or expired.

**Fix:**
- Re-generate token in Databricks workspace (User Settings → Access Tokens)
- Update `.env` with new token

### Error: SQL warehouse is stopped

**Cause:** The SQL warehouse specified in `CLUBOS_DATABRICKS_HTTP_PATH` is not running.

**Fix:**
- Start the warehouse in Databricks UI, OR
- Use a different running warehouse, OR
- Switch to local snapshot mode for development

## File Locations

- `.env` (project root) — **Loaded by settings.py; git-ignored**
- `backend/api/.env.example` — **Template; safe to commit**
- `~/.databrickscfg` — **Your local Databricks profile (never commit)**
- `data/gold_snapshots/` — **Local snapshot files (generated; git-ignored)**

## Environment Variable Precedence

1. Explicit env vars in `.env` file (highest priority)
2. System environment variables (e.g., `export CLUBOS_DATABRICKS_HOST=...`)
3. Databricks SDK profile detection (`~/.databrickscfg`)
4. Defaults in `backend/api/app/config/settings.py` (lowest priority)

---

**Next:** See [backend/api/README.md](../backend/api/README.md) for API setup and usage.
