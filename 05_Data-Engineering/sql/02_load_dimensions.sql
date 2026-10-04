/* ============================================================================================
   etl.usp_load_dimensions
   Adds new dimension members from Silver (existing keys never change) and applies Type 1 updates.
   Every dimension has an "Unknown" member (key -1) so fact rows are never dropped for a missing
   attribute. Safe to re-run: a second run with no new data inserts nothing.
   ============================================================================================ */
CREATE OR ALTER PROCEDURE etl.usp_load_dimensions
    @pipeline_run_id VARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @load_id VARCHAR(36) = CAST(NEWID() AS VARCHAR(36)),
            @started DATETIME2(6) = SYSUTCDATETIME(),
            @rows BIGINT = 0;

    BEGIN TRY
        /* ---- Unknown members ---------------------------------------------------------------- */
        IF NOT EXISTS (SELECT 1 FROM gold.dim_agency WHERE agency_key = -1)
            INSERT INTO gold.dim_agency VALUES (-1, 'UNKNOWN', 'Unknown agency');
        IF NOT EXISTS (SELECT 1 FROM gold.dim_complaint_type WHERE complaint_key = -1)
            INSERT INTO gold.dim_complaint_type VALUES (-1, 'Unknown', 'Other');
        IF NOT EXISTS (SELECT 1 FROM gold.dim_borough WHERE borough_key = -1)
            INSERT INTO gold.dim_borough VALUES (-1, 'Unknown');
        IF NOT EXISTS (SELECT 1 FROM gold.dim_channel WHERE channel_key = -1)
            INSERT INTO gold.dim_channel VALUES (-1, 'Unknown');

        /* ---- dim_date: every date used by a fact --------------------------------------------- */
        INSERT INTO gold.dim_date
        SELECT YEAR(d) * 10000 + MONTH(d) * 100 + DAY(d),
               d, YEAR(d), DATEPART(QUARTER, d), MONTH(d), DATENAME(MONTH, d),
               CONVERT(VARCHAR(7), d, 23), DAY(d),
               DATEDIFF(DAY, '19000101', d) % 7 + 1,                      -- 1 = Monday, independent of DATEFIRST
               DATENAME(WEEKDAY, d),
               CASE WHEN DATEDIFF(DAY, '19000101', d) % 7 >= 5 THEN 1 ELSE 0 END
        FROM (
            SELECT created_date AS d FROM lh_city_ops.silver.service_requests
            UNION
            SELECT CAST(closed_at AS DATE) FROM lh_city_ops.silver.service_requests WHERE closed_at IS NOT NULL
            UNION
            SELECT observed_date FROM lh_city_ops.silver.weather_hourly
        ) src
        WHERE NOT EXISTS (SELECT 1 FROM gold.dim_date t WHERE t.full_date = src.d);
        SET @rows += @@ROWCOUNT;

        /* ---- dim_agency ---------------------------------------------------------------------- */
        INSERT INTO gold.dim_agency
        SELECT (SELECT ISNULL(MAX(agency_key), 0) FROM gold.dim_agency WHERE agency_key > 0)
                   + ROW_NUMBER() OVER (ORDER BY src.agency_code),
               src.agency_code, src.agency_name
        FROM (
            SELECT CAST(agency_code AS VARCHAR(20)) AS agency_code,
                   CAST(MAX(ISNULL(agency_name, agency_code)) AS VARCHAR(200)) AS agency_name
            FROM lh_city_ops.silver.service_requests
            WHERE agency_code IS NOT NULL
            GROUP BY agency_code
        ) src
        WHERE NOT EXISTS (SELECT 1 FROM gold.dim_agency t WHERE t.agency_code = src.agency_code);
        SET @rows += @@ROWCOUNT;

        /* ---- dim_complaint_type: raw types rolled up into a reporting category --------------- */
        INSERT INTO gold.dim_complaint_type
        SELECT (SELECT ISNULL(MAX(complaint_key), 0) FROM gold.dim_complaint_type WHERE complaint_key > 0)
                   + ROW_NUMBER() OVER (ORDER BY src.complaint_type),
               src.complaint_type,
               CASE
                   WHEN u LIKE 'NOISE%' THEN 'Noise'
                   WHEN u IN ('ILLEGAL PARKING', 'BLOCKED DRIVEWAY', 'ABANDONED VEHICLE', 'DERELICT VEHICLES',
                              'FOR HIRE VEHICLE COMPLAINT', 'TAXI COMPLAINT') THEN 'Parking & Vehicles'
                   WHEN u IN ('HEAT/HOT WATER', 'UNSANITARY CONDITION', 'PLUMBING', 'PAINT/PLASTER', 'DOOR/WINDOW',
                              'WATER LEAK', 'GENERAL', 'ELECTRIC', 'FLOORING/STAIRS', 'APPLIANCE', 'ELEVATOR',
                              'GENERAL CONSTRUCTION/PLUMBING', 'BUILDING/USE', 'SAFETY', 'OUTSIDE BUILDING')
                        THEN 'Housing & Buildings'
                   WHEN u IN ('STREET CONDITION', 'TRAFFIC SIGNAL CONDITION', 'STREET LIGHT CONDITION',
                              'SIDEWALK CONDITION', 'SNOW OR ICE', 'OBSTRUCTION', 'CURB CONDITION',
                              'STREET SIGN - DAMAGED', 'STREET SIGN - MISSING', 'HIGHWAY CONDITION')
                        THEN 'Streets & Sidewalks'
                   WHEN u IN ('DIRTY CONDITION', 'ILLEGAL DUMPING', 'MISSED COLLECTION', 'RODENT', 'GRAFFITI',
                              'RESIDENTIAL DISPOSAL COMPLAINT', 'COMMERCIAL DISPOSAL COMPLAINT', 'LITTER BASKET COMPLAINT')
                        OR u LIKE 'SANITATION%' THEN 'Sanitation'
                   WHEN u IN ('WATER SYSTEM', 'SEWER', 'WATER MAINTENANCE', 'WATER QUALITY', 'WATER CONSERVATION')
                        THEN 'Water & Sewer'
                   WHEN u LIKE '%TREE%' OR u IN ('MAINTENANCE OR FACILITY', 'ANIMAL IN A PARK', 'VIOLATION OF PARK RULES')
                        THEN 'Parks & Trees'
                   WHEN u IN ('ENCAMPMENT', 'HOMELESS PERSON ASSISTANCE', 'NON-EMERGENCY POLICE MATTER',
                              'VENDOR ENFORCEMENT', 'CONSUMER COMPLAINT', 'DRUG ACTIVITY', 'PANHANDLING')
                        THEN 'Public Safety & Social'
                   ELSE 'Other'
               END
        FROM (
            SELECT DISTINCT CAST(complaint_type AS VARCHAR(200)) AS complaint_type,
                            UPPER(CAST(complaint_type AS VARCHAR(200))) AS u
            FROM lh_city_ops.silver.service_requests
            WHERE complaint_type IS NOT NULL
        ) src
        WHERE NOT EXISTS (SELECT 1 FROM gold.dim_complaint_type t WHERE t.complaint_type = src.complaint_type);
        SET @rows += @@ROWCOUNT;

        /* ---- dim_borough --------------------------------------------------------------------- */
        INSERT INTO gold.dim_borough
        SELECT (SELECT ISNULL(MAX(borough_key), 0) FROM gold.dim_borough WHERE borough_key > 0)
                   + ROW_NUMBER() OVER (ORDER BY src.borough),
               src.borough
        FROM (
            SELECT CAST(borough AS VARCHAR(50)) AS borough FROM lh_city_ops.silver.service_requests WHERE borough <> 'UNKNOWN'
            UNION
            SELECT CAST(borough AS VARCHAR(50)) FROM lh_city_ops.silver.weather_hourly
        ) src
        WHERE NOT EXISTS (SELECT 1 FROM gold.dim_borough t WHERE t.borough_name = src.borough);
        SET @rows += @@ROWCOUNT;

        /* ---- dim_channel --------------------------------------------------------------------- */
        INSERT INTO gold.dim_channel
        SELECT (SELECT ISNULL(MAX(channel_key), 0) FROM gold.dim_channel WHERE channel_key > 0)
                   + ROW_NUMBER() OVER (ORDER BY src.channel),
               src.channel
        FROM (
            SELECT DISTINCT CAST(channel AS VARCHAR(50)) AS channel
            FROM lh_city_ops.silver.service_requests WHERE channel <> 'UNKNOWN'
        ) src
        WHERE NOT EXISTS (SELECT 1 FROM gold.dim_channel t WHERE t.channel_name = src.channel);
        SET @rows += @@ROWCOUNT;

        /* ---- Type 1 change: an agency renamed at source is renamed here ------------------------ */
        UPDATE d
        SET agency_name = s.agency_name
        FROM gold.dim_agency d
        JOIN (SELECT CAST(agency_code AS VARCHAR(20)) AS agency_code,
                     CAST(MAX(ISNULL(agency_name, agency_code)) AS VARCHAR(200)) AS agency_name
              FROM lh_city_ops.silver.service_requests WHERE agency_code IS NOT NULL GROUP BY agency_code) s
          ON s.agency_code = d.agency_code
        WHERE d.agency_name <> s.agency_name;

        INSERT INTO etl.load_log
        VALUES (@load_id, @pipeline_run_id, 'etl.usp_load_dimensions', @started, SYSUTCDATETIME(), @rows, 0, 'Succeeded', NULL);
    END TRY
    BEGIN CATCH
        DECLARE @msg VARCHAR(4000) = CAST(ERROR_MESSAGE() AS VARCHAR(4000));
        INSERT INTO etl.load_log
        VALUES (@load_id, @pipeline_run_id, 'etl.usp_load_dimensions', @started, SYSUTCDATETIME(), NULL, NULL, 'Failed', @msg);
        THROW;
    END CATCH
END;
GO
