# %% [markdown]
# # 01 · Ingest NYC 311 service requests → Bronze
#
# **Source:** NYC Open Data (Socrata REST API), dataset `erm2-nwe9`
# **Target:** `Files/landing/nyc311/` (raw JSON) → `bronze.nyc311_service_requests` (Delta, append-only)
#
# | Step | What happens |
# |---|---|
# | 1 | Read settings from `meta.source_config` and the high-watermark from `meta.watermarks` |
# | 2 | Call the API page by page with retry and back-off |
# | 3 | Land every page untouched as compressed JSON in the lakehouse `Files/` area |
# | 4 | Append to the Bronze Delta table with lineage columns, and reconcile the row count |
# | 5 | Advance the watermark and write the run to `meta.run_log` |

# %% tags=["parameters"]
# Parameters (set by the pipeline)
load_mode = "incremental"     # "incremental" or "backfill"
pipeline_run_id = ""

# %%
%run nb_00_common

# %%
import gzip, os
from concurrent.futures import ThreadPoolExecutor
from pyspark.sql.types import StringType, StructField, StructType

SOURCE = "nyc311"
BRONZE_TABLE = "bronze.nyc311_service_requests"

cfg = get_config(SOURCE)
watermark = get_watermark(SOURCE)
if watermark is None:
    load_mode = "backfill"        # first run: nothing to be incremental against

run = RunContext(SOURCE, "bronze", load_mode, pipeline_run_id)
landing_rel = f"Files/landing/nyc311/load_date={run.started_at:%Y-%m-%d}/run_id={run.run_id}"
landing_local = f"/lakehouse/default/{landing_rel}"
os.makedirs(landing_local, exist_ok=True)

# %% [markdown]
# ## 1 · Work out what to ask the API for
#
# 311 requests are **updated after they are created** (status changes, closure). A watermark on
# `created_date` alone would miss those updates, so the incremental filter also picks up rows whose
# `resolution_action_updated_date` moved past the watermark. A short look-back window covers late arrivals;
# the Silver merge makes re-reading the same row harmless.

# %%
now_utc = datetime.utcnow()
soql_ts = lambda d: d.strftime("%Y-%m-%dT%H:%M:%S")

if load_mode == "backfill":
    # One window per calendar month keeps each API query small and lets windows run in parallel
    windows = []
    cursor = datetime.combine(cfg["backfill_start"], datetime.min.time())
    while cursor < now_utc:
        nxt = (cursor.replace(day=1) + timedelta(days=32)).replace(day=1)
        windows.append((f"{cursor:%Y-%m}",
                        f"created_date >= '{soql_ts(cursor)}' AND created_date < '{soql_ts(nxt)}'"))
        cursor = nxt
else:
    since = watermark - timedelta(days=cfg["lookback_days"])
    windows = [("incremental",
                f"created_date > '{soql_ts(since)}' OR (resolution_action_updated_date > '{soql_ts(since)}' "
                f"AND resolution_action_updated_date <= '{soql_ts(now_utc)}')")]

print(f"watermark = {watermark}")
for name, where in windows:
    print(f"  window {name}: {where}")

# %% [markdown]
# ## 2 · Extract: paginated API calls, landed as raw JSON

# %%
session = requests.Session()
session.headers.update({"Accept": "application/json"})
page_size = cfg["page_size"]


def extract_window(window) -> int:
    """Pull every page for one window and land each page as newline-delimited JSON (gzip)."""
    name, where = window
    offset, part, rows = 0, 0, 0
    while True:
        page = http_get_json(session, cfg["base_url"],
                             {"$where": where, "$order": "unique_key", "$limit": page_size, "$offset": offset})
        if not page:
            break
        part += 1
        with gzip.open(f"{landing_local}/{name}_part-{part:04d}.json.gz", "wt", encoding="utf-8") as fh:
            for record in page:
                fh.write(json.dumps(record) + "\n")
        rows += len(page)
        offset += page_size
        if len(page) < page_size:
            break
    print(f"  window {name}: {rows:,} rows in {part} file(s)")
    return rows


