# %% [markdown]
# # 00 · Common framework
#
# Shared by every notebook through `%run nb_00_common`, so logging, watermarks, API retries and
# data-quality checks behave the same way everywhere and are maintained in one place.
#
# | Component | Purpose |
# |---|---|
# | `meta.source_config` | Control table: endpoints, page size, look-back window. Changing a source needs no code change |
# | `meta.watermarks` | High-watermark per source for incremental loads |
# | `meta.run_log` | One audit row per notebook run: rows in, rows out, duration, status |
# | `meta.dq_results` | One row per data-quality rule per run |
# | `RunContext` | Opens a run, records the outcome (success or failure) and returns the exit payload |
# | `http_get_json` | REST call with exponential back-off on throttling and server errors |

# %%
import json, time, traceback, uuid
from datetime import datetime, timedelta

import requests
from pyspark.sql import functions as F

for _schema in ("meta", "bronze", "silver"):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {_schema}")

spark.sql("""
    CREATE TABLE IF NOT EXISTS meta.source_config (
        source STRING, base_url STRING, page_size INT, lookback_days INT,
        backfill_start DATE, is_enabled BOOLEAN, notes STRING
    ) USING DELTA""")
spark.sql("""
    CREATE TABLE IF NOT EXISTS meta.watermarks (
        source STRING, watermark_value TIMESTAMP, updated_at TIMESTAMP, run_id STRING
    ) USING DELTA""")
spark.sql("""
    CREATE TABLE IF NOT EXISTS meta.run_log (
        run_id STRING, pipeline_run_id STRING, source STRING, layer STRING, load_mode STRING,
        started_at TIMESTAMP, finished_at TIMESTAMP, duration_seconds DOUBLE,
        rows_read BIGINT, rows_written BIGINT, status STRING, message STRING
    ) USING DELTA""")
spark.sql("""
    CREATE TABLE IF NOT EXISTS meta.dq_results (
        run_id STRING, checked_at TIMESTAMP, layer STRING, table_name STRING, rule_id STRING,
        rule_description STRING, action STRING, rows_checked BIGINT, rows_failed BIGINT, failed_pct DOUBLE
    ) USING DELTA""")

# Seed the control table on first run only; afterwards it is maintained as data
if spark.table("meta.source_config").count() == 0:
    spark.sql("""
        INSERT INTO meta.source_config VALUES
        ('nyc311',  'https://data.cityofnewyork.us/resource/erm2-nwe9.json', 50000, 2, DATE'2026-01-01', true,
         'NYC Open Data (Socrata). 311 service requests, updated daily'),
        ('weather', 'https://archive-api.open-meteo.com/v1/archive',         0,     7, DATE'2026-01-01', true,
         'Open-Meteo hourly weather per borough. Recent days are revised, hence the 7-day look-back')""")

# %%
def get_config(source: str) -> dict:
    """Settings for one source from the control table."""
    row = spark.table("meta.source_config").where(F.col("source") == source).first()
    if row is None or not row["is_enabled"]:
        raise ValueError(f"Source '{source}' is missing or disabled in meta.source_config")
    return row.asDict()


def get_watermark(source: str):
    row = spark.table("meta.watermarks").where(F.col("source") == source).agg(F.max("watermark_value")).first()
    return row[0] if row else None


def set_watermark(source: str, value, run_id: str):
    """Replace the watermark for a source. Called only after the load has been verified."""
    spark.sql(f"DELETE FROM meta.watermarks WHERE source = '{source}'")
    spark.createDataFrame([(source, value, datetime.utcnow(), run_id)],
                          spark.table("meta.watermarks").schema).write.mode("append").saveAsTable("meta.watermarks")


def http_get_json(session: requests.Session, url: str, params: dict, max_attempts: int = 6, timeout: int = 300):
    """GET that retries on HTTP 429 / 5xx and network errors with exponential back-off."""
    for attempt in range(1, max_attempts + 1):
        try:
            resp = session.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code not in (429, 500, 502, 503, 504):
                resp.raise_for_status()
            reason = f"HTTP {resp.status_code}"
        except (requests.ConnectionError, requests.Timeout) as exc:
            reason = type(exc).__name__
        wait = min(2 ** attempt, 60)
        print(f"    retry {attempt}/{max_attempts} in {wait}s ({reason})")
        time.sleep(wait)
    raise RuntimeError(f"GET {url} failed after {max_attempts} attempts")


def record_dq(run_id: str, layer: str, table_name: str, rule_id: str, description: str, action: str,
              rows_checked: int, rows_failed: int):
    """Persist the outcome of one data-quality rule."""
    pct = round(100.0 * rows_failed / rows_checked, 4) if rows_checked else 0.0
    spark.createDataFrame(
        [(run_id, datetime.utcnow(), layer, table_name, rule_id, description, action,
          int(rows_checked), int(rows_failed), pct)],
        spark.table("meta.dq_results").schema).write.mode("append").saveAsTable("meta.dq_results")


class RunContext:
    """Audit wrapper for a notebook run. Every run ends with exactly one row in meta.run_log."""

    def __init__(self, source: str, layer: str, load_mode: str, pipeline_run_id: str = ""):
        self.run_id = uuid.uuid4().hex[:12]
        self.source, self.layer, self.load_mode = source, layer, load_mode
        self.pipeline_run_id = pipeline_run_id
        self.started_at = datetime.utcnow()
        self.rows_read = self.rows_written = 0
        print(f"[{layer}/{source}] run_id={self.run_id} load_mode={load_mode} started {self.started_at:%Y-%m-%d %H:%M:%S} UTC")

    def _log(self, status: str, message: str):
        finished = datetime.utcnow()
        spark.createDataFrame(
            [(self.run_id, self.pipeline_run_id, self.source, self.layer, self.load_mode, self.started_at, finished,
              (finished - self.started_at).total_seconds(), int(self.rows_read), int(self.rows_written),
              status, message[:2000])],
            spark.table("meta.run_log").schema).write.mode("append").saveAsTable("meta.run_log")

    def succeed(self, message: str = "") -> str:
        self._log("Succeeded", message)
        return json.dumps({"ok": True, "run_id": self.run_id, "source": self.source, "layer": self.layer,
                           "load_mode": self.load_mode, "rows_read": int(self.rows_read),
                           "rows_written": int(self.rows_written)})

    def fail(self, exc: Exception):
        """Log the failure, then re-raise so the pipeline activity is marked Failed."""
        self._log("Failed", f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")
        raise exc


def refresh_sql_endpoint():
    """Ask the lakehouse SQL endpoint to pick up new Delta commits now, so the Warehouse load that
    follows in the pipeline reads current data rather than waiting for the background sync."""
    ctx = notebookutils.runtime.context
    ws_id, lh_id = ctx["currentWorkspaceId"], ctx["defaultLakehouseId"]
    headers = {"Authorization": f"Bearer {notebookutils.credentials.getToken('pbi')}"}
    api = "https://api.fabric.microsoft.com/v1"
    lakehouse = requests.get(f"{api}/workspaces/{ws_id}/lakehouses/{lh_id}", headers=headers, timeout=60).json()
    endpoint_id = lakehouse["properties"]["sqlEndpointProperties"]["id"]
    resp = requests.post(f"{api}/workspaces/{ws_id}/sqlEndpoints/{endpoint_id}/refreshMetadata",
                         headers=headers, json={}, timeout=120)
    while resp.status_code == 202:
        time.sleep(int(resp.headers.get("Retry-After", 5)))
        resp = requests.get(resp.headers["Location"], headers=headers, timeout=60)
    resp.raise_for_status()
    print("SQL endpoint metadata refreshed")
