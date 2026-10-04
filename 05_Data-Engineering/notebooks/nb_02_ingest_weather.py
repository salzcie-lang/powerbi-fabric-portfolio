# %% [markdown]
# # 02 · Ingest hourly weather → Bronze
#
# **Source:** Open-Meteo REST API (historical archive + recent observations), one call per NYC borough
# **Target:** `Files/landing/weather/` (raw JSON) → `bronze.weather_hourly` (Delta, append-only)
#
# The weather feed is the second source in this solution. It is conformed to the 311 data on
# **borough + hour**, which lets the Gold layer answer questions such as "do heating complaints
# rise when the temperature drops?".

# %% tags=["parameters"]
# Parameters (set by the pipeline)
load_mode = "incremental"     # "incremental" or "backfill"
pipeline_run_id = ""

# %%
%run nb_00_common

# %%
import os

SOURCE = "weather"
BRONZE_TABLE = "bronze.weather_hourly"
RECENT_URL = "https://api.open-meteo.com/v1/forecast"   # the archive lags a few days; this covers the gap
HOURLY_VARS = ["temperature_2m", "apparent_temperature", "relative_humidity_2m", "precipitation",
               "rain", "snowfall", "wind_speed_10m", "weather_code"]
BOROUGHS = {            # representative point per borough
    "MANHATTAN":     (40.7831, -73.9712),
    "BROOKLYN":      (40.6782, -73.9442),
    "QUEENS":        (40.7282, -73.7949),
    "BRONX":         (40.8448, -73.8648),
    "STATEN ISLAND": (40.5795, -74.1502),
}

cfg = get_config(SOURCE)
watermark = get_watermark(SOURCE)
if watermark is None:
    load_mode = "backfill"

run = RunContext(SOURCE, "bronze", load_mode, pipeline_run_id)
landing_rel = f"Files/landing/weather/load_date={run.started_at:%Y-%m-%d}/run_id={run.run_id}"
landing_local = f"/lakehouse/default/{landing_rel}"
os.makedirs(landing_local, exist_ok=True)

# %% [markdown]
# ## 1 · Extract: one call per borough, landed as raw JSON
#
# A backfill reads the historical archive. Every run also reads the last few days from the recent
# endpoint, because recent weather observations are revised after the fact.

# %%
session = requests.Session()
common = {"hourly": ",".join(HOURLY_VARS), "timezone": "America/New_York"}   # same clock as the 311 data
today = datetime.utcnow().date()

try:
    calls = 0
    for borough, (lat, lon) in BOROUGHS.items():
        requests_to_make = [("recent", RECENT_URL,
                             {"latitude": lat, "longitude": lon, "past_days": cfg["lookback_days"], "forecast_days": 1})]
        if load_mode == "backfill":
            requests_to_make.insert(0, ("archive", cfg["base_url"],
                                        {"latitude": lat, "longitude": lon,
                                         "start_date": str(cfg["backfill_start"]),
                                         "end_date": str(today - timedelta(days=cfg["lookback_days"]))}))
        for api_name, url, params in requests_to_make:
            payload = http_get_json(session, url, {**params, **common})
            with open(f"{landing_local}/{api_name}_{borough.replace(' ', '_').lower()}.json", "w") as fh:
                json.dump({"borough": borough, "api": api_name, "response": payload}, fh)
            calls += 1
            print(f"  {borough:<14} {api_name:<8} {len(payload['hourly']['time']):>6,} hourly rows")
    print(f"{calls} API calls landed in {landing_rel}")
except Exception as exc:
    run.fail(exc)

# %% [markdown]
# ## 2 · Load: flatten the hourly arrays and append to Bronze
#
# The API returns one array per measure. They are zipped into one row per borough and hour and kept
# as text; typing and de-duplication happen in Silver.

# %%
try:
    raw = spark.read.option("multiLine", True).json(landing_rel)
    zipped = F.arrays_zip(F.col("response.hourly.time").alias("time"),
                          *[F.col(f"response.hourly.{v}").alias(v) for v in HOURLY_VARS])
    bronze_df = (
        raw.select("borough", "api",
                   F.col("response.latitude").cast("string").alias("latitude"),
                   F.col("response.longitude").cast("string").alias("longitude"),
                   F.explode(zipped).alias("h"), F.col("_metadata.file_name").alias("_source_file"))
           .select("borough", "api", "latitude", "longitude",
                   F.col("h.time").alias("observed_at"),
                   *[F.col(f"h.{v}").cast("string").alias(v) for v in HOURLY_VARS],
                   F.lit(run.started_at).cast("timestamp").alias("_ingested_at"),
                   F.lit(run.started_at.date()).cast("date").alias("_ingest_date"),
                   "_source_file",
                   F.lit(run.run_id).alias("_run_id"),
                   F.lit(load_mode).alias("_load_mode"))
    )
    run.rows_read = bronze_df.count()
    bronze_df.write.format("delta").mode("append").partitionBy("_ingest_date").saveAsTable(BRONZE_TABLE)
    run.rows_written = spark.table(BRONZE_TABLE).where(F.col("_run_id") == run.run_id).count()

    if run.rows_written != run.rows_read:
        raise ValueError(f"Reconciliation failed: parsed {run.rows_read:,}, Bronze has {run.rows_written:,}")
    print(f"Appended {run.rows_written:,} rows to {BRONZE_TABLE} (reconciled)")
except Exception as exc:
    run.fail(exc)

# %%
try:
    set_watermark(SOURCE, datetime.utcnow(), run.run_id)
    display(spark.sql(f"""
        SELECT borough, api, count(*) AS hours, min(observed_at) AS first_hour, max(observed_at) AS last_hour
        FROM {BRONZE_TABLE} WHERE _run_id = '{run.run_id}' GROUP BY borough, api ORDER BY borough, api"""))
    exit_payload = run.succeed(f"{calls} API calls")
except Exception as exc:
    run.fail(exc)

# %%
notebookutils.notebook.exit(exit_payload)
