"""Generate the case-study slide pages (diagram/slide_NN.html) from the specs below."""
from pathlib import Path

here = Path(__file__).resolve().parent

CSS = """
.canvas { width: 1920px; height: 1080px; padding: 52px 60px 44px; display: flex; flex-direction: column; }
.top { display: flex; align-items: flex-start; justify-content: space-between; }
.kicker { font-size: 14px; font-weight: 700; letter-spacing: 0.16em; color: var(--accent); text-transform: uppercase; }
h1 { font-size: 46px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.08; margin-top: 10px; max-width: 1300px; }
.lead { font-size: 20px; color: var(--ink-2); margin-top: 12px; max-width: 1150px; line-height: 1.4; }
.pageno { font-size: 14px; color: var(--ink-3); font-weight: 600; letter-spacing: 0.08em; white-space: nowrap; padding-top: 4px; }
.body { display: grid; grid-template-columns: 470px minmax(0, 1fr); gap: 44px; margin-top: 30px; flex: 1; min-height: 0; }
.points { display: flex; flex-direction: column; gap: 16px; }
.point { padding: 18px 20px; }
.point h3 { font-size: 19px; font-weight: 700; display: flex; gap: 10px; align-items: baseline; }
.point h3 b { color: var(--accent); font-size: 14px; font-weight: 800; }
.point p { font-size: 15.5px; line-height: 1.5; color: var(--ink-2); margin-top: 7px; }
code { font-family: 'JetBrains Mono', Consolas, monospace; font-size: 0.88em; color: var(--teal); }
.stats { display: flex; gap: 14px; margin-top: auto; }
.statbox { flex: 1; padding: 14px 18px; border-radius: 14px; background: rgba(255, 210, 31, 0.08); border: 1px solid rgba(255, 210, 31, 0.35); }
.statbox .v { font-size: 30px; font-weight: 800; letter-spacing: -0.01em; }
.statbox .l { font-size: 13px; color: var(--ink-2); margin-top: 3px; line-height: 1.35; }
.shots { display: flex; flex-direction: column; gap: 18px; min-height: 0; }
.frame { border-radius: 14px; overflow: hidden; border: 1px solid rgba(255,255,255,0.18); box-shadow: 0 24px 60px rgba(0,0,0,0.5), 0 0 0 6px rgba(255,255,255,0.03); background: #fff; position: relative; }
.frame img { display: block; width: 100%; }
.cap { font-size: 13.5px; color: var(--ink-3); margin-top: -8px; }
.cap b { color: var(--ink-2); font-weight: 600; }
table.dq { width: 100%; border-collapse: collapse; font-size: 15px; }
table.dq th { text-align: left; font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); padding: 0 14px 9px; font-weight: 700; }
table.dq td { padding: 9px 14px; border-top: 1px solid var(--line); color: var(--ink-2); }
table.dq td.n { text-align: right; font-variant-numeric: tabular-nums; color: var(--ink); font-weight: 600; }
table.dq td.id { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--teal); }
table.dq th.n { text-align: right; }
.pill { font-size: 12px; font-weight: 700; border-radius: 999px; padding: 3px 10px; }
.pill.ok { background: rgba(63,224,197,0.14); color: var(--teal); }
.pill.fix { background: rgba(255,210,31,0.14); color: var(--accent); }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-top: 30px; }
.std { padding: 20px 22px; }
.std .tick { width: 30px; height: 30px; border-radius: 9px; background: rgba(63,224,197,0.15); color: var(--teal); display: grid; place-items: center; font-weight: 800; font-size: 17px; }
.std h3 { font-size: 18px; font-weight: 700; margin-top: 12px; }
.std p { font-size: 14.5px; color: var(--ink-2); line-height: 1.5; margin-top: 6px; }
.band { display: grid; grid-template-columns: repeat(5, 1fr); gap: 18px; margin-top: 24px; }
.stack { margin-top: auto; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.stack span { font-size: 14px; font-weight: 600; color: var(--ink-2); border: 1px solid var(--line); border-radius: 999px; padding: 6px 14px; }
.stack .lbl { border: 0; padding-left: 0; color: var(--ink-3); letter-spacing: 0.1em; text-transform: uppercase; font-size: 12px; }
"""


