# Databricks Workspace Assets

This folder contains the data platform side of ClubOS.

It is organized by medallion stage and supporting assets:

- `notebooks/bronze/`
- `notebooks/silver/`
- `notebooks/gold/`
- `notebooks/analytics/`
- `notebooks/quality/`
- `sql/`
- `jobs/`
- `seeds/`

The target behavior is a recurring monthly refresh path:

1. ingest
2. normalize
3. validate
4. publish Gold outputs
