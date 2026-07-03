"""GoldClient — reads ClubOS metric values from v1's existing Gold CSV snapshots.

Phase 1 strategy: read DATA/gold_snapshots/*.csv directly with pandas.
This reuses the same data source v1 uses in dev mode — no duplicate Gold layer,
no drift between v1's and v2's view of the world.

Future migration path (Phase 2+):
    Implement DatabricksGoldClient subclass matching the same fetch_metric()
    signature. When deployed against the live Databricks SQL Warehouse, swap
    GoldClient for DatabricksGoldClient — no change to callers.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from pydantic_settings import BaseSettings

logger = logging.getLogger("clubos.tools.gold_client")

# Gold CSVs that contain per-metric values. Searched in priority order.
_METRIC_CSV_FILES = [
    "gold_kpi_health.csv",  # primary: per-metric rows with asset breakdown
    "gold_priority_board.csv",  # secondary: priority board with primary_metric column
]


class GoldClientSettings(BaseSettings):
    """Reads GOLD_SNAPSHOTS_DIR from environment, defaults to v1's DATA dir."""

    gold_snapshots_dir: str = "./data/gold_snapshots"

    model_config = {"env_file": ".env", "extra": "ignore"}


class MetricNotInGoldError(Exception):
    """Internal error: metric validated in registry but absent from Gold CSVs."""


