# ClubOS Scripts

## discover_gold_metrics.py

Scans Gold-layer CSV files and prints a JSON array of all metric compound names.

```bash
python scripts/discover_gold_metrics.py > docs/gold_metrics_inventory.json
```

Run this whenever Gold files change (new platform added, new metric column). The output feeds the CI coverage test.

## diff_gold_vs_registry.py

Compares the Gold inventory against `metric_registry`. Reports which registry metrics fail to resolve to Gold data via GoldClient.

```bash
python scripts/diff_gold_vs_registry.py
```

Writes `docs/registry_gap_analysis.json`.

---

# Scheduled Scripts

## scheduled_monthly_briefing.py

Runs the Briefer for the previous complete calendar month. Designed for cron invocation on the 1st of each month.

**What it does:**
- Computes the previous complete calendar month automatically (no arguments needed)
- Calls `run_briefing` with `triggered_by="scheduled_cron"`
- Returns the cached briefing if one already exists within the freshness window (idempotent)
- Exits 0 on success (generated or cached), 1 on failure

**Example crontab entry:**
```
0 6 1 * * cd /path/to/clubos && /path/to/venv/bin/python scripts/scheduled_monthly_briefing.py >> /var/log/clubos_monthly.log 2>&1
```

**Production deployment:** in GCP Cloud Run, wrap this in a Cloud Scheduler job that hits
`POST /api/ai/briefer/run_monthly` instead of invoking the script directly. The API
endpoint has the same dedup behavior.

**Idempotent:** running it twice on the same day is safe — the second call returns the cached
briefing with no LLM cost.

---

## v2_demo_phase3.sh / v2_demo_phase4.sh

End-to-end demonstration scripts for Phase 3 (Watchdog) and Phase 4 (Investigator). Run from
the project root after starting the backend.

---

## v2_ci_gate.py

CI eval gate. Runs the golden-set eval and fails if any metric regresses below the baseline in
`eval/reports/baseline.json`. Called by `make v2-eval-ci`.
