/* ============================================================================================
   wh_city_ops · Gold layer · schemas and tables
   Star schema for reporting. Loaded by the stored procedures in 02_/03_ from lh_city_ops.silver.
   ============================================================================================ */

IF SCHEMA_ID('gold') IS NULL EXEC('CREATE SCHEMA gold');
GO
IF SCHEMA_ID('etl') IS NULL EXEC('CREATE SCHEMA etl');
GO

/* ---------- ETL control tables --------------------------------------------------------------- */
IF OBJECT_ID('etl.watermark') IS NULL
CREATE TABLE etl.watermark (
    table_name        VARCHAR(100) NOT NULL,
    watermark_value   DATETIME2(6) NOT NULL,
    updated_at        DATETIME2(6) NOT NULL
);
GO
IF OBJECT_ID('etl.load_log') IS NULL
CREATE TABLE etl.load_log (
    load_id           VARCHAR(36)   NOT NULL,
    pipeline_run_id   VARCHAR(100)  NULL,
    procedure_name    VARCHAR(100)  NOT NULL,
    started_at        DATETIME2(6)  NOT NULL,
    finished_at       DATETIME2(6)  NULL,
    rows_inserted     BIGINT        NULL,
    rows_deleted      BIGINT        NULL,
    status            VARCHAR(20)   NOT NULL,
    message           VARCHAR(4000) NULL
);
GO
IF OBJECT_ID('etl.reconciliation_log') IS NULL
CREATE TABLE etl.reconciliation_log (
    checked_at        DATETIME2(6)  NOT NULL,
    pipeline_run_id   VARCHAR(100)  NULL,
    check_name        VARCHAR(100)  NOT NULL,
    source_value      BIGINT        NULL,
    target_value      BIGINT        NULL,
    difference        BIGINT        NULL,
    result            VARCHAR(10)   NOT NULL
);
GO

/* ---------- Dimensions ----------------------------------------------------------------------- */
IF OBJECT_ID('gold.dim_date') IS NULL
CREATE TABLE gold.dim_date (
    date_key          INT          NOT NULL,     -- yyyymmdd
    full_date         DATE         NOT NULL,
    year_number       INT          NOT NULL,
    quarter_number    INT          NOT NULL,
    month_number      INT          NOT NULL,
    month_name        VARCHAR(10)  NOT NULL,
    year_month        VARCHAR(7)   NOT NULL,     -- yyyy-mm
    day_of_month      INT          NOT NULL,
    day_of_week       INT          NOT NULL,     -- 1 = Monday
    day_name          VARCHAR(10)  NOT NULL,
    is_weekend        BIT          NOT NULL
);
GO
IF OBJECT_ID('gold.dim_agency') IS NULL
CREATE TABLE gold.dim_agency (
    agency_key        INT          NOT NULL,
    agency_code       VARCHAR(20)  NOT NULL,
    agency_name       VARCHAR(200) NOT NULL
);
GO
IF OBJECT_ID('gold.dim_complaint_type') IS NULL
CREATE TABLE gold.dim_complaint_type (
    complaint_key       INT          NOT NULL,
    complaint_type      VARCHAR(200) NOT NULL,
    complaint_category  VARCHAR(50)  NOT NULL
);
GO
IF OBJECT_ID('gold.dim_borough') IS NULL
CREATE TABLE gold.dim_borough (
    borough_key       INT          NOT NULL,
    borough_name      VARCHAR(50)  NOT NULL
);
GO
IF OBJECT_ID('gold.dim_channel') IS NULL
CREATE TABLE gold.dim_channel (
    channel_key       INT          NOT NULL,
    channel_name      VARCHAR(50)  NOT NULL
);
GO

/* ---------- Facts ---------------------------------------------------------------------------- */
IF OBJECT_ID('gold.fact_service_request') IS NULL
CREATE TABLE gold.fact_service_request (
    service_request_id  BIGINT       NOT NULL,   -- source unique_key (grain: one row per request)
    created_date_key    INT          NOT NULL,
    closed_date_key     INT          NULL,
    agency_key          INT          NOT NULL,
    complaint_key       INT          NOT NULL,
    borough_key         INT          NOT NULL,
    channel_key         INT          NOT NULL,
    created_at          DATETIME2(6) NOT NULL,
    closed_at           DATETIME2(6) NULL,
    created_hour        INT          NOT NULL,   -- 0-23
    status              VARCHAR(50)  NOT NULL,
    incident_zip        VARCHAR(5)   NULL,
    latitude            FLOAT        NULL,
    longitude           FLOAT        NULL,
    is_closed           BIT          NOT NULL,
    resolution_hours    DECIMAL(12,2) NULL,
    closed_within_due   BIT          NULL,
    has_dq_flag         BIT          NOT NULL,
    loaded_at           DATETIME2(6) NOT NULL
);
GO
IF OBJECT_ID('gold.fact_weather_daily') IS NULL
CREATE TABLE gold.fact_weather_daily (
    date_key            INT          NOT NULL,   -- grain: one row per borough per day
    borough_key         INT          NOT NULL,
    avg_temperature_c   DECIMAL(5,1) NULL,
    min_temperature_c   DECIMAL(5,1) NULL,
    max_temperature_c   DECIMAL(5,1) NULL,
    precipitation_mm    DECIMAL(7,1) NULL,
    snowfall_cm         DECIMAL(7,1) NULL,
    max_wind_speed_kmh  DECIMAL(5,1) NULL,
    hours_observed      INT          NOT NULL,
    is_wet_day          BIT          NOT NULL,
    is_freezing_day     BIT          NOT NULL,
    loaded_at           DATETIME2(6) NOT NULL
);
GO

/* ---------- Keys (not enforced in Fabric Warehouse; they document the model and help the optimiser
              and Power BI detect relationships) ------------------------------------------------ */
IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'pk_dim_date')
    ALTER TABLE gold.dim_date ADD CONSTRAINT pk_dim_date PRIMARY KEY NONCLUSTERED (date_key) NOT ENFORCED;
GO
IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'pk_dim_agency')
    ALTER TABLE gold.dim_agency ADD CONSTRAINT pk_dim_agency PRIMARY KEY NONCLUSTERED (agency_key) NOT ENFORCED;
GO
IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'pk_dim_complaint_type')
    ALTER TABLE gold.dim_complaint_type ADD CONSTRAINT pk_dim_complaint_type PRIMARY KEY NONCLUSTERED (complaint_key) NOT ENFORCED;
GO
IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'pk_dim_borough')
    ALTER TABLE gold.dim_borough ADD CONSTRAINT pk_dim_borough PRIMARY KEY NONCLUSTERED (borough_key) NOT ENFORCED;
GO
IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'pk_dim_channel')
    ALTER TABLE gold.dim_channel ADD CONSTRAINT pk_dim_channel PRIMARY KEY NONCLUSTERED (channel_key) NOT ENFORCED;
GO
IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'pk_fact_service_request')
    ALTER TABLE gold.fact_service_request ADD CONSTRAINT pk_fact_service_request PRIMARY KEY NONCLUSTERED (service_request_id) NOT ENFORCED;
GO
