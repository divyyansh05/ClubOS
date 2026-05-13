# ClubOS API Contract Overview

## MVP Endpoints

- `GET /health`
- `GET /health/summary`
- `GET /priorities/latest`
- `GET /priorities/{priority_id}`
- `GET /benchmark/{asset}/{metric}`
- `GET /signals`
- `GET /briefing/latest`
- `GET /refresh/status`

## Contract Principle

The API is a delivery layer over Gold outputs. It must not duplicate the analytical engine.

## Gold-to-API Mapping

- `GET /health/summary` -> `gold_kpi_health` (latest month aggregate summary only)
- `GET /priorities/latest` -> `gold_priority_board` (latest month ranked cards)
- `GET /priorities/{priority_id}` -> `gold_priority_board` (single row detail + parsed `supporting_metrics_json`)
- `GET /benchmark/{asset}/{metric}` -> `gold_peer_benchmark` (full monthly series for selected metric)
- `GET /signals` -> `gold_signal_relationships` (active validated signal rows returned as-is with typed fields)
- `GET /briefing/latest` -> `gold_monthly_brief_inputs` (latest monthly briefing payload)
- `GET /refresh/status` -> `silver_data_quality_checks` + `gold_kpi_health` (latest run status + latest Gold month)

## Service Boundary

- Backend is read-only and thin.
- Backend may parse JSON payload fields and shape response types.
- Backend must not recompute ranking/scoring/benchmark/signal logic that already exists in Gold.

## Connectivity Modes

- Preferred for development: snapshot mode via `CLUBOS_GOLD_SNAPSHOT_DIR` with exported table files.
- Optional for runtime: live Databricks SQL mode when host/token/http_path/catalog/schema env vars are configured.