try:
    with ThreadPoolExecutor(max_workers=3) as pool:
        run.rows_read = sum(pool.map(extract_window, windows))
    print(f"Extracted {run.rows_read:,} rows from the API")
except Exception as exc:
    run.fail(exc)

# %% [markdown]
# ## 3 · Load: append to Bronze exactly as received
#
# Bronze keeps every column as text, so nothing is lost or silently coerced. Lineage columns make
# any row traceable to the file and run that delivered it.

# %%
SOURCE_COLUMNS = [
    "unique_key", "created_date", "closed_date", "agency", "agency_name", "complaint_type", "descriptor",
    "descriptor_2", "location_type", "incident_zip", "incident_address", "street_name", "cross_street_1",
    "cross_street_2", "intersection_street_1", "intersection_street_2", "address_type", "city", "landmark",
    "facility_type", "status", "due_date", "resolution_description", "resolution_action_updated_date",
    "community_board", "council_district", "police_precinct", "bbl", "borough", "x_coordinate_state_plane",
    "y_coordinate_state_plane", "open_data_channel_type", "park_facility_name", "park_borough", "vehicle_type",
    "taxi_company_borough", "taxi_pick_up_location", "bridge_highway_name", "bridge_highway_direction",
    "road_ramp", "bridge_highway_segment", "latitude", "longitude", "location",
]
raw_schema = StructType([StructField(c, StringType(), True) for c in SOURCE_COLUMNS])

try:
    if run.rows_read > 0:
        (spark.read.schema(raw_schema).json(landing_rel)
            .withColumn("_ingested_at", F.lit(run.started_at).cast("timestamp"))
            .withColumn("_ingest_date", F.lit(run.started_at.date()).cast("date"))
            .withColumn("_source_file", F.col("_metadata.file_name"))
            .withColumn("_run_id", F.lit(run.run_id))
            .withColumn("_load_mode", F.lit(load_mode))
            .write.format("delta").mode("append").partitionBy("_ingest_date").saveAsTable(BRONZE_TABLE))
        run.rows_written = spark.table(BRONZE_TABLE).where(F.col("_run_id") == run.run_id).count()

    # Reconciliation: what the API returned must equal what landed in Bronze
    if run.rows_written != run.rows_read:
        raise ValueError(f"Reconciliation failed: API returned {run.rows_read:,}, Bronze has {run.rows_written:,}")
    print(f"Appended {run.rows_written:,} rows to {BRONZE_TABLE} (reconciled with API extract)")
except Exception as exc:
    run.fail(exc)

# %% [markdown]
# ## 4 · Advance the watermark and log the run
#
# The watermark moves only after the load has been reconciled, so a failed run is simply retried
# from the same point.

# %%
try:
    if run.rows_written > 0:
        # The source contains a few future-dated rows, so the watermark is capped at "now"
        new_wm = (spark.table(BRONZE_TABLE).where(F.col("_run_id") == run.run_id)
                  .select(F.max(F.least(F.to_timestamp("created_date"), F.lit(now_utc).cast("timestamp")))).first()[0])
        set_watermark(SOURCE, new_wm, run.run_id)
        print(f"Watermark advanced to {new_wm}")

    display(spark.sql(f"""
        SELECT _load_mode AS load_mode, count(*) AS rows, count(DISTINCT _source_file) AS files,
               min(created_date) AS first_created, max(created_date) AS last_created
        FROM {BRONZE_TABLE} WHERE _run_id = '{run.run_id}' GROUP BY _load_mode"""))
    exit_payload = run.succeed(f"{len(windows)} window(s)")
except Exception as exc:
    run.fail(exc)

# %%
notebookutils.notebook.exit(exit_payload)
