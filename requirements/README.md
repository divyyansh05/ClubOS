# Python Requirements

This folder provides pinned Python dependencies for ClubOS.

## Files

- `base.txt` -> core runtime and shared data tooling
- `dev.txt` -> local development and test tooling
- `databricks-local.txt` -> optional local Spark support for Databricks-like experimentation

## Recommended Install

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/dev.txt
```

If you want local Spark support:

```bash
pip install -r requirements/databricks-local.txt
```

Optional live Databricks SQL connector:

```bash
pip install databricks-sql-connector==4.2.6
```
