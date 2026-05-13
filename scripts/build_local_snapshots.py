#!/usr/bin/env python3
"""
Build local ClubOS snapshot tables from data/source Excel workbooks.

Outputs CSV snapshots consumable by backend/api snapshot mode:
- silver_data_quality_checks
- gold_kpi_health
- gold_peer_benchmark
- gold_signal_relationships
- gold_priority_board
- gold_monthly_brief_inputs
"""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


INTERNAL_FILE = "Tema5.internal_metrics.dataset.xlsx"
BENCHMARK_FILE = "Tema5.benchmark.dataset.xlsx"

INTERNAL_SHEETS = {
    "Main_Website": ("main_website", "web"),
    "eCommerce": ("ecommerce", "web"),
    "Streaming_Website": ("streaming", "streaming"),
    "Fan_App": ("fan_app", "app"),
}

BENCHMARK_SHEETS = {
    "Main_Website": ("main_website", "web"),
    "eCommerce": ("ecommerce", "web"),
    "Streaming": ("streaming", "streaming"),
    "Fan_App": ("fan_app", "app"),
}

INTERNAL_ALLOWLIST = {
    "unique_visitors", "visits", "page_views", "international_visits", "mobile_visits",
    "search_organic_visits", "social_organic_visits", "marketing_visits",
    "other_channels_visits", "consumption", "bounce_rate", "recurrence",
    "new_users", "logged_users", "purchases", "items", "net_sales",
    "search_organic_purchases", "social_organic_purchases", "marketing_purchases",
    "other_channels_purchases", "cart_value", "product_views_rate", "card_addition_rate",
    "checkout_rate", "conversion_rate", "daily_users", "video_plays", "streamers",
    "subscriptions", "search_organic_plays", "social_organic_plays", "marketing_plays",
    "other_traffic_plays", "subscription_rate", "streamers_rate", "video_recurrence",
    "video_play_rate", "video_progress_25_rate", "video_progress_50_rate",
    "video_progress_75_rate", "video_complete_rate", "app_downloads", "matchday_visits",
    "pct_android", "organic_launch_visits", "app_push_visits", "deeplink_visits",
    "other_channel_visits", "session_time_avg", "heavy_users", "user_rating",
}

BENCHMARK_ALLOWLIST = {
    "unique_visitors", "visits", "bounce_rate", "recurrence",
    "conversion_rate", "cart_value", "daily_users", "streamers_rate",
    "video_play_rate", "app_downloads", "matchday_visits", "heavy_users", "user_rating",
}

BENCHMARK_POLARITY = {
    "unique_visitors": 1,
    "visits": 1,
    "bounce_rate": -1,
    "recurrence": 1,
    "conversion_rate": 1,
    "cart_value": 1,
    "daily_users": 1,
    "streamers_rate": 1,
    "video_play_rate": 1,
    "matchday_visits": 1,
    "app_downloads": 1,
    "heavy_users": 1,
    "user_rating": 1,
}

METRIC_POLARITY = {
    "bounce_rate": -1,
}


def _clean_column_name(name: str) -> str:
    cleaned = name.strip().lower().replace(" ", "_").replace(".", "_")
    if cleaned == "%android":
        cleaned = "pct_android"
    if cleaned == "otherl_traffic_plays":
        cleaned = "other_traffic_plays"
    return cleaned


