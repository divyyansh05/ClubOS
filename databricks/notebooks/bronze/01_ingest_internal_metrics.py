# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest Internal Metrics (Bronze)
# MAGIC Reads the raw internal metrics Excel file, adds lineage metadata, and saves to Bronze.

import pyspark.sql.functions as F
from datetime import datetime

# In a real environment, this path would be dynamic or mounted
SOURCE_FILE = "/Volumes/clubos/main/raw/Tema5.internal_metrics.dataset.xlsx"

def ingest_sheet(sheet_name, target_table):
    # Note: Databricks standard engine doesn't read excel natively without the spark-excel library.
    # We write this using spark.read.format("excel") assuming the library is installed.
    df = (spark.read
          .format("excel")
          .option("header", "true")
          .option("dataAddress", f"'{sheet_name}'!")
          .load(SOURCE_FILE))
    
    # Add metadata
    df = df.withColumn("source_file_name", F.lit("Tema5.internal_metrics.dataset.xlsx"))
    df = df.withColumn("ingestion_timestamp", F.current_timestamp())
    
    # Write to delta
    # spark.sql(f"CREATE DATABASE IF NOT EXISTS clubos_bronze")
    df.write.format("delta").mode("overwrite").saveAsTable(f"clubos_bronze.{target_table}")
    print(f"Saved {sheet_name} to clubos_bronze.{target_table} with {df.count()} rows.")

# Ingest the 4 main sheets
ingest_sheet("Main_Website", "bronze_internal_main_website")
ingest_sheet("eCommerce", "bronze_internal_ecommerce")
ingest_sheet("Streaming_Website", "bronze_internal_streaming")
ingest_sheet("Fan_App", "bronze_internal_fan_app")