class GoldClient:
    """Reads metric values from v1's existing gold_snapshots CSVs.

    Metric-name convention
    ----------------------
    The semantic_layer registry stores metric names in compound form:
        ``<asset_name>_<raw_metric_name>``
    e.g. ``streaming_daily_users``, ``ecommerce_net_sales``.

    gold_kpi_health.csv stores them split across two columns:
        asset_name = "streaming", metric_name = "daily_users"

    GoldClient splits on the first underscore that matches a known asset name
    to reconstruct the filter. If no known asset prefix matches, it falls back
    to a direct ``metric_name`` column match.
    """

    KNOWN_ASSETS = {"ecommerce", "streaming", "fan_app", "main_website", "social_media", "web"}

    def __init__(self, settings: GoldClientSettings | None = None) -> None:
        self.settings = settings or GoldClientSettings()
        self.gold_dir = Path(self.settings.gold_snapshots_dir)
        if not self.gold_dir.exists():
            raise FileNotFoundError(
                f"Gold snapshots directory not found at '{self.gold_dir}'. "
                "Run from repo root or set GOLD_SNAPSHOTS_DIR env var."
            )
        self._kpi_df: pd.DataFrame | None = None
        self._priority_df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def fetch_metric(
        self,
        metric_name: str,
        month: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch rows for a metric from Gold CSVs.

        Phase 1 strategy: try gold_priority_board.csv first (it has the 59 main metrics),
        then gold_kpi_health.csv. If found in neither, raise MetricNotInGoldError.
        """
        import json

        asset, raw_metric = self._split_metric_name(metric_name)

        # 1. Try gold_priority_board.csv first
        df_pb = self._load_priority_df()
        if asset:
            mask = (df_pb["asset_name"] == asset) & (df_pb["primary_metric"] == raw_metric)
        else:
            mask = df_pb["primary_metric"] == raw_metric

        filtered_pb = df_pb[mask].copy()

        if not filtered_pb.empty:
            source_file = "gold.priority_board"
            if month:
                filtered_pb = filtered_pb[filtered_pb["month"] == month]
                if filtered_pb.empty:
                    raise MetricNotInGoldError(
                        f"Metric '{metric_name}' found in gold_priority_board.csv "
                        f"but no row for month='{month}'."
                    )
            else:
                all_months = sorted(filtered_pb["month"].unique(), reverse=True)
                recent_months = all_months[:12]
                filtered_pb = filtered_pb[filtered_pb["month"].isin(recent_months)]

            filtered_pb = filtered_pb.sort_values("month", ascending=False)

            rows = []
            for _, row in filtered_pb.iterrows():
                try:
                    js_data = json.loads(row["supporting_metrics_json"])
                    sev_inputs = js_data.get("severity_inputs", {})
                except Exception:
                    sev_inputs = {}

                peer_ctx = js_data.get("peer_context") or {}
                rows.append(
                    {
                        "month": str(row["month"]),
                        "asset_name": str(row["asset_name"]),
                        "metric_name": str(row["primary_metric"]),
                        "metric_value": sev_inputs.get("metric_value", 0.0),
                        "trend_direction": sev_inputs.get("trend_direction", "flat"),
                        "health_status": sev_inputs.get("health_status", "stable"),
                        "deviation_from_rolling_avg": sev_inputs.get(
                            "deviation_from_rolling_avg", 0.0
                        ),
                        "seasonal_z_score": sev_inputs.get("seasonal_z_score", 0.0),
                        "prior_month_value": None,
                        "prior_season_same_month_value": None,
                        "rolling_12m_avg": None,
                        "source": source_file,
                        "compound_metric_name": metric_name,
                        "peer_rank": peer_ctx.get("peer_rank"),
                        "peer_club_count": peer_ctx.get("peer_club_count"),
                        "peer_gap_to_median": peer_ctx.get("gap_to_peer_median"),
                    }
                )
            return rows

        # 2. Fall back to gold_kpi_health.csv
        df_kh = self._load_kpi_df()
        if asset:
            mask = (df_kh["asset_name"] == asset) & (df_kh["metric_name"] == raw_metric)
        else:
            mask = df_kh["metric_name"] == raw_metric

        filtered_kh = df_kh[mask].copy()

        if filtered_kh.empty:
            raise MetricNotInGoldError(
                f"Metric '{metric_name}' (asset={asset!r}, raw={raw_metric!r}) "
                f"not found in gold_priority_board.csv or gold_kpi_health.csv."
            )

        source_file = "gold.metrics_monthly"
        if month:
            filtered_kh = filtered_kh[filtered_kh["month"] == month]
            if filtered_kh.empty:
                raise MetricNotInGoldError(
                    f"Metric '{metric_name}' found in Gold but no row for month='{month}'."
                )
        else:
            all_months = sorted(filtered_kh["month"].unique(), reverse=True)
            recent_months = all_months[:12]
            filtered_kh = filtered_kh[filtered_kh["month"].isin(recent_months)]

        filtered_kh = filtered_kh.sort_values("month", ascending=False)

        rows = filtered_kh.to_dict(orient="records")
        for row in rows:
            row["source"] = source_file
            row["compound_metric_name"] = metric_name

        return rows  # type: ignore[no-any-return]

    def list_available_metrics(self) -> dict[str, str]:
        """Return ``{compound_metric_name: source_csv}`` for every metric in Gold.

        Used by MetricNotFoundError for "did you mean" suggestions.
        """
        result: dict[str, str] = {}

        # 1. Add metrics from gold_kpi_health.csv
        df_kh = self._load_kpi_df()
        source_kh = str(self.gold_dir / "gold_kpi_health.csv")
        for _, row in df_kh[["asset_name", "metric_name"]].drop_duplicates().iterrows():
            compound = f"{row['asset_name']}_{row['metric_name']}"
            result[compound] = source_kh

        # 2. Update/Overwrite with metrics from gold_priority_board.csv (giving them priority)
        df_pb = self._load_priority_df()
        source_pb = str(self.gold_dir / "gold_priority_board.csv")
        for _, row in df_pb[["asset_name", "primary_metric"]].drop_duplicates().iterrows():
            compound = f"{row['asset_name']}_{row['primary_metric']}"
            result[compound] = source_pb

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_kpi_df(self) -> pd.DataFrame:
        """Load gold_kpi_health.csv, cached for the lifetime of this GoldClient."""
        if self._kpi_df is None:
            path = self.gold_dir / "gold_kpi_health.csv"
            logger.info("Loading Gold KPI data from '%s' ...", path)
            self._kpi_df = pd.read_csv(str(path), low_memory=False)
            logger.info("Loaded %d rows from gold_kpi_health.csv.", len(self._kpi_df))
        return self._kpi_df

    def _load_priority_df(self) -> pd.DataFrame:
        """Load gold_priority_board.csv, cached for the lifetime of this GoldClient."""
        if self._priority_df is None:
            path = self.gold_dir / "gold_priority_board.csv"
            logger.info("Loading Gold Priority Board data from '%s' ...", path)
            self._priority_df = pd.read_csv(str(path), low_memory=False)
            logger.info("Loaded %d rows from gold_priority_board.csv.", len(self._priority_df))
        return self._priority_df

    def _split_metric_name(self, metric_name: str) -> tuple[str | None, str]:
        """Split compound metric name into (asset_name, raw_metric_name).

        Strategy: try each known asset name as a prefix.
        Returns (None, metric_name) if no known asset prefix matches.

        Examples:
            "streaming_daily_users"  → ("streaming", "daily_users")
            "ecommerce_net_sales"    → ("ecommerce", "net_sales")
            "fan_app_matchday_visits"→ ("fan_app", "matchday_visits")
            "net_sales"              → (None, "net_sales")   # fallback
        """
        # Sort assets longest-first so "fan_app" is tried before "fan"
        for asset in sorted(self.KNOWN_ASSETS, key=len, reverse=True):
            prefix = asset + "_"
            if metric_name.startswith(prefix):
                raw = metric_name[len(prefix) :]
                return asset, raw
        # Also try asset as suffix (e.g. conversion_rate_ecommerce → ecommerce asset)
        for asset in sorted(self.KNOWN_ASSETS, key=len, reverse=True):
            suffix = "_" + asset
            if metric_name.endswith(suffix):
                raw = metric_name[: -len(suffix)]
                return asset, raw
        # No known asset prefix or suffix — try direct match
        return None, metric_name


@lru_cache(maxsize=1)
def get_gold_client() -> GoldClient:
    """Module-level singleton. Cached so the CSV is only loaded once per process."""
    return GoldClient()