def _read_excel_long(
    workbook_path: Path,
    sheets_map: Dict[str, Tuple[str, str]],
    allowlist: set[str],
    source_type: str,
) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for sheet_name, (asset_name, asset_type) in sheets_map.items():
        raw = pd.read_excel(workbook_path, sheet_name=sheet_name)
        raw.columns = [_clean_column_name(str(c)) for c in raw.columns]
        if "month" not in raw.columns:
            continue
        raw["month"] = pd.to_datetime(raw["month"], errors="coerce").dt.normalize()
        raw = raw.dropna(subset=["month"])
        raw["asset_name"] = asset_name
        raw["asset_type"] = asset_type

        dim_cols = {"month", "asset_name", "asset_type", "club"}
        measure_cols = [c for c in raw.columns if c in allowlist and c not in dim_cols]
        if not measure_cols:
            continue

        id_vars = ["month", "asset_name", "asset_type"]
        if "club" in raw.columns:
            id_vars.append("club")

        melted = raw.melt(
            id_vars=id_vars,
            value_vars=measure_cols,
            var_name="metric_name",
            value_name="metric_value",
        )
        melted["metric_value"] = pd.to_numeric(melted["metric_value"], errors="coerce")
        melted = melted.dropna(subset=["metric_value"])
        melted["source_type"] = source_type
        frames.append(melted)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_kpi_health(internal_df: pd.DataFrame) -> pd.DataFrame:
    if internal_df.empty:
        return pd.DataFrame(columns=[
            "month", "asset_name", "metric_name", "metric_value", "prior_month_value",
            "prior_season_same_month_value", "rolling_12m_avg", "seasonal_baseline",
            "deviation_from_seasonal_baseline", "trend_direction", "health_status",
        ])
    df = internal_df.copy()
    df = df.sort_values(["asset_name", "metric_name", "month"])
    grp = df.groupby(["asset_name", "metric_name"], sort=False)
    df["prior_month_value"] = grp["metric_value"].shift(1)
    df["prior_season_same_month_value"] = grp["metric_value"].shift(12)
    df["rolling_12m_avg"] = grp["metric_value"].transform(lambda s: s.rolling(12, min_periods=1).mean())
    df["seasonal_baseline"] = df["rolling_12m_avg"]
    df["deviation_from_seasonal_baseline"] = np.where(
        df["seasonal_baseline"] != 0,
        (df["metric_value"] - df["seasonal_baseline"]) / df["seasonal_baseline"],
        np.nan,
    )
    df["trend_direction"] = np.where(
        df["prior_month_value"].isna(),
        "flat",
        np.where(df["metric_value"] > df["prior_month_value"], "up", np.where(df["metric_value"] < df["prior_month_value"], "down", "flat")),
    )
    polarity = df["metric_name"].map(METRIC_POLARITY).fillna(1).astype(int)

    def _health_row(dev: float, pol: int) -> str:
        if pd.isna(dev):
            return "stable"
        if pol == 1:
            if dev > 0.05:
                return "good"
            if dev < -0.05:
                return "review"
            return "stable"
        if dev < -0.05:
            return "good"
        if dev > 0.05:
            return "review"
        return "stable"

    df["health_status"] = [ _health_row(float(dev) if pd.notna(dev) else np.nan, int(pol)) for dev, pol in zip(df["deviation_from_seasonal_baseline"], polarity) ]
    return df[[
        "month", "asset_name", "metric_name", "metric_value", "prior_month_value",
        "prior_season_same_month_value", "rolling_12m_avg", "seasonal_baseline",
        "deviation_from_seasonal_baseline", "trend_direction", "health_status",
    ]]


