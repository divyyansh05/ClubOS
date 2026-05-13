# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest Benchmark Metrics (Bronze)

import pyspark.sql.functions as F

SOURCE_FILE = "/Volumes/clubos/main/raw/Tema5.benchmark.dataset.xlsx"

def ingest_sheet(sheet_name, target_table):
    df = (spark.read
          .format("excel")
          .option("header", "true")
          .option("dataAddress", f"'{sheet_name}'!")
          .load(SOURCE_FILE))
    
    df = df.withColumn("source_file_name", F.lit("Tema5.benchmark.dataset.xlsx"))
    df = df.withColumn("ingestion_timestamp", F.current_timestamp())
    
    df.write.format("delta").mode("overwrite").saveAsTable(f"clubos_bronze.{target_table}")
    print(f"Saved {sheet_name} to clubos_bronze.{target_table}")

ingest_sheet("Main_Website", "bronze_benchmark_main_website")
ingest_sheet("eCommerce", "bronze_benchmark_ecommerce")
ingest_sheet("Streaming", "bronze_benchmark_streaming")
ingest_sheet("Fan_App", "bronze_benchmark_fan_app")
