# Bronze & Silver Logic Documentation

This document explicitly defines what the ingestion and normalization pipelines accomplish in Databricks for ClubOS.

## Bronze Ingestion
**Notebooks**: `01_ingest_internal_metrics.py`, `02_ingest_benchmark_metrics.py`

### What it does:
- Directly reads the `.xlsx` files sheet by sheet (using spark-excel format).
- Attaches the raw `source_file_name` and `ingestion_timestamp` columns to preserve data provenance.
- Overwrites the corresponding Bronze tables so each monthly payload acts as a complete refresh.

### Tables Generated:
- `clubos_bronze.bronze_internal_main_website`
- `clubos_bronze.bronze_internal_ecommerce`
- `clubos_bronze.bronze_internal_streaming`
- `clubos_bronze.bronze_internal_fan_app`
- `clubos_bronze.bronze_benchmark_main_website`
- `clubos_bronze.bronze_benchmark_ecommerce`
- `clubos_bronze.bronze_benchmark_streaming`
- `clubos_bronze.bronze_benchmark_fan_app`

## Silver Normalization
**Notebooks**: `01_normalize_internal_metrics.py`, `02_normalize_benchmark_metrics.py`

### What it does:
- Enforces `DateType` on the `month` column.
- Casts all column headers to `snake_case`.
- Drops raw generic dimensions (`active_type`, `digital_active`) in favor of standardizing hardcoded canonical `asset_name` and `asset_type` to guarantee stable downstream grouping regardless of slight source adjustments.
- **Enforces a strict approved metric allowlist**: Any extra unapproved columns silently appearing in new uploads are ignored and not unpivoted. This guarantees that garbage columns do not poison the downstream analytics layer.
- Implements the unpivot structure. The schema calls for a normalized long fact table (`silver_internal_asset_metrics` and `silver_benchmark_asset_metrics`) where metrics are stacked for clean analytical reading. Wide tables for internal assets are also created for backup/easy joins.
- Preserves monthly alignment keys (`month`, `asset_name`, `metric_name`) so Gold can safely join internal Real Madrid metrics to benchmark peer distributions without treating any benchmark row as a client proxy.

### Bug Fixes enforced in Silver:
- Mapped `%android` to `pct_android` gracefully.
- Mapped `otherl_traffic_plays` to `other_traffic_plays`.
- Handled the Benchmarking Streaming naming bug: `digital_active` in the Excel showed `main_website` instead of `streaming`. This is bypassed successfully by explicitly returning standard string bounds (`asset_name = 'streaming'`).

### Tables Generated:
- `clubos_silver.silver_internal_main_website` (Wide structure)
- `clubos_silver.silver_internal_ecommerce` (Wide structure)
- `clubos_silver.silver_internal_streaming` (Wide structure)
- `clubos_silver.silver_internal_fan_app` (Wide structure)
- `clubos_silver.silver_internal_asset_metrics` (Normalized long fact table)
- `clubos_silver.silver_benchmark_asset_metrics` (Normalized long fact table)

## Quality Validations
**Notebook**: `01_run_data_quality_checks.py`

### What it does:
- Programatically checks condition expressions for completeness over the Silver tables.
- Validates that `month` and `metric_value` are not logically NULL.
- Ensures the 5-club benchmark minimum remains respected across all active months.
- Appends log run outputs to `clubos_silver.silver_data_quality_checks`.

### Remaining Assumptions:
- Uses `spark-excel` format as the standard. If Databricks standard nodes do not have this library installed out of the box, an unzipping wrapper must be added or they must be saved down to `.csv` manually prior to Spark session loads. 
- The schema currently writes out to managed Delta tables via `saveAsTable`. The pattern dictates standard overwrites in Bronze/Silver but allows quality checks to append logs contextually in Silver.
