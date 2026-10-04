# %% [markdown]
# # 03 · Bronze → Silver: clean, validate, conform
#
# **Input:** `bronze.nyc311_service_requests`, `bronze.weather_hourly` (only rows not yet processed)
# **Output:** `silver.service_requests`, `silver.weather_hourly` (typed, de-duplicated, merged)
#
# | Rule | Check | When it fails |
# |---|---|---|
# | SR01 | `unique_key` is present and numeric | Row goes to quarantine |
# | SR02 | `created_date` is present and not in the future | Row goes to quarantine |
# | SR03 | One row per `unique_key` | Latest version kept |
# | SR04 | `closed_date` is not before `created_date` | Closed date cleared, row flagged |
# | SR05 | `closed_date` is not in the future | Closed date cleared, row flagged |
# | SR06 | ZIP code is 5 digits | ZIP cleared, row flagged |
# | SR07 | Coordinates fall inside New York City | Coordinates cleared, row flagged |
# | SR08 | Borough is one of the five boroughs | Set to `UNKNOWN`, row flagged |
# | WX01 | Weather hour has a temperature reading | Row dropped (not yet published by source) |
# | WX02 | One row per borough and hour | Latest version kept |
#
# Every rule writes its pass/fail counts to `meta.dq_results`. Nothing is dropped silently:
# rejected rows are kept in `silver.service_requests_quarantine` with the reason.

# %% tags=["parameters"]
# Parameters (set by the pipeline)
load_mode = "incremental"     # "backfill" reprocesses all of Bronze
pipeline_run_id = ""

# %%
%run nb_00_common

# %%
from delta.tables import DeltaTable
from pyspark.sql import Window

spark.conf.set("spark.sql.parquet.vorder.default", "true")          # read-optimised files for SQL and Power BI
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")

now_ts = F.lit(datetime.utcnow()).cast("timestamp")


def clean_text(col_name):
    """Trim, and turn the source's placeholder values into real NULLs."""
    c = F.trim(F.col(col_name))
    return F.when(c.isNull() | F.upper(c).isin("", "UNSPECIFIED", "N/A", "NA", "UNKNOWN"), None).otherwise(c)


def merge_into(df, table: str, key_condition: str):
    """Upsert a DataFrame into a Delta table, creating the table on first use."""
    if spark.catalog.tableExists(table):
        (DeltaTable.forName(spark, table).alias("t").merge(df.alias("s"), key_condition)
            .whenMatchedUpdateAll().whenNotMatchedInsertAll().execute())
    else:
        df.write.format("delta").saveAsTable(table)

# %% [markdown]
# ## 1 · Service requests: type and standardise

# %%
SR_SOURCE, SR_TABLE = "silver_service_requests", "silver.service_requests"
run = RunContext("nyc311", "silver", load_mode, pipeline_run_id)

try:
    sr_wm = None if load_mode == "backfill" else get_watermark(SR_SOURCE)
    bronze = spark.table("bronze.nyc311_service_requests")
    if sr_wm is not None:
        bronze = bronze.where(F.col("_ingested_at") > F.lit(sr_wm))
    run.rows_read = bronze.count()
    print(f"{run.rows_read:,} Bronze rows to process (watermark: {sr_wm})")

    typed = bronze.select(
        F.col("unique_key").cast("bigint").alias("unique_key"),
        F.to_timestamp("created_date").alias("created_at"),
        F.to_timestamp("closed_date").alias("closed_at"),
        F.to_timestamp("due_date").alias("due_at"),
        F.to_timestamp("resolution_action_updated_date").alias("resolution_updated_at"),
        F.upper(clean_text("agency")).alias("agency_code"),
        clean_text("agency_name").alias("agency_name"),
        clean_text("complaint_type").alias("complaint_type"),
        clean_text("descriptor").alias("descriptor"),
        clean_text("location_type").alias("location_type"),
        clean_text("incident_zip").alias("incident_zip"),
        F.initcap(clean_text("city")).alias("city"),
        F.upper(clean_text("borough")).alias("borough"),
        clean_text("community_board").alias("community_board"),
        F.col("council_district").cast("int").alias("council_district"),
        F.upper(clean_text("open_data_channel_type")).alias("channel"),
        clean_text("status").alias("status"),
        clean_text("resolution_description").alias("resolution_description"),
        F.col("latitude").cast("double").alias("latitude"),
        F.col("longitude").cast("double").alias("longitude"),
        F.col("unique_key").alias("_raw_unique_key"),
        F.col("created_date").alias("_raw_created_date"),
        F.col("_run_id").alias("_bronze_run_id"),
        "_ingested_at", "_source_file",
    )
