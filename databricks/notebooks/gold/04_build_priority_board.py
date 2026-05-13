# Databricks notebook source
# COMMAND ----------
# ClubOS Gold Output - Priority Board
#
# Purpose:
# - convert scored priority inputs into ranked monthly product outputs
# - persist deterministic evidence payloads for every row

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.sql.window import Window

df = spark.read.table("clubos_gold.gold_priority_inputs")

# 1. Calculate Priority Score
# Formula: 0.30*severity + 0.20*persistence + 0.20*peer_gap + 0.20*commercial + 0.10*supporting
df = df.withColumn(
    "priority_score",
    (F.col("severity_score") * F.lit(0.30))
    + (F.col("persistence_score") * F.lit(0.20))
    + (F.col("peer_gap_score") * F.lit(0.20))
    + (F.col("commercial_weight_score") * F.lit(0.20))
    + (F.col("supporting_evidence_score") * F.lit(0.10))
)

# 2. Rank priorities per month and keep top 10
w_rank = Window.partitionBy("month").orderBy(F.col("priority_score").desc(), F.col("asset_name"), F.col("metric_name"))
df = df.withColumn("priority_rank", F.row_number().over(w_rank)).filter(F.col("priority_rank") <= 10)

# 3. Deterministic presentation fields (non-AI)
df = df.withColumn("priority_id", F.col("priority_candidate_id"))
df = df.withColumn(
    "priority_title",
    F.concat(F.initcap(F.col("category")), F.lit(" in "), F.initcap(F.regexp_replace(F.col("asset_name"), "_", " ")))
)
df = df.withColumn("primary_metric", F.col("metric_name"))
df = df.withColumn("priority_category", F.col("category"))

df = df.withColumn(
    "summary_text",
    F.concat(
        F.lit(""),
        F.col("primary_metric"),
        F.lit(" is "),
        F.col("trend_direction"),
        F.lit(" versus prior month with seasonal deviation "),
        F.format_number(F.col("deviation_from_seasonal_baseline"), 4),
        F.lit(".")
    )
)

df = df.withColumn(
    "why_it_matters",
    F.when(
        F.size("linked_signal_refs") > 0,
        F.lit("This metric is connected to validated leading indicators and can affect commercial outcomes.")
    ).when(
        F.col("peer_context").isNotNull(),
        F.lit("This metric has measurable peer benchmark context and a defined competitive gap.")
    ).otherwise(
        F.lit("This metric is persistently outside stable range and requires operational review.")
    )
)

df = df.withColumn(
    "suggested_next_investigation",
    F.when(F.col("category").like("%conversion%"), F.lit("Investigate funnel drop-off points and recent checkout changes."))
    .when(F.col("category").like("%growth%"), F.lit("Review acquisition channels and campaign pacing for this asset."))
    .when(F.col("category").like("%benchmark%"), F.lit("Compare competitor tactics for this KPI and isolate the largest monthly delta driver."))
    .otherwise(F.lit("Review segment-level drivers and data quality checks before taking action."))
)

# 4. Deterministic evidence payload (fully usable without AI)
evidence_struct = F.struct(
    F.struct(
        F.col("severity_score").alias("severity"),
        F.col("persistence_score").alias("persistence"),
        F.col("peer_gap_score").alias("peer_gap"),
        F.col("commercial_weight_score").alias("commercial_weight"),
        F.col("supporting_evidence_score").alias("supporting_evidence")
    ).alias("score_components"),
    F.struct(
        F.col("metric_value").alias("metric_value"),
        F.col("health_status").alias("health_status"),
        F.col("trend_direction").alias("trend_direction"),
        F.col("deviation_from_seasonal_baseline").alias("deviation_from_seasonal_baseline")
    ).alias("severity_inputs"),
    F.struct(
        F.col("persistence_months").alias("active_months_in_last_3"),
        F.lit(3).alias("lookback_months")
    ).alias("persistence_inputs"),
    F.col("peer_context").alias("peer_context"),
    F.col("linked_signal_refs").alias("linked_signal_references"),
    F.col("supporting_metric_rows").alias("supporting_metric_rows")
)

df = df.withColumn("supporting_metrics_json", F.to_json(evidence_struct))

final_cols = [
    "month",
    "priority_id",
    "priority_title",
    "priority_category",
    "priority_score",
    "priority_rank",
    "asset_name",
    "primary_metric",
    "summary_text",
    "why_it_matters",
    "suggested_next_investigation",
    "supporting_metrics_json"
]

gold_priority = df.select(*final_cols)
gold_priority.write.format("delta").mode("overwrite").saveAsTable("clubos_gold.gold_priority_board")
print(f"Created gold_priority_board with deterministic evidence payloads. {gold_priority.count()} rows.")