def page(n, total, kicker, title, lead, body):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<link rel="stylesheet" href="base.css"><style>{CSS}</style></head><body><div class="canvas">
<div class="top"><div><div class="kicker">{kicker}</div><h1>{title}</h1><div class="lead">{lead}</div></div>
<div class="pageno">CITY OPERATIONS DATA PLATFORM &nbsp;·&nbsp; {n:02d} / {total:02d}</div></div>
{body}</div></body></html>"""


def points(items):
    return "".join(f'<div class="panel point"><h3><b>{i:02d}</b>{h}</h3><p>{p}</p></div>' for i, (h, p) in enumerate(items, 1))


def stats(items):
    return '<div class="stats">' + "".join(
        f'<div class="statbox"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in items) + "</div>"


def shot(src, style=""):
    return f'<div class="frame" style="{style}"><img src="../screenshots/{src}"></div>'


def cap(html, style=""):
    return f'<div class="cap" style="{style}">{html}</div>'


def two_col(pts, sts, right):
    return f'<div class="body"><div class="points">{points(pts)}{stats(sts)}</div><div class="shots">{right}</div></div>'


TOTAL = 9
slides = {}

slides[3] = page(3, TOTAL, "Orchestration · Data Pipeline", "One pipeline runs the whole load, every day",
    "Ingestion, transformation, the warehouse load and the checks run as a single scheduled job, with one place to look when something goes wrong.",
    two_col([
        ("Each step waits for the one before", "Each step starts only when the step before it has succeeded. The two API ingests run in parallel; the warehouse loads run in sequence to avoid write conflicts."),
        ("A failure is logged and fails the run", "Any failed step triggers a branch that records the failure and marks the run as failed. An email or Teams alert plugs in at that point."),
        ("One parameter, two modes", "<code>load_mode</code> switches the same pipeline between the daily incremental load and a full historical backfill."),
    ], [("6 min 46 s", "full daily run, API to Gold"), ("7 of 7", "activities succeeded; scheduled daily at 06:00")],
    shot("01_pipeline_canvas.png") + cap("<b>Pipeline canvas.</b> The last two steps are the failure branch.")
    + shot("02_pipeline_run.png") + cap("<b>Monitoring hub.</b> A real run: every activity with its status and duration.")))

slides[4] = page(4, TOTAL, "Ingestion · PySpark notebooks", "APIs are read safely and landed untouched",
    "The NYC 311 API returns 50,000 rows per page, and its records keep changing after they are created. The ingest is built around both facts.",
    two_col([
        ("Incremental by watermark", "Only records created or updated since the last run are requested, with a short look-back for late changes. The daily run moved 36,400 rows instead of 3 million."),
        ("API calls that retry", "The notebook pages through the API and splits a backfill into monthly windows that run in parallel. When the API throttles, times out or returns a server error, the call is retried with exponential back-off."),
        ("Row counts checked before the watermark moves", "Rows returned by the API must equal rows landed in Bronze. Only then does the watermark advance, so a failed run simply retries from the same point."),
    ], [("3,014,623", "rows backfilled in 21 minutes, reconciled to the row"), ("42 s", "daily incremental ingest")],
    shot("03_notebook_ingest.png") + cap("<b>Notebook header.</b> Each notebook documents its own source, target and steps.")
    + shot("04_notebook_code.png") + cap("<b>Extraction loop.</b> Page, land as compressed JSON, repeat. Failures are logged and re-raised.")))

slides[5] = page(5, TOTAL, "Storage · Lakehouse on OneLake", "Three layers, each with one job",
    "Raw data is never edited, and clean data is never mixed with raw. Every layer is an open Delta table that Spark, SQL and Power BI read without copies.",
    two_col([
        ("Landing and Bronze: the record of what arrived", "Raw API responses are kept as files, then appended to Bronze with the file name, run id and load time on every row. Any number can be traced back to its source."),
        ("Silver: one trusted row per request", "Typed columns, standardised values and a MERGE on the business key. When a request is updated at source, the existing row is updated, so there is still one row per request."),
        ("Control tables sit beside the data", "The <code>meta</code> schema holds source settings, watermarks, the run log and data-quality results, all queryable with SQL."),
    ], [("3.09M", "Bronze rows: full history of every load"), ("3.01M", "Silver rows: one per service request")],
    shot("05_lakehouse.png") + cap("<b>Lakehouse explorer.</b> Bronze, Silver and control schemas, with a preview of the typed Silver table.")))

dq_rows = [
    ("SR01", "Request id is present and numeric", "Quarantine", 0),
    ("SR02", "Created date is present, not in the future", "Quarantine", 0),
    ("SR03", "One row per request id", "Keep latest", 0),
    ("SR04", "Closed date is not before created date", "Clear and flag", 935),
    ("SR05", "Closed date is not in the future", "Clear and flag", 1),
    ("SR06", "ZIP code is five digits", "Clear and flag", 1),
    ("SR07", "Coordinates fall inside New York City", "Clear and flag", 0),
    ("SR08", "Borough is one of the five boroughs", "Set to Unknown, flag", 3286),
]
dq_table = ('<div class="panel" style="padding:20px 10px 8px"><table class="dq"><tr><th>Rule</th><th>Check</th>'
            '<th>When it fails</th><th class="n">Rows checked</th><th class="n">Rows failed</th><th></th></tr>')
for rule, desc, action, failed in dq_rows:
    pill = '<span class="pill fix">repaired</span>' if failed else '<span class="pill ok">clean</span>'
    dq_table += (f'<tr><td class="id">{rule}</td><td>{desc}</td><td>{action}</td><td class="n">3,014,623</td>'
                 f'<td class="n">{failed:,}</td><td>{pill}</td></tr>')
dq_table += "</table></div>"

slides[6] = page(6, TOTAL, "Data quality · Bronze to Silver", "Every bad row is counted and kept",
    "Real public data is messy. The backfill contained requests closed before they were opened, and thousands with no borough. Each problem is handled by a named rule.",
    two_col([
        ("Rules run on every load", "Ten rules check keys, dates, locations and duplicates each time data moves from Bronze to Silver."),
        ("Rejected rows go to quarantine", "Rows that cannot be trusted go to a quarantine table with the reason. Rows with one bad field are repaired and flagged, so analysts can include or exclude them."),
        ("Rule results are stored", "Every rule writes how many rows it checked and how many failed to <code>meta.dq_results</code>, so quality can be trended and alerted on like any other metric."),
    ], [("4,223", "rows repaired and flagged in the backfill"), ("0", "rows lost between layers")],
    dq_table + cap("<b>Results of the backfill run</b>, read from <code>meta.dq_results</code>. Two more rules cover the weather feed.", "margin-top:-6px")
    + shot("06_notebook_silver.png") + cap("<b>Silver notebook.</b> The rules are documented where they are implemented.")))

slides[7] = page(7, TOTAL, "Modelling · Warehouse (T-SQL)", "A star schema the business can query",
    "Gold is a dimensional model in the Fabric Warehouse: two fact tables sharing date and borough dimensions, loaded by stored procedures.",
    two_col([
        ("Built for reporting", "Dimensions use surrogate keys, and each has an Unknown member so no fact row is dropped. The 197 raw complaint types roll up into nine reporting categories."),
        ("Incremental and transactional", "Only changed rows are replaced, in one transaction with the watermark. The daily run updated 36,203 requests and added 197 new ones in 3 seconds."),
        ("Reconciled after every load", "Five reconciliation checks compare Silver with Gold after every load. If they disagree, the run fails and reports are not refreshed on bad data."),
    ], [("3,014,820", "Silver rows = Gold rows, checked every run"), ("5 of 5", "reconciliation checks passed")],
    shot("07_warehouse_query.png") + cap("<b>One query on Gold answers a business question.</b> Heating complaints: 79,928 in January at -2.2 °C, 3,682 in August at 24.3 °C. Noise complaints move the other way.")))

slides[8] = page(8, TOTAL, "Serving · Semantic model and lineage", "Ready for Power BI, traceable end to end",
    "A semantic model sits on top of Gold for Power BI, and Fabric shows the full path from each report back to the source.",
    two_col([
        ("Direct Lake semantic model", "Power BI reads the Gold Delta tables directly, so there is no scheduled import and no second copy of the data. Reports show the latest load as soon as the pipeline finishes."),
        ("Measures defined once", "Total requests, closure rate, average resolution time and weather measures live in the model, so every report uses the same definitions."),
        ("Lineage is visible in Fabric", "Fabric draws the chain from lakehouse to notebooks, pipeline, warehouse and semantic model, which makes impact analysis quick."),
    ], [("7", "tables and 8 measures in the model"), ("0", "data copies between Gold and Power BI")],
    '<div style="display:flex;justify-content:center">' + shot("08_lineage.png", "width:900px") + "</div>"
    + cap("<b>Workspace lineage view.</b> Lakehouse, notebooks, pipeline, warehouse and semantic model.", "text-align:center")))

standards = [
    ("Incremental loads", "High-watermark with look-back. The daily run moved 36,400 changed rows out of 3 million."),
    ("Safe to re-run", "MERGE upserts and transactional loads. Running a load twice gives the same result."),
    ("Data-quality rules", "Ten named rules, results logged on every run, bad rows quarantined."),
    ("Reconciliation gates", "API vs Bronze and Silver vs Gold are compared. A mismatch fails the run."),
    ("Full audit trail", "Every step records rows in, rows out, duration and status."),
    ("Failure handling", "Retries on transient errors, a failure branch, and a hook for alerts."),
    ("Settings held as data", "Endpoints, page sizes and look-back windows live in a control table."),
    ("Everything as code", "Notebooks, SQL, pipeline and model are files, deployed by script."),
]
summary = '<div class="grid4">' + "".join(
    f'<div class="panel std"><div class="tick">✓</div><h3>{h}</h3><p>{p}</p></div>' for h, p in standards) + "</div>"
summary += '<div class="band">' + "".join(
    f'<div class="statbox"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in [
        ("2", "REST API sources"), ("3.01M", "service requests loaded"), ("6 min 46 s", "daily end-to-end run"),
        ("10", "data-quality rules"), ("100%", "of rows reconciled across layers")]) + "</div>"
summary += ('<div class="stack"><span class="lbl">Stack</span><span>Microsoft Fabric</span><span>OneLake · Delta</span>'
            '<span>PySpark</span><span>T-SQL</span><span>Data Pipelines</span><span>Direct Lake · Power BI</span><span>REST APIs</span></div>')
slides[9] = page(9, TOTAL, "Summary", "What you get with this build",
    "The same engineering standards apply whether the source is a public API, an ERP, a CRM or a folder of spreadsheets.", summary)

for n, html in slides.items():
    (here / f"slide_{n:02d}.html").write_text(html, encoding="utf-8")
print("slides:", sorted(slides))
