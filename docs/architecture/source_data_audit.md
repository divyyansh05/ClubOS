# Source Data Audit

## Overview
This document records an audit of the provided Real Madrid monthly data deliveries (Excel workbooks) against the established data contracts and Databricks schema plans.

**Date of Audit**: April 2026
**Data Covered**: July 2017 to January 2026 (103 months)

## 1. Internal Metrics Workbook
**File**: `Tema5.internal_metrics.dataset.xlsx`

### Sheets and Grain
- **Info**: 75 rows. Contains metric definitions.
- **Main_Website**: 103 rows. One row per month.
- **eCommerce**: 103 rows. One row per month.
- **Streaming_Website**: 103 rows. One row per month.
- **Fan_App**: 103 rows. One row per month.

### Source Inconsistencies and Issues
- **Streaming_Website**: The raw file contains a field named `otherl_traffic_plays` (typo for "other_traffic" or similar). This will need to be mapped properly in the Silver layer without breaking Bronze ingestion.
- **Fan_App**: The raw file contains the field `%android`. The schema plan suggested `pct_android`. The Bronze ingestion must accept `%android` and standardize to `pct_android` in Silver.
- **Columns not fully defined in contract**: The source Excel files contain many extended dimensions (e.g., `international_visits`, `marketing_visits`, `logged_users`, `session_time_avg`) that were previously missing from the initial `internal_metrics_contract.md`. These will be ingested into Bronze but not all are needed for MVP.

## 2. Benchmark Workbook
**File**: `Tema5.benchmark.dataset.xlsx`

### Sheets and Grain
- **Info**: 75 rows.
- **Main_Website**: 515 rows (5 clubs × 103 months).
- **eCommerce**: 515 rows. 
- **Streaming**: 515 rows. 
- **Fan_App**: 515 rows. 

### Source Inconsistencies and Issues
- **Streaming Sheet naming bug**: In the Streaming sheet, the `digital_active` column contains the value `main_website` instead of `streaming`. However, the `active_type` column correctly says `streaming`. The Silver layer must detect this and override `digital_active` to `streaming` to join properly.
- **Limited supported metrics**: The benchmark file does NOT support all the KPIs that the internal file does. For example, there's no `bounce_rate` or `page_views` for Fan_App, no `items` or `checkout_rate` for eCommerce, and no engagement volume like `video_plays` for Streaming (only rates). 

## 3. Benchmark Limitations & Capabilities
- **What the data CAN support**: 
  - Gap comparisons and rankings at the monthly grain. 
  - Core MVP KPIs (unique visitors, visits, conversion rates, and app usage metrics).
- **What the data CANNOT support**:
  - Anything more granular than monthly (no weekly or daily reporting).
  - Absolute revenue comparisons or raw sales counts for peers.
  - Streaming absolute volumes for peers.
  - Granular marketing/traffic-source benchmarking across peers (only internal traffic sources are available). 

## Conclusion
The files confirm that the foundation is stable enough for the ClubOS monthly workflow. The schema design mapping Bronze to these exact structures and correcting column names in Silver is fully supported by the audit.