except Exception as exc:
    run.fail(exc)

# %% [markdown]
# ## 2 · Service requests: apply the data-quality rules

# %%
try:
    # --- Reject rules: rows that cannot be trusted at all go to quarantine -------------------------
    checked = typed.withColumn(
        "reject_reason",
        F.when(F.col("unique_key").isNull(), "SR01 missing or non-numeric unique_key")
         .when(F.col("created_at").isNull(), "SR02 missing or unparseable created_date")
         .when(F.col("created_at") > F.date_add(now_ts, 1), "SR02 created_date in the future"),
    ).cache()

    rejected = checked.where(F.col("reject_reason").isNotNull())
    n_sr01 = rejected.where(F.col("reject_reason").startswith("SR01")).count()
    n_sr02 = rejected.where(F.col("reject_reason").startswith("SR02")).count()
    (rejected.select("_raw_unique_key", "_raw_created_date", "reject_reason", "_bronze_run_id", "_source_file",
                     F.lit(run.run_id).alias("_silver_run_id"), now_ts.alias("_quarantined_at"))
        .write.format("delta").mode("append").saveAsTable("silver.service_requests_quarantine"))

    # --- De-duplicate: the same request arrives again whenever it is updated ---------------------
    valid = checked.where(F.col("reject_reason").isNull())
    n_valid = valid.count()
    latest = Window.partitionBy("unique_key").orderBy(F.col("_ingested_at").desc(),
                                                      F.col("resolution_updated_at").desc_nulls_last())
    deduped = valid.withColumn("_rn", F.row_number().over(latest)).where("_rn = 1").drop("_rn")

    # --- Repair rules: fix the field, keep the row, flag what was done ---------------------------
    BOROUGHS = ["MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND"]
    f_sr04 = F.col("closed_at") < F.col("created_at")
    f_sr05 = F.col("closed_at") > F.date_add(now_ts, 1)
    f_sr06 = F.col("incident_zip").isNotNull() & ~F.col("incident_zip").rlike(r"^\d{5}$")
    f_sr07 = F.col("latitude").isNotNull() & ~(F.col("latitude").between(40.4, 41.0) & F.col("longitude").between(-74.3, -73.6))
    f_sr08 = F.col("borough").isNull() | ~F.col("borough").isin(BOROUGHS)

    flagged = (deduped
        .withColumn("f_sr04", F.coalesce(f_sr04, F.lit(False))).withColumn("f_sr05", F.coalesce(f_sr05, F.lit(False)))
        .withColumn("f_sr06", F.coalesce(f_sr06, F.lit(False))).withColumn("f_sr07", F.coalesce(f_sr07, F.lit(False)))
        .withColumn("f_sr08", F.coalesce(f_sr08, F.lit(False))))

    counts = flagged.agg(F.count("*").alias("n"), *[F.sum(F.col(f"f_sr0{i}").cast("int")).alias(f"sr0{i}") for i in range(4, 9)]).first()
    n_dedup = counts["n"]

    rules = [
        ("SR01", "unique_key is present and numeric", "quarantine", run.rows_read, n_sr01),
        ("SR02", "created_date is present and not in the future", "quarantine", run.rows_read, n_sr02),
        ("SR03", "one row per unique_key", "keep latest version", n_valid, n_valid - n_dedup),
        ("SR04", "closed_date is not before created_date", "clear closed_date, flag row", n_dedup, counts["sr04"] or 0),
        ("SR05", "closed_date is not in the future", "clear closed_date, flag row", n_dedup, counts["sr05"] or 0),
        ("SR06", "ZIP code is 5 digits", "clear ZIP, flag row", n_dedup, counts["sr06"] or 0),
        ("SR07", "coordinates fall inside New York City", "clear coordinates, flag row", n_dedup, counts["sr07"] or 0),
        ("SR08", "borough is one of the five boroughs", "set to UNKNOWN, flag row", n_dedup, counts["sr08"] or 0),
    ]
    for rule_id, desc, action, n_checked, n_failed in rules:
        record_dq(run.run_id, "silver", SR_TABLE, rule_id, desc, action, n_checked, n_failed)
        print(f"  {rule_id}  {desc:<48} failed {n_failed:>9,} of {n_checked:>10,}")
