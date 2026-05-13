# ClubOS Backend API

This service exposes ClubOS Gold outputs to the frontend.

It should remain a delivery layer over Databricks outputs, not a second analytics engine.

## Install

From the repository root:

```bash
./scripts/bootstrap.sh
```

Or from this folder:

```bash
source ../../clubosvenv/bin/activate
pip install -r requirements.txt
```

Runtime standard:

- Python `3.11.x` only

Optional for live Databricks SQL mode:

```bash
pip install databricks-sql-connector==4.2.6
```

## Local Snapshot Mode (No Databricks Required)

Build API-ready snapshot tables directly from `data/source`:

```bash
./clubosvenv/bin/python scripts/build_local_snapshots.py \
  --source-dir data/source \
  --output-dir data/gold_snapshots
```

Start API against those snapshots:

```bash
./clubosvenv/bin/python -m uvicorn app.main:app --app-dir backend/api --reload --port 8000
```

By default, the API auto-detects `data/gold_snapshots` from the repository root.
Set `CLUBOS_GOLD_SNAPSHOT_DIR` only if your snapshots live in a different folder.
