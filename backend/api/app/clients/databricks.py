import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from app.config.settings import settings


class SnapshotAccessError(RuntimeError):
    """Raised when snapshot/live data access is not available for API reads."""


class DatabricksClient:
    """
    Read-only data client for ClubOS.

    Access modes:
    - Snapshot mode (default): reads exported table snapshots from local files
    - Live mode (optional): queries Databricks SQL when connection env vars are set
    """

    def __init__(self, host: Optional[str], token: Optional[str]) -> None:
        self.host = host
        self.token = token
        self.http_path = settings.clubos_databricks_http_path
        self.catalog = settings.clubos_databricks_catalog
        self.schema = settings.clubos_databricks_schema
        self.snapshot_dir = settings.clubos_gold_snapshot_dir

    def _live_mode_enabled(self) -> bool:
        return bool(self.host and self.token and self.http_path and self.catalog and self.schema)

    def _snapshot_base_path(self, table_name: str) -> Path:
        if not self.snapshot_dir:
            raise SnapshotAccessError(
                "CLUBOS_GOLD_SNAPSHOT_DIR is not configured and live Databricks mode is unavailable. "
                "Set snapshot dir or Databricks SQL connection env vars."
            )
        return Path(self.snapshot_dir) / table_name

    def _read_snapshot(self, table_name: str) -> list[dict[str, Any]]:
        base_path = self._snapshot_base_path(table_name)
        candidates = [
            base_path.with_suffix(".json"),
            base_path.with_suffix(".csv"),
            base_path.with_suffix(".parquet"),
        ]

        for path in candidates:
            if not path.exists():
                continue

            if path.suffix == ".json":
                raw = path.read_text(encoding="utf-8").strip()
                if not raw:
                    return []
                if raw.startswith("["):
                    rows = json.loads(raw)
                    if not isinstance(rows, list):
                        raise RuntimeError(f"Invalid JSON structure in {path}; expected list.")
                    return [dict(r) for r in rows]
                return [json.loads(line) for line in raw.splitlines() if line.strip()]

            if path.suffix == ".csv":
                df = pd.read_csv(path)
                # Drop rows where all values are NaN
                df = df.dropna(how="all")
                # Convert to dict and filter out empty rows
                records = df.to_dict(orient="records")
                # Filter out rows where all values are None/NaN
                return [r for r in records if any(v is not None and str(v).strip() for v in r.values())]

            if path.suffix == ".parquet":
                return pd.read_parquet(path).to_dict(orient="records")

        raise SnapshotAccessError(
            f"Table snapshot not found for '{table_name}'. "
            f"Expected one of: {[str(p) for p in candidates]}"
        )

    def _read_live(self, table_name: str) -> list[dict[str, Any]]:
        try:
            from databricks import sql  # type: ignore
        except Exception as exc:
            raise SnapshotAccessError(
                "Live Databricks mode requested, but databricks-sql-connector is not installed."
            ) from exc

        full_table = f"{self.catalog}.{self.schema}.{table_name}"
        query = f"SELECT * FROM {full_table}"

        with sql.connect(
            server_hostname=self.host,
            http_path=self.http_path,
            access_token=self.token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in rows]

    def read_table(self, table_name: str) -> list[dict[str, Any]]:
        if self._live_mode_enabled():
            return self._read_live(table_name)
        return self._read_snapshot(table_name)

    def read_gold_table(self, table_name: str) -> list[dict[str, Any]]:
        return self.read_table(table_name)