except Exception as exc:
    run.fail(exc)

# %% [markdown]
# ## 3 · Service requests: derive business columns and merge into Silver
#
# The merge is keyed on `unique_key`, so re-running a load, or re-reading a request that was updated
# at source, updates the existing row instead of creating a duplicate. The load is idempotent.

# %%
try:
    bad_closed = F.col("f_sr04") | F.col("f_sr05")
    silver_sr = (flagged
        .withColumn("closed_at", F.when(bad_closed, None).otherwise(F.col("closed_at")))
        .withColumn("incident_zip", F.when(F.col("f_sr06"), None).otherwise(F.col("incident_zip")))
        .withColumn("latitude", F.when(F.col("f_sr07"), None).otherwise(F.col("latitude")))
        .withColumn("longitude", F.when(F.col("f_sr07"), None).otherwise(F.col("longitude")))
        .withColumn("borough", F.when(F.col("f_sr08"), "UNKNOWN").otherwise(F.col("borough")))
        .withColumn("status", F.coalesce(F.col("status"), F.lit("Unknown")))
        .withColumn("channel", F.coalesce(F.col("channel"), F.lit("UNKNOWN")))
        .withColumn("created_date", F.to_date("created_at"))
        .withColumn("created_hour", F.date_trunc("hour", "created_at"))
        .withColumn("is_closed", F.col("closed_at").isNotNull())
        .withColumn("resolution_hours",
                    F.round((F.col("closed_at").cast("long") - F.col("created_at").cast("long")) / 3600.0, 2))
        .withColumn("closed_within_due",
                    F.when(F.col("closed_at").isNotNull() & F.col("due_at").isNotNull(), F.col("closed_at") <= F.col("due_at")))
        .withColumn("dq_flags", F.concat_ws(",",
                    F.when(F.col("f_sr04"), "SR04"), F.when(F.col("f_sr05"), "SR05"), F.when(F.col("f_sr06"), "SR06"),
                    F.when(F.col("f_sr07"), "SR07"), F.when(F.col("f_sr08"), "SR08")))
        .withColumn("_silver_run_id", F.lit(run.run_id))
        .withColumn("_silver_updated_at", now_ts)
        .drop("f_sr04", "f_sr05", "f_sr06", "f_sr07", "f_sr08", "reject_reason",
              "_raw_unique_key", "_raw_created_date", "_source_file")
    )

    merge_into(silver_sr, SR_TABLE, "t.unique_key = s.unique_key")
    run.rows_written = n_dedup

    new_wm = bronze.agg(F.max("_ingested_at")).first()[0]
    if new_wm is not None:
        set_watermark(SR_SOURCE, new_wm, run.run_id)
    checked.unpersist()

    total = spark.table(SR_TABLE).count()
    print(f"Merged {n_dedup:,} rows into {SR_TABLE}; table now holds {total:,} requests")
    sr_exit = run.succeed(f"quarantined {n_sr01 + n_sr02:,}; duplicates removed {n_valid - n_dedup:,}")
except Exception as exc:
    run.fail(exc)

# %% [markdown]
# ## 4 · Weather: type, de-duplicate and merge into Silver

