/* ============================================================================================
   etl.usp_load_fact_service_request
   Incremental load: only Silver rows changed since the last successful load are replaced.
   Delete + insert runs in one transaction with the watermark update, so a failure leaves the
   fact table and the watermark exactly as they were.
   ============================================================================================ */
CREATE OR ALTER PROCEDURE etl.usp_load_fact_service_request
    @pipeline_run_id VARCHAR(100) = NULL,
    @full_reload BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @load_id VARCHAR(36) = CAST(NEWID() AS VARCHAR(36)),
            @started DATETIME2(6) = SYSUTCDATETIME(),
            @deleted BIGINT = 0, @inserted BIGINT = 0,
            @wm DATETIME2(6), @new_wm DATETIME2(6);

    SELECT @wm = MAX(watermark_value) FROM etl.watermark WHERE table_name = 'gold.fact_service_request';
    IF @wm IS NULL OR @full_reload = 1 SET @wm = '1900-01-01';
    SELECT @new_wm = MAX(_silver_updated_at) FROM lh_city_ops.silver.service_requests;

    BEGIN TRY
        BEGIN TRANSACTION;

        DELETE f
        FROM gold.fact_service_request f
        WHERE @full_reload = 1
           OR EXISTS (SELECT 1 FROM lh_city_ops.silver.service_requests s
                      WHERE s.unique_key = f.service_request_id AND s._silver_updated_at > @wm);
        SET @deleted = @@ROWCOUNT;

        INSERT INTO gold.fact_service_request
        SELECT s.unique_key,
               YEAR(s.created_date) * 10000 + MONTH(s.created_date) * 100 + DAY(s.created_date),
               YEAR(s.closed_at) * 10000 + MONTH(s.closed_at) * 100 + DAY(s.closed_at),
               ISNULL(a.agency_key, -1),
               ISNULL(c.complaint_key, -1),
               ISNULL(b.borough_key, -1),
               ISNULL(ch.channel_key, -1),
               s.created_at,
               s.closed_at,
               DATEPART(HOUR, s.created_at),
               CAST(s.status AS VARCHAR(50)),
               CAST(s.incident_zip AS VARCHAR(5)),
               s.latitude,
               s.longitude,
               CAST(s.is_closed AS BIT),
               CAST(s.resolution_hours AS DECIMAL(12,2)),
               CAST(s.closed_within_due AS BIT),
               CASE WHEN s.dq_flags <> '' THEN 1 ELSE 0 END,
               SYSUTCDATETIME()
        FROM lh_city_ops.silver.service_requests s
        LEFT JOIN gold.dim_agency         a  ON a.agency_code    = s.agency_code
        LEFT JOIN gold.dim_complaint_type c  ON c.complaint_type = s.complaint_type
        LEFT JOIN gold.dim_borough        b  ON b.borough_name   = s.borough
        LEFT JOIN gold.dim_channel        ch ON ch.channel_name  = s.channel
        WHERE s._silver_updated_at > @wm;
        SET @inserted = @@ROWCOUNT;

        DELETE FROM etl.watermark WHERE table_name = 'gold.fact_service_request';
        IF @new_wm IS NOT NULL
            INSERT INTO etl.watermark VALUES ('gold.fact_service_request', @new_wm, SYSUTCDATETIME());

        COMMIT TRANSACTION;

        INSERT INTO etl.load_log
        VALUES (@load_id, @pipeline_run_id, 'etl.usp_load_fact_service_request', @started, SYSUTCDATETIME(),
                @inserted, @deleted, 'Succeeded', NULL);
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @msg VARCHAR(4000) = CAST(ERROR_MESSAGE() AS VARCHAR(4000));
        INSERT INTO etl.load_log
        VALUES (@load_id, @pipeline_run_id, 'etl.usp_load_fact_service_request', @started, SYSUTCDATETIME(),
                NULL, NULL, 'Failed', @msg);
        THROW;
    END CATCH
END;
GO

/* ============================================================================================
   etl.usp_load_fact_weather_daily
   Rolls hourly weather up to one row per borough per day. Only days touched since the last load
   are rebuilt (recent observations are revised by the source).
   ============================================================================================ */
CREATE OR ALTER PROCEDURE etl.usp_load_fact_weather_daily
    @pipeline_run_id VARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @load_id VARCHAR(36) = CAST(NEWID() AS VARCHAR(36)),
            @started DATETIME2(6) = SYSUTCDATETIME(),
            @deleted BIGINT = 0, @inserted BIGINT = 0,
            @wm DATETIME2(6), @new_wm DATETIME2(6);

    SELECT @wm = MAX(watermark_value) FROM etl.watermark WHERE table_name = 'gold.fact_weather_daily';
    IF @wm IS NULL SET @wm = '1900-01-01';
    SELECT @new_wm = MAX(_silver_updated_at) FROM lh_city_ops.silver.weather_hourly;

    BEGIN TRY
        BEGIN TRANSACTION;

        DELETE f
        FROM gold.fact_weather_daily f
        WHERE EXISTS (SELECT 1 FROM lh_city_ops.silver.weather_hourly w
                      WHERE w._silver_updated_at > @wm
                        AND YEAR(w.observed_date) * 10000 + MONTH(w.observed_date) * 100 + DAY(w.observed_date) = f.date_key);
        SET @deleted = @@ROWCOUNT;

        INSERT INTO gold.fact_weather_daily
        SELECT YEAR(w.observed_date) * 10000 + MONTH(w.observed_date) * 100 + DAY(w.observed_date),
               ISNULL(b.borough_key, -1),
               CAST(AVG(w.temperature_c) AS DECIMAL(5,1)),
               CAST(MIN(w.temperature_c) AS DECIMAL(5,1)),
               CAST(MAX(w.temperature_c) AS DECIMAL(5,1)),
               CAST(SUM(w.precipitation_mm) AS DECIMAL(7,1)),
               CAST(SUM(w.snowfall_cm) AS DECIMAL(7,1)),
               CAST(MAX(w.wind_speed_kmh) AS DECIMAL(5,1)),
               COUNT(*),
               CASE WHEN SUM(w.precipitation_mm) >= 1.0 THEN 1 ELSE 0 END,
               CASE WHEN MIN(w.temperature_c) <= 0 THEN 1 ELSE 0 END,
               SYSUTCDATETIME()
        FROM lh_city_ops.silver.weather_hourly w
        LEFT JOIN gold.dim_borough b ON b.borough_name = w.borough
        WHERE w.observed_date IN (SELECT DISTINCT observed_date FROM lh_city_ops.silver.weather_hourly
                                  WHERE _silver_updated_at > @wm)
        GROUP BY w.observed_date, b.borough_key;
        SET @inserted = @@ROWCOUNT;

        DELETE FROM etl.watermark WHERE table_name = 'gold.fact_weather_daily';
        IF @new_wm IS NOT NULL
            INSERT INTO etl.watermark VALUES ('gold.fact_weather_daily', @new_wm, SYSUTCDATETIME());

        COMMIT TRANSACTION;

        INSERT INTO etl.load_log
        VALUES (@load_id, @pipeline_run_id, 'etl.usp_load_fact_weather_daily', @started, SYSUTCDATETIME(),
                @inserted, @deleted, 'Succeeded', NULL);
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @msg VARCHAR(4000) = CAST(ERROR_MESSAGE() AS VARCHAR(4000));
        INSERT INTO etl.load_log
        VALUES (@load_id, @pipeline_run_id, 'etl.usp_load_fact_weather_daily', @started, SYSUTCDATETIME(),
                NULL, NULL, 'Failed', @msg);
        THROW;
    END CATCH
END;
GO
