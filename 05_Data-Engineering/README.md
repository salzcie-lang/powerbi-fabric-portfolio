# 05 · Data Engineering: City Operations Data Platform (Microsoft Fabric)

Public REST APIs (NYC 311 service requests, Open-Meteo weather) to a Gold star schema, orchestrated daily in a Microsoft Fabric workspace.

![Architecture](exports/02%20Architecture.png)

## What it does

| Stage | Implementation |
|---|---|
| Ingest | Two PySpark notebooks page through the APIs with retry and back-off, driven by a control table (`meta.source_config`). High-watermark incremental loads with a look-back window; raw responses land as compressed JSON |
| Bronze | Append-only Delta tables, every column kept as text, with file, run and load-time lineage |
| Silver | Typed and validated, one row per business key. 10 data-quality rules with logged results, a quarantine table for bad rows, idempotent `MERGE` upserts |
| Gold | Fabric Warehouse star schema: 2 facts, 5 dimensions. T-SQL stored procedures load only what changed, inside a transaction |
| Reconcile | API vs Bronze and Silver vs Gold row counts are compared on every run. A mismatch fails the run |
| Orchestrate | One pipeline, `pl_city_ops_daily`, scheduled daily. A `load_mode` parameter switches between incremental and full backfill. Any failed step is logged and fails the run |
| Serve | Direct Lake semantic model on the Gold tables, plus a SQL endpoint and reporting views |

## Run evidence

The platform was deployed to a Fabric workspace and run end to end on 4 October 2026.

| Claim | Evidence |
|---|---|
| All 7 pipeline activities succeeded; the run started 19:31:19 and ended 19:37:50, about six and a half minutes | [Monitoring hub capture](screenshots/02_pipeline_run.png) |
| 3.01M service requests in Gold | [Warehouse query capture](screenshots/07_warehouse_query.png): the monthly totals from `gold.vw_daily_borough_summary` add up to 3,014,623 |
| Bronze and Silver tables exist in the lakehouse as described | [Lakehouse capture](screenshots/05_lakehouse.png) |
| Pipeline, notebooks, lakehouse, warehouse and semantic model are connected | [Lineage capture](screenshots/08_lineage.png) |

Row counts by layer (`_build/stats.json`): 86 landing files, 3.09M Bronze rows, 3.01M Silver requests, 3.01M Gold fact rows, 33,195 hourly weather readings.

Not tested: redeploying into a different workspace from this repository.

## Folders

| Folder | Contents |
|---|---|
| `exports/` | Architecture diagram and the 9-page case study (PNG + PDF) |
| `notebooks/` | Notebook sources (`# %%` cells). `nb_00_common` is the shared framework for logging, watermarks, retries and quality checks |
| `sql/` | Warehouse DDL, stored procedures, reconciliation, views |
| `pipeline/` | `pl_city_ops_daily` definition |
| `semantic_model/` | Direct Lake model (TMDL) on the Gold tables |
| `diagram/` | HTML sources for the diagram, cover and slides |
| `screenshots/` | Fabric portal captures used in the slides |
| `_build/` | Deploy, run, SQL, screenshot and render scripts |

## Rebuild or redeploy

Needs a Fabric workspace with a lakehouse and a warehouse, the Azure CLI (`az login`), Python with `pyodbc` and "ODBC Driver 17 for SQL Server". Workspace, notebook and warehouse ids in `pipeline/` and `semantic_model/` are placeholders such as `<workspace-id>`; replace them and `your-warehouse-endpoint` with your own values.

```bash
cp _build/env.example.sh _build/env.sh                 # then fill in your workspace ids
source _build/env.sh                                   # tokens from the Azure CLI login
python _build/build_notebooks.py $WS_ID $LH_ID lh_city_ops
python _build/fabric_api.py deploy Notebook nb_01_ingest_nyc311 _build/out/nb_01_ingest_nyc311.Notebook
python _build/run_sql.py wh_city_ops -f sql/01_schemas_and_tables.sql sql/02_load_dimensions.sql sql/03_load_facts.sql sql/04_reconcile_and_views.sql
python _build/fabric_api.py run DataPipeline pl_city_ops_daily Pipeline
python diagram/build_slides.py && python _build/render.py slide_03.html "exports/03 Orchestration.png" 1920 1080 2
python _build/make_pdf.py
```

Numbers shown on the diagram come from `_build/stats.json`; slide figures are in `diagram/build_slides.py`.

## Data sources

- [NYC Open Data: 311 Service Requests](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9) (Socrata API)
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