def build_peer_benchmark(internal_df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.DataFrame:
    if internal_df.empty or benchmark_df.empty:
        return pd.DataFrame(columns=[
            "month", "asset_name", "metric_name", "rm_value", "peer_median", "peer_mean",
            "peer_leader_value", "rm_rank", "club_count", "gap_to_peer_median", "gap_to_leader",
            "rank_change_12m", "gap_change_12m",
        ])

    rm = internal_df.rename(columns={"metric_value": "rm_value"})[["month", "asset_name", "metric_name", "rm_value"]]
    peers = benchmark_df.rename(columns={"metric_value": "peer_value"})[["month", "asset_name", "metric_name", "club", "peer_value"]]
    stats = peers.groupby(["month", "asset_name", "metric_name"], as_index=False).agg(
        peer_median=("peer_value", "median"),
        peer_mean=("peer_value", "mean"),
        peer_max_value=("peer_value", "max"),
        peer_min_value=("peer_value", "min"),
        club_count=("club", "nunique"),
    )
    stats = stats[stats["club_count"] == 5].copy()
    aligned = rm.merge(stats, on=["month", "asset_name", "metric_name"], how="inner")
    aligned["polarity"] = aligned["metric_name"].map(BENCHMARK_POLARITY).fillna(1).astype(int)
    aligned["peer_leader_value"] = np.where(aligned["polarity"] == -1, aligned["peer_min_value"], aligned["peer_max_value"])
    aligned["gap_to_peer_median"] = aligned["polarity"] * (aligned["rm_value"] - aligned["peer_median"])
    aligned["gap_to_leader"] = aligned["polarity"] * (aligned["rm_value"] - aligned["peer_leader_value"])

    rank_rows = peers.merge(aligned[["month", "asset_name", "metric_name", "polarity"]].drop_duplicates(), on=["month", "asset_name", "metric_name"], how="inner")
    rank_rows = rank_rows.rename(columns={"peer_value": "value"})
    rm_rows = aligned[["month", "asset_name", "metric_name", "rm_value", "polarity"]].rename(columns={"rm_value": "value"})
    rm_rows["is_rm"] = 1
    rank_rows["is_rm"] = 0
    rank_all = pd.concat([rank_rows[["month", "asset_name", "metric_name", "value", "polarity", "is_rm"]], rm_rows[["month", "asset_name", "metric_name", "value", "polarity", "is_rm"]]], ignore_index=True)
    rank_all["adjusted_value"] = rank_all["value"] * rank_all["polarity"]
    rank_all["rm_rank"] = rank_all.groupby(["month", "asset_name", "metric_name"])["adjusted_value"].rank(method="min", ascending=False)
    rm_rank = rank_all[rank_all["is_rm"] == 1][["month", "asset_name", "metric_name", "rm_rank"]]
    aligned = aligned.merge(rm_rank, on=["month", "asset_name", "metric_name"], how="left")
    aligned["rm_rank"] = aligned["rm_rank"].astype("Int64")

    aligned = aligned.sort_values(["asset_name", "metric_name", "month"])
    aligned["rank_12m_ago"] = aligned.groupby(["asset_name", "metric_name"])["rm_rank"].shift(12)
    aligned["gap_12m_ago"] = aligned.groupby(["asset_name", "metric_name"])["gap_to_peer_median"].shift(12)
    aligned["rank_change_12m"] = aligned["rank_12m_ago"] - aligned["rm_rank"]
    aligned["gap_change_12m"] = aligned["gap_to_peer_median"] - aligned["gap_12m_ago"]
    return aligned[[
        "month", "asset_name", "metric_name", "rm_value", "peer_median", "peer_mean",
        "peer_leader_value", "rm_rank", "club_count", "gap_to_peer_median", "gap_to_leader",
        "rank_change_12m", "gap_change_12m",
    ]]


def build_signals(internal_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "source_asset", "source_metric", "target_asset", "target_metric", "lag_months",
        "relationship_direction", "strength_score", "validation_status",
        "business_interpretation", "last_validated_month",
    ]
    if internal_df.empty:
        return pd.DataFrame(columns=cols)
    wide = internal_df.assign(feature_key=internal_df["asset_name"] + "_" + internal_df["metric_name"]).pivot_table(
        index="month", columns="feature_key", values="metric_value", aggfunc="max"
    ).sort_index()

    targets = [
        ("ecommerce", "net_sales"),
        ("ecommerce", "conversion_rate"),
        ("streaming", "subscriptions"),
    ]
    candidates = [
        ("fan_app", "heavy_users", "Rising app engagement from heavy users predicts increased {} in the following months."),
        ("main_website", "bounce_rate", "Increased friction (bounce rate) on the main site tends to degrade {} over a lag window."),
        ("main_website", "unique_visitors", "Top-of-funnel traffic volume strongly leads {} shortly after."),
    ]
    rows: List[Dict[str, Any]] = []
    for c_asset, c_metric, interp in candidates:
        source_col = f"{c_asset}_{c_metric}"
        if source_col not in wide.columns:
            continue
        for t_asset, t_metric in targets:
            target_col = f"{t_asset}_{t_metric}"
            if target_col not in wide.columns:
                continue
            for lag in (1, 2, 3):
                paired = pd.DataFrame({
                    "source": wide[source_col],
                    "target": wide[target_col].shift(-lag),
                }).dropna()
                if len(paired) <= 12:
                    continue
                corr = paired["source"].corr(paired["target"])
                if pd.isna(corr) or abs(float(corr)) <= 0.65:
                    continue
                rows.append({
                    "source_asset": c_asset,
                    "source_metric": c_metric,
                    "target_asset": t_asset,
                    "target_metric": t_metric,
                    "lag_months": lag,
                    "relationship_direction": "positive" if corr > 0 else "negative",
                    "strength_score": float(corr),
                    "validation_status": "active",
                    "business_interpretation": interp.format(f"{t_asset} {t_metric}"),
                })
    rows = sorted(rows, key=lambda r: abs(float(r["strength_score"])), reverse=True)[:3]
    if not rows:
        return pd.DataFrame(columns=cols)
    latest_month = internal_df["month"].max()
    out = pd.DataFrame(rows)
    out["last_validated_month"] = latest_month
    return out[cols]


def build_priority_board(kpi: pd.DataFrame, peer: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    if kpi.empty:
        return pd.DataFrame(columns=[
            "month", "priority_id", "priority_title", "priority_category", "priority_score", "priority_rank",
            "asset_name", "primary_metric", "summary_text", "why_it_matters", "suggested_next_investigation",
            "supporting_metrics_json",
        ])

    df = kpi.merge(
        peer[["month", "asset_name", "metric_name", "rm_rank", "club_count", "peer_median", "peer_leader_value", "gap_to_peer_median", "gap_to_leader"]],
        on=["month", "asset_name", "metric_name"],
        how="left",
    ).rename(columns={"rm_rank": "peer_rank", "club_count": "peer_club_count"})

    df["metric_key"] = df["asset_name"] + "_" + df["metric_name"]
    df["is_active"] = (df["health_status"] != "stable").astype(int)
    df["severity_score"] = np.where(
        df["health_status"] != "stable",
        np.minimum(1.0, np.abs(df["deviation_from_seasonal_baseline"].fillna(0.0)) / 0.20),
        0.0,
    )
    df = df.sort_values(["asset_name", "metric_name", "month"])
    df["persistence_months"] = df.groupby(["asset_name", "metric_name"])["is_active"].transform(lambda s: s.rolling(3, min_periods=1).sum())
    df["persistence_score"] = np.minimum(1.0, df["persistence_months"] / 3.0)
    peer_rank_num = pd.to_numeric(df["peer_rank"], errors="coerce")
    peer_rank_safe = peer_rank_num.fillna(-1)
    df["peer_gap_score"] = np.where(
        peer_rank_num.isna(),
        0.0,
        np.where(peer_rank_safe >= 5, 1.0, np.where(peer_rank_safe == 4, 0.8, np.where(peer_rank_safe == 3, 0.4, 0.0))),
    )
    signal_keys = set()
    if not signals.empty:
        signal_keys = set((signals["source_asset"] + "_" + signals["source_metric"]).tolist())
    target_keys = {"ecommerce_net_sales", "ecommerce_conversion_rate", "streaming_subscriptions"}
    df["commercial_weight_score"] = np.where(df["metric_key"].isin(target_keys), 1.0, np.where(df["metric_key"].isin(signal_keys), 0.8, 0.4))
    df = df[df["is_active"] == 1].copy()
    if df.empty:
        return pd.DataFrame(columns=[
            "month", "priority_id", "priority_title", "priority_category", "priority_score", "priority_rank",
            "asset_name", "primary_metric", "summary_text", "why_it_matters", "suggested_next_investigation",
            "supporting_metrics_json",
        ])

    df["category"] = np.where(
        (df["health_status"] == "review") & (df["asset_name"] == "ecommerce"),
        "conversion weakness",
        np.where(
            (df["health_status"] == "review") & (df["metric_name"].str.contains("visitors|app_downloads", regex=True)),
            "growth risk",
            np.where(
                df["peer_gap_score"] >= 0.8,
                "benchmark underperformance",
                np.where(
                    (df["health_status"] == "good") & (df["metric_name"].str.contains("recurrence|heavy_users", regex=True)),
                    "engagement opportunity",
                    np.where(df["health_status"] == "review", "resilience concern", "engagement opportunity"),
                ),
            ),
        ),
    )
    pool = df[["month", "asset_name", "metric_name", "metric_value", "health_status", "trend_direction", "deviation_from_seasonal_baseline", "severity_score"]]
    support_map: Dict[Tuple[pd.Timestamp, str], List[Dict[str, Any]]] = {}
    for (month, asset), g in pool.groupby(["month", "asset_name"]):
        support_map[(month, asset)] = g.drop(columns=["month", "asset_name"]).to_dict(orient="records")

    signal_refs: Dict[str, List[Dict[str, Any]]] = {}
    if not signals.empty:
        for r in signals.to_dict(orient="records"):
            skey = f"{r['source_asset']}_{r['source_metric']}"
            tkey = f"{r['target_asset']}_{r['target_metric']}"
            base = {
                "source_asset": r["source_asset"],
                "source_metric": r["source_metric"],
                "target_asset": r["target_asset"],
                "target_metric": r["target_metric"],
                "lag_months": int(r["lag_months"]),
                "relationship_direction": r["relationship_direction"],
                "strength_score": float(r["strength_score"]),
                "validation_status": r["validation_status"],
                "business_interpretation": r["business_interpretation"],
            }
            signal_refs.setdefault(skey, []).append({"signal_role": "source", **base})
            signal_refs.setdefault(tkey, []).append({"signal_role": "target", **base})

    def _build_evidence(row: pd.Series) -> str:
        key = (row["month"], row["asset_name"])
        supporting_rows = [
            r for r in support_map.get(key, [])
            if r["metric_name"] != row["metric_name"]
        ]
        peer_context = None
        if pd.notna(row.get("peer_rank")):
            peer_context = {
                "peer_rank": int(row["peer_rank"]),
                "peer_club_count": int(row["peer_club_count"]),
                "peer_median": float(row["peer_median"]),
                "peer_leader_value": float(row["peer_leader_value"]),
                "gap_to_peer_median": float(row["gap_to_peer_median"]),
                "gap_to_leader": float(row["gap_to_leader"]),
            }
        payload = {
            "score_components": {
                "severity": float(row["severity_score"]),
                "persistence": float(row["persistence_score"]),
                "peer_gap": float(row["peer_gap_score"]),
                "commercial_weight": float(row["commercial_weight_score"]),
                "supporting_evidence": 1.0 if supporting_rows else 0.0,
            },
            "severity_inputs": {
                "metric_value": float(row["metric_value"]),
                "health_status": row["health_status"],
                "trend_direction": row["trend_direction"],
                "deviation_from_seasonal_baseline": float(row["deviation_from_seasonal_baseline"]) if pd.notna(row["deviation_from_seasonal_baseline"]) else None,
            },
            "persistence_inputs": {
                "active_months_in_last_3": int(row["persistence_months"]),
                "lookback_months": 3,
            },
            "peer_context": peer_context,
            "linked_signal_references": signal_refs.get(row["metric_key"], []),
            "supporting_metric_rows": supporting_rows,
        }
        return json.dumps(payload)

    df["supporting_evidence_score"] = np.where(
        df.apply(lambda r: len([x for x in support_map.get((r["month"], r["asset_name"]), []) if x["metric_name"] != r["metric_name"]]) > 0, axis=1),
        1.0,
        0.0,
    )
    df["priority_score"] = (
        0.30 * df["severity_score"]
        + 0.20 * df["persistence_score"]
        + 0.20 * df["peer_gap_score"]
        + 0.20 * df["commercial_weight_score"]
        + 0.10 * df["supporting_evidence_score"]
    )
    df["priority_candidate_id"] = df["month"].dt.strftime("%Y-%m-%d") + "_" + df["asset_name"] + "_" + df["metric_name"]
    df = df.sort_values(["month", "priority_score", "asset_name", "metric_name"], ascending=[True, False, True, True])
    df["priority_rank"] = df.groupby("month").cumcount() + 1
    df = df[df["priority_rank"] <= 10].copy()
    df["priority_id"] = df["priority_candidate_id"]
    df["priority_title"] = df["category"].str.title() + " in " + df["asset_name"].str.replace("_", " ").str.title()
    df["primary_metric"] = df["metric_name"]
    df["priority_category"] = df["category"]
    df["summary_text"] = (
        df["primary_metric"] + " is " + df["trend_direction"] + " versus prior month with seasonal deviation "
        + df["deviation_from_seasonal_baseline"].fillna(0.0).map(lambda x: f"{x:.4f}") + "."
    )
    df["why_it_matters"] = np.where(
        df["metric_key"].isin(signal_refs.keys()),
        "This metric is connected to validated leading indicators and can affect commercial outcomes.",
        np.where(
            df["peer_rank"].notna(),
            "This metric has measurable peer benchmark context and a defined competitive gap.",
            "This metric is persistently outside stable range and requires operational review.",
        ),
    )
    df["suggested_next_investigation"] = np.where(
        df["category"].str.contains("conversion"),
        "Investigate funnel drop-off points and recent checkout changes.",
        np.where(
            df["category"].str.contains("growth"),
            "Review acquisition channels and campaign pacing for this asset.",
            np.where(
                df["category"].str.contains("benchmark"),
                "Compare competitor tactics for this KPI and isolate the largest monthly delta driver.",
                "Review segment-level drivers and data quality checks before taking action.",
            ),
        ),
    )
    df["supporting_metrics_json"] = df.apply(_build_evidence, axis=1)
    return df[[
        "month", "priority_id", "priority_title", "priority_category", "priority_score", "priority_rank",
        "asset_name", "primary_metric", "summary_text", "why_it_matters", "suggested_next_investigation",
        "supporting_metrics_json",
    ]]


def build_monthly_brief(priority: pd.DataFrame, kpi: pd.DataFrame, peer: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    if kpi.empty:
        return pd.DataFrame(columns=[
            "month", "top_priority_ids_json", "top_anomalies_json", "strongest_signal_ids_json",
            "benchmark_summary_json", "health_summary_json",
        ])
    months = sorted(kpi["month"].dropna().unique())
    out_rows: List[Dict[str, Any]] = []
    for month in months:
        p_month = priority[priority["month"] == month].sort_values("priority_rank").head(3)
        top_priorities = [{
            "priority_id": str(r["priority_id"]),
            "priority_rank": int(r["priority_rank"]),
            "priority_title": str(r["priority_title"]),
            "priority_category": str(r["priority_category"]),
            "priority_score": round(float(r["priority_score"]), 4),
        } for _, r in p_month.iterrows()]

        anom = kpi[(kpi["month"] == month) & (kpi["health_status"] == "review")].copy()
        anom["abs_dev"] = anom["deviation_from_seasonal_baseline"].abs()
        anom = anom.sort_values(["abs_dev", "asset_name", "metric_name"], ascending=[False, True, True]).head(3)
        top_anom = [{
            "anomaly_rank": idx + 1,
            "asset_name": str(r["asset_name"]),
            "metric_name": str(r["metric_name"]),
            "metric_value": round(float(r["metric_value"]), 4),
            "deviation_from_seasonal_baseline": round(float(r["deviation_from_seasonal_baseline"]), 4) if pd.notna(r["deviation_from_seasonal_baseline"]) else None,
        } for idx, (_, r) in enumerate(anom.iterrows())]

        sig_items: List[Dict[str, Any]] = []
        if not signals.empty:
            sig_month = signals[signals["last_validated_month"] == month].copy()
            sig_month["signal_id"] = (
                sig_month["source_asset"] + "__" + sig_month["source_metric"] + "__" + sig_month["target_asset"] + "__" + sig_month["target_metric"] + "__" + sig_month["lag_months"].astype(int).astype(str)
            )
            sig_month["abs_strength"] = sig_month["strength_score"].abs()
            sig_month = sig_month.sort_values(["abs_strength", "signal_id"], ascending=[False, True]).head(3)
            sig_items = [{
                "signal_rank": idx + 1,
                "signal_id": str(r["signal_id"]),
                "source_asset": str(r["source_asset"]),
                "source_metric": str(r["source_metric"]),
                "target_asset": str(r["target_asset"]),
                "target_metric": str(r["target_metric"]),
                "lag_months": int(r["lag_months"]),
                "relationship_direction": str(r["relationship_direction"]),
                "strength_score": round(float(r["strength_score"]), 4),
            } for idx, (_, r) in enumerate(sig_month.iterrows())]

        b_month = peer[peer["month"] == month]
        benchmark_summary = {
            "benchmarked_metric_count": int(len(b_month)),
            "benchmark_underperformance_count": int((b_month["rm_rank"] >= 4).sum()) if not b_month.empty else 0,
            "avg_gap_to_peer_median": round(float(b_month["gap_to_peer_median"].mean()), 4) if not b_month.empty else None,
            "worst_gap_to_peer_median": round(float(b_month["gap_to_peer_median"].min()), 4) if not b_month.empty else None,
        }
        h_month = kpi[kpi["month"] == month]
        health_summary = {
            "metric_count": int(len(h_month)),
            "good_count": int((h_month["health_status"] == "good").sum()),
            "review_count": int((h_month["health_status"] == "review").sum()),
            "stable_count": int((h_month["health_status"] == "stable").sum()),
            "avg_abs_deviation": round(float(h_month["deviation_from_seasonal_baseline"].abs().mean()), 4) if not h_month.empty else None,
        }

        out_rows.append({
            "month": month,
            "top_priority_ids_json": json.dumps(top_priorities),
            "top_anomalies_json": json.dumps(top_anom),
            "strongest_signal_ids_json": json.dumps(sig_items),
            "benchmark_summary_json": json.dumps(benchmark_summary),
            "health_summary_json": json.dumps(health_summary),
        })
    return pd.DataFrame(out_rows)


def build_quality_checks(internal_df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.DataFrame:
    run_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()
    checks: List[Dict[str, Any]] = []

    def add_check(table: str, check: str, severity: str, issue_count: int, details: str) -> None:
        checks.append({
            "run_id": run_id,
            "table_name": table,
            "check_name": check,
            "severity": severity,
            "status": "PASS" if issue_count == 0 else "FAIL",
            "issue_count": int(issue_count),
            "issue_details": details,
            "run_timestamp": ts,
        })

    add_check("clubos_silver.silver_internal_asset_metrics", "No null months", "REQUIRED", int(internal_df["month"].isna().sum()), "month IS NOT NULL")
    add_check("clubos_silver.silver_internal_asset_metrics", "No null metric values", "REQUIRED", int(internal_df["metric_value"].isna().sum()), "metric_value IS NOT NULL")
    dup_internal = int(internal_df.duplicated(subset=["month", "asset_name", "metric_name"], keep=False).sum())
    add_check("clubos_silver.silver_internal_asset_metrics", "No duplicate keys on (month, asset_name, metric_name)", "REQUIRED", dup_internal, "Duplicate key groups")
    dup_bench = int(benchmark_df.duplicated(subset=["month", "asset_name", "metric_name", "club"], keep=False).sum()) if not benchmark_df.empty else 0
    add_check("clubos_silver.silver_benchmark_asset_metrics", "No duplicate keys on (month, asset_name, metric_name, club)", "REQUIRED", dup_bench, "Duplicate key groups")
    counts = benchmark_df.groupby(["month", "asset_name", "metric_name"])["club"].nunique() if not benchmark_df.empty else pd.Series(dtype="int")
    issue_bench = int((counts != 5).sum()) if len(counts) else 0
    add_check("clubos_silver.silver_benchmark_asset_metrics", "Exactly 5 benchmark clubs per month+asset+metric", "REQUIRED", issue_bench, "Expected club_count == 5")
    rate_rows = internal_df[internal_df["metric_name"].str.contains("rate$|_rate$|recurrence$|bounce_rate$", regex=True, na=False)]
    rate_issues = int(((rate_rows["metric_value"] < 0) | (rate_rows["metric_value"] > 1)).sum()) if not rate_rows.empty else 0
    add_check("clubos_silver.silver_internal_asset_metrics", "Rate and recurrence metrics bounded between 0 and 1", "REQUIRED", rate_issues, "Found rate-like metric outside [0,1]")
    return pd.DataFrame(checks)


def save_csv(df: pd.DataFrame, out_dir: Path, table_name: str) -> None:
    path = out_dir / f"{table_name}.csv"
    if "month" in df.columns:
        df = df.copy()
        df["month"] = pd.to_datetime(df["month"], errors="coerce").dt.strftime("%Y-%m-%d")
    if "last_validated_month" in df.columns:
        df["last_validated_month"] = pd.to_datetime(df["last_validated_month"], errors="coerce").dt.strftime("%Y-%m-%d")
    df.to_csv(path, index=False)
    print(f"wrote {path}")


def locate_workbook(source_dir: Path, filename: str) -> Path:
    matches = list(source_dir.rglob(filename))
    if not matches:
        raise FileNotFoundError(f"Could not find '{filename}' under {source_dir}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local ClubOS snapshot tables from source files.")
    parser.add_argument("--source-dir", default="data/source", help="Root folder containing source xlsx files.")
    parser.add_argument("--output-dir", default="data/gold_snapshots", help="Output snapshot directory.")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    internal_path = locate_workbook(source_dir, INTERNAL_FILE)
    benchmark_path = locate_workbook(source_dir, BENCHMARK_FILE)
    print(f"internal workbook: {internal_path}")
    print(f"benchmark workbook: {benchmark_path}")

    internal_df = _read_excel_long(internal_path, INTERNAL_SHEETS, INTERNAL_ALLOWLIST, "internal")
    benchmark_df = _read_excel_long(benchmark_path, BENCHMARK_SHEETS, BENCHMARK_ALLOWLIST, "benchmark")

    kpi_health = build_kpi_health(internal_df)
    peer = build_peer_benchmark(internal_df[["month", "asset_name", "metric_name", "metric_value"]], benchmark_df[["month", "asset_name", "metric_name", "club", "metric_value"]])
    signals = build_signals(internal_df[["month", "asset_name", "metric_name", "metric_value"]])
    priority = build_priority_board(kpi_health, peer, signals)
    brief = build_monthly_brief(priority, kpi_health, peer, signals)
    quality = build_quality_checks(internal_df, benchmark_df)

    save_csv(quality, output_dir, "silver_data_quality_checks")
    save_csv(kpi_health, output_dir, "gold_kpi_health")
    save_csv(peer, output_dir, "gold_peer_benchmark")
    save_csv(signals, output_dir, "gold_signal_relationships")
    save_csv(priority, output_dir, "gold_priority_board")
    save_csv(brief, output_dir, "gold_monthly_brief_inputs")
    print("local snapshot generation complete")


if __name__ == "__main__":
    main()