# %%
WX_SOURCE, WX_TABLE = "silver_weather_hourly", "silver.weather_hourly"
wx_run = RunContext("weather", "silver", load_mode, pipeline_run_id)

try:
    wx_wm = None if load_mode == "backfill" else get_watermark(WX_SOURCE)
    wx_bronze = spark.table("bronze.weather_hourly")
    if wx_wm is not None:
        wx_bronze = wx_bronze.where(F.col("_ingested_at") > F.lit(wx_wm))
    wx_run.rows_read = wx_bronze.count()

    code = F.col("weather_code")
    wx_typed = wx_bronze.select(
        "borough",
        F.to_timestamp("observed_at").alias("observed_at"),
        F.col("temperature_2m").cast("double").alias("temperature_c"),
        F.col("apparent_temperature").cast("double").alias("feels_like_c"),
        F.col("relative_humidity_2m").cast("double").alias("humidity_pct"),
        F.col("precipitation").cast("double").alias("precipitation_mm"),
        F.col("rain").cast("double").alias("rain_mm"),
        F.col("snowfall").cast("double").alias("snowfall_cm"),
        F.col("wind_speed_10m").cast("double").alias("wind_speed_kmh"),
        F.col("weather_code").cast("int").alias("weather_code"),
        "api", "_ingested_at",
    ).withColumn("weather_condition",          # WMO weather interpretation codes
        F.when(code == 0, "Clear").when(code.isin(1, 2), "Partly cloudy").when(code == 3, "Overcast")
         .when(code.isin(45, 48), "Fog").when(code.between(51, 57), "Drizzle").when(code.between(61, 67), "Rain")
         .when(code.between(71, 77), "Snow").when(code.between(80, 82), "Rain showers")
         .when(code.between(85, 86), "Snow showers").when(code >= 95, "Thunderstorm").otherwise("Other"))

    has_reading = wx_typed.where(F.col("temperature_c").isNotNull() & (F.col("observed_at") <= now_ts))
    n_reading = has_reading.count()
    latest_wx = Window.partitionBy("borough", "observed_at").orderBy(F.col("_ingested_at").desc(), F.col("api"))
    silver_wx = (has_reading.withColumn("_rn", F.row_number().over(latest_wx)).where("_rn = 1")
                 .drop("_rn", "api")
                 .withColumn("observed_date", F.to_date("observed_at"))
                 .withColumn("_silver_run_id", F.lit(wx_run.run_id))
                 .withColumn("_silver_updated_at", now_ts))
    wx_run.rows_written = silver_wx.count()

    record_dq(wx_run.run_id, "silver", WX_TABLE, "WX01", "weather hour has a temperature reading",
              "drop row (not yet published)", wx_run.rows_read, wx_run.rows_read - n_reading)
    record_dq(wx_run.run_id, "silver", WX_TABLE, "WX02", "one row per borough and hour",
              "keep latest version", n_reading, n_reading - wx_run.rows_written)

    merge_into(silver_wx, WX_TABLE, "t.borough = s.borough AND t.observed_at = s.observed_at")
    new_wx_wm = wx_bronze.agg(F.max("_ingested_at")).first()[0]
    if new_wx_wm is not None:
        set_watermark(WX_SOURCE, new_wx_wm, wx_run.run_id)
    print(f"Merged {wx_run.rows_written:,} rows into {WX_TABLE}")
    wx_exit = wx_run.succeed()
except Exception as exc:
    wx_run.fail(exc)

# %% [markdown]
# ## 5 · Compact the tables and publish to the SQL endpoint

# %%
for table in (SR_TABLE, WX_TABLE):
    spark.sql(f"OPTIMIZE {table}")
refresh_sql_endpoint()

display(spark.sql(f"""
    SELECT rule_id, rule_description, action, rows_checked, rows_failed, failed_pct
    FROM meta.dq_results WHERE run_id IN ('{run.run_id}', '{wx_run.run_id}') ORDER BY rule_id"""))

# %%
notebookutils.notebook.exit(json.dumps({"ok": True, "service_requests": json.loads(sr_exit), "weather": json.loads(wx_exit)}))
