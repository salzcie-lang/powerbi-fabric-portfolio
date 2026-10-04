/* ============================================================================================
   etl.usp_reconcile
   Last step of the pipeline. Compares Silver with Gold and records the result. If the layers do
   not agree the procedure raises an error, the pipeline run fails and the failure path fires,
   so a report is never refreshed on top of incomplete data.
   ============================================================================================ */
CREATE OR ALTER PROCEDURE etl.usp_reconcile
    @pipeline_run_id VARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @now DATETIME2(6) = SYSUTCDATETIME(), @src BIGINT, @tgt BIGINT, @failures INT;

    /* 1. Every Silver request is in the fact table, exactly once */
    SELECT @src = COUNT_BIG(*) FROM lh_city_ops.silver.service_requests;
    SELECT @tgt = COUNT_BIG(*) FROM gold.fact_service_request;
    INSERT INTO etl.reconciliation_log
    VALUES (@now, @pipeline_run_id, 'service requests: silver rows = gold rows', @src, @tgt, @tgt - @src,
            CASE WHEN @src = @tgt THEN 'PASS' ELSE 'FAIL' END);

    SELECT @src = COUNT_BIG(*) FROM gold.fact_service_request;
    SELECT @tgt = COUNT_BIG(DISTINCT service_request_id) FROM gold.fact_service_request;
    INSERT INTO etl.reconciliation_log
    VALUES (@now, @pipeline_run_id, 'service requests: no duplicate keys in gold', @src, @tgt, @src - @tgt,
            CASE WHEN @src = @tgt THEN 'PASS' ELSE 'FAIL' END);

    /* 2. Closed-request totals agree, so a measure built on Gold matches Silver */
    SELECT @src = COUNT_BIG(*) FROM lh_city_ops.silver.service_requests WHERE is_closed = 1;
    SELECT @tgt = COUNT_BIG(*) FROM gold.fact_service_request WHERE is_closed = 1;
    INSERT INTO etl.reconciliation_log
    VALUES (@now, @pipeline_run_id, 'service requests: closed count matches', @src, @tgt, @tgt - @src,
            CASE WHEN @src = @tgt THEN 'PASS' ELSE 'FAIL' END);

    /* 3. Every borough-day of weather made it to the daily fact */
    SELECT @src = COUNT_BIG(*) FROM (SELECT DISTINCT borough, observed_date FROM lh_city_ops.silver.weather_hourly) x;
    SELECT @tgt = COUNT_BIG(*) FROM gold.fact_weather_daily;
    INSERT INTO etl.reconciliation_log
    VALUES (@now, @pipeline_run_id, 'weather: silver borough-days = gold rows', @src, @tgt, @tgt - @src,
            CASE WHEN @src = @tgt THEN 'PASS' ELSE 'FAIL' END);

    /* 4. No fact row points at a date that is missing from dim_date */
    SELECT @tgt = COUNT_BIG(*) FROM gold.fact_service_request f
    WHERE NOT EXISTS (SELECT 1 FROM gold.dim_date d WHERE d.date_key = f.created_date_key);
    INSERT INTO etl.reconciliation_log
    VALUES (@now, @pipeline_run_id, 'service requests: no orphan date keys', 0, @tgt, @tgt,
            CASE WHEN @tgt = 0 THEN 'PASS' ELSE 'FAIL' END);

    SELECT @failures = COUNT(*) FROM etl.reconciliation_log WHERE checked_at = @now AND result = 'FAIL';
    IF @failures > 0
        THROW 50001, 'Reconciliation failed: Silver and Gold do not agree. See etl.reconciliation_log.', 1;
END;
GO

/* ============================================================================================
   Reporting views
   ============================================================================================ */
CREATE OR ALTER VIEW gold.vw_daily_borough_summary
AS
/* One row per borough per day: request volumes next to that day's weather. */
SELECT d.full_date,
       d.year_month,
       d.day_name,
       d.is_weekend,
       b.borough_name,
       r.total_requests,
       r.closed_requests,
       r.avg_resolution_hours,
       r.heat_requests,
       r.noise_requests,
       r.street_requests,
       w.avg_temperature_c,
       w.min_temperature_c,
       w.precipitation_mm,
       w.snowfall_cm,
       w.is_wet_day,
       w.is_freezing_day
FROM (
    SELECT f.created_date_key, f.borough_key,
           COUNT_BIG(*) AS total_requests,
           SUM(CAST(f.is_closed AS INT)) AS closed_requests,
           CAST(AVG(f.resolution_hours) AS DECIMAL(12,1)) AS avg_resolution_hours,
           SUM(CASE WHEN c.complaint_type = 'HEAT/HOT WATER' THEN 1 ELSE 0 END) AS heat_requests,
           SUM(CASE WHEN c.complaint_category = 'Noise' THEN 1 ELSE 0 END) AS noise_requests,
           SUM(CASE WHEN c.complaint_category = 'Streets & Sidewalks' THEN 1 ELSE 0 END) AS street_requests
    FROM gold.fact_service_request f
    JOIN gold.dim_complaint_type c ON c.complaint_key = f.complaint_key
    GROUP BY f.created_date_key, f.borough_key
) r
JOIN gold.dim_date d    ON d.date_key = r.created_date_key
JOIN gold.dim_borough b ON b.borough_key = r.borough_key
LEFT JOIN gold.fact_weather_daily w ON w.date_key = r.created_date_key AND w.borough_key = r.borough_key;
GO

CREATE OR ALTER VIEW etl.vw_load_history
AS
/* Operations view: what ran, when, how long it took, how many rows moved. */
SELECT procedure_name, status, started_at, finished_at,
       DATEDIFF(SECOND, started_at, finished_at) AS duration_seconds,
       rows_inserted, rows_deleted, pipeline_run_id, message
FROM etl.load_log;
GO

/* ============================================================================================
   etl.usp_log_pipeline_failure
   Called by the pipeline's failure branch so that a failed run is recorded next to the
   successful ones and can be alerted on.
   ============================================================================================ */
CREATE OR ALTER PROCEDURE etl.usp_log_pipeline_failure
    @pipeline_run_id VARCHAR(100),
    @pipeline_name   VARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO etl.load_log
    VALUES (CAST(NEWID() AS VARCHAR(36)), @pipeline_run_id, @pipeline_name, SYSUTCDATETIME(), SYSUTCDATETIME(),
            NULL, NULL, 'Failed', 'Pipeline run failed. Open the run in the Monitoring hub for the failing activity.');
END;
GO
