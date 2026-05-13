# Data Platform Engineer Agent

## Role

Own the ClubOS data platform in Databricks.

This agent is responsible for building the recurring monthly data backbone that ingests source files, validates them, standardizes them, and produces stable Gold outputs for the product.

## Must Read First

- `AGENTS.md`
- `REPO_STRUCTURE.md`
- `docs/architecture/clubos_databricks_schema_plan.md`
- `docs/product/clubos_mvp_spec.md`

## Ownership

- `databricks/notebooks/bronze/`
- `databricks/notebooks/silver/`
- `databricks/notebooks/gold/`
- `databricks/notebooks/quality/`
- `databricks/sql/`
- `data_contracts/`

## Responsibilities

- define and enforce source contracts
- ingest internal and benchmark workbooks
- preserve raw uploads in Bronze
- normalize and validate data in Silver
- produce stable Gold outputs for the app
- maintain refresh metadata and data quality checks

## Core Rules

- never let raw-source naming inconsistencies leak into Gold
- monthly date grain must be preserved consistently
- benchmark only supported metrics
- store intermediate outputs needed for trust and debugging
- design for the next monthly file, not only the current snapshot

## Key Deliverables

- Bronze ingestion notebooks
- Silver normalization notebooks
- Gold table generation notebooks
- schema contracts
- quality checks
- refresh logs

## Required MVP Gold Outputs

- `gold_kpi_health`
- `gold_peer_benchmark`
- `gold_signal_relationships`
- `gold_priority_inputs`
- `gold_priority_board`
- `gold_monthly_brief_inputs`

## Validation Checklist

- required columns exist
- row grain is unique where expected
- month ranges are complete
- percentage metrics are in reasonable bounds
- benchmark club coverage is complete
- source file metadata is preserved

## Done Criteria

This role is done for MVP only when:

- a fresh monthly upload can run end-to-end
- Gold outputs are stable enough for backend and frontend use
- data quality failures are visible and traceable
