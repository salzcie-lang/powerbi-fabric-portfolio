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
.statbox { flex: 1; padding: 14px 18px; border-radius: 14px; background: rgba(31, 94, 255, 0.07); border: 1px solid rgba(31, 94, 255, 0.28); }
.statbox .v { font-size: 30px; font-weight: 800; letter-spacing: -0.01em; }
.statbox .l { font-size: 13px; color: var(--ink-2); margin-top: 3px; line-height: 1.35; }
.shots { display: flex; flex-direction: column; gap: 18px; min-height: 0; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }
.pair { display: flex; gap: 22px; align-items: flex-start; min-height: 0; }
.pair .tall { flex: none; height: 760px; }
.pair .tall img { height: 100%; width: auto; }
.pair .rest { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 18px; }
pre.code { font-family: 'JetBrains Mono', Consolas, monospace; font-size: 13.5px; line-height: 1.5; color: var(--ink); background: var(--panel-2); border: 1px solid var(--line); border-radius: 12px; padding: 14px 18px; white-space: pre-wrap; }
pre.code .k { color: var(--accent); } pre.code .s { color: var(--teal); }
table.mini { width: 100%; border-collapse: collapse; font-size: 14px; }
table.mini th { text-align: left; font-size: 11.5px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); padding: 0 12px 7px; font-weight: 700; }
table.mini td { padding: 8px 12px; border-top: 1px solid var(--line); color: var(--ink-2); vertical-align: top; }
table.mini td.n { color: var(--ink); font-weight: 600; white-space: nowrap; }
table.runs { width: 100%; border-collapse: collapse; font-size: 15px; margin-top: 22px; }
table.runs th { text-align: left; font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); padding: 0 14px 9px; font-weight: 700; }
table.runs td { padding: 9px 14px; border-top: 1px solid var(--line); color: var(--ink-2); }
table.runs td.n { color: var(--ink); font-weight: 600; }
.frame { border-radius: 14px; overflow: hidden; border: 1px solid rgba(15,23,42,0.14); box-shadow: 0 18px 44px rgba(15,23,42,0.14); background: #fff; position: relative; }
.frame img { display: block; width: 100%; }
.cap { font-size: 13.5px; color: var(--ink-3); margin-top: -8px; }
.cap b { color: var(--ink-2); font-weight: 600; }
table.dq { width: 100%; border-collapse: collapse; font-size: 15px; }
table.dq th { text-align: left; font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); padding: 0 14px 9px; font-weight: 700; }
table.dq td { padding: 8px 14px; border-top: 1px solid var(--line); color: var(--ink-2); }
table.dq td.id { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--teal); }
table.dq td.n { color: var(--ink); font-weight: 600; }
.pill { font-size: 12px; font-weight: 700; border-radius: 999px; padding: 3px 10px; white-space: nowrap; }
.pill.ok { background: rgba(15,157,138,0.12); color: var(--teal); }
.pill.fix { background: rgba(217,140,0,0.14); color: var(--amber); }
.pill.q { background: rgba(217,71,95,0.12); color: var(--red); }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-top: 30px; }
.std { padding: 20px 22px; }
.std .tick { width: 30px; height: 30px; border-radius: 9px; background: rgba(15,157,138,0.12); color: var(--teal); display: grid; place-items: center; font-weight: 800; font-size: 17px; }
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
<div class="pageno">FILE INTAKE AUTOMATION &nbsp;·&nbsp; {n:02d} / {total:02d}</div></div>
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


TOTAL = 8
slides = {}

slides[3] = page(3, TOTAL, "Flow 01 · File intake router", "Files route themselves, and mistakes are visible",
    "An analyst drops files into one OneDrive folder. Each file is copied to the landing folder its name says it belongs in, so the dataflows that read those folders never need a person in between.",
    two_col([
        ("Noise is rejected before a run starts", "Trigger conditions drop Office lock files, folders and unsupported extensions. A stray <code>.txt</code> file consumed no run at all."),
        ("Rule order and case are deliberate", "Contract logs are named <i>Quote Log Customer Contracts</i>, so the contract rule is tested before the quote rule. Inventory names are case-exact because the dataflow that reads them is."),
        ("Unknown names are quarantined, not lost", "A file that matches no rule goes to <code>_Inbox Unrouted</code> and triggers a high-importance alert, instead of landing where nothing reads it."),
    ], [("18 of 18", "live runs succeeded, including overwrites"), ("16 / 16", "routing test cases pass")],
    '<div class="pair">' + shot("01_router_editor.png", "flex:none;height:760px") .replace('class="frame"', 'class="frame tall"')
    + shot("01_router_run_detail.png", "flex:none;height:760px").replace('class="frame"', 'class="frame tall"') + '</div>'
    + cap("<b>Left: flow canvas.</b> Trigger conditions, a routing expression, and a copy guarded by a condition. &nbsp; <b>Right: a real run.</b> The routing step's output for a wrongly cased inventory file is the quarantine folder.")))

rules = [
    ("1", "customer contract log", "any", "Contracts", "ok"),
    ("2", "quote log", "any", "Quotes", "ok"),
    ("3", "design registration…", "any", "Design Registrations", "ok"),
    ("4", "price list", "any", "Price List", "ok"),
    ("5", "Distributor Backlog · Month-End Inventory", "exact", "Inventory", "fix"),
    ("6", "ytd sales detail", "any", "skip (manual monthly upload)", "fix"),
    ("7", "anything else", "", "_Inbox Unrouted + alert", "q"),
]
rule_table = ('<div class="panel" style="padding:20px 10px 8px"><table class="dq"><tr><th>#</th><th>Name contains</th>'
              '<th>Case</th><th>Destination</th><th></th></tr>')
for n, pat, case, dest, kind in rules:
    pill = {"ok": "copy", "fix": "special", "q": "quarantine"}[kind]
    rule_table += f'<tr><td class="id">{n}</td><td class="n">{pat}</td><td>{case}</td><td>{dest}</td><td><span class="pill {kind}">{pill}</span></td></tr>'
rule_table += "</table></div>"

slides[4] = page(4, TOTAL, "Flow 01 · Evidence", "Tested with real files, checked by hand",
    "Seven files with production-style names were dropped three times. Every run is in the flow's history, and every file is where the rules say it should be.",
    two_col([
        ("Routing rules in one place", "Seven ordered rules in a single expression, mirrored by a Python test so a rule change is checked before deployment."),
        ("Same-name uploads overwrite", "Daily files keep their name. The destination is replaced and SharePoint keeps the previous copy as a version."),
        ("Every run is accounted for", "Six files, six runs per drop; the filtered file produced none. All eighteen runs succeeded in under a second each."),
    ], [("7", "routing rules"), ("< 1 s", "typical run")],
    rule_table + cap("<b>Routing contract.</b> Order matters: rule 1 is tested before rule 2 because contract-log names contain “quote log”.", "margin-top:-6px")
    + '<div class="row">' + shot("01_router_run_history.png") + shot("landing_folder.png") + "</div>"
    + cap("<b>Left:</b> run history, all succeeded. <b>Right:</b> the landing zone after the test, one folder per file family plus quarantine and outbox.")))

slides[5] = page(5, TOTAL, "Flow 02 · Landing zone alert", "The team learns what arrived and what to run",
    "Every file that reaches the landing zone produces one email: what it is, who put it there, which version, and the refresh it needs. Refreshes are deliberately not triggered automatically.",
    two_col([
        ("One flow, two tones", "Normal uploads arrive as ordinary mail. Quarantined files arrive marked UNROUTED at high importance, so they are noticed."),
        ("The next step is in the email", "A small expression maps the file family to the dataflow or pipeline that reads it, so whoever is on duty does not have to look it up."),
        ("Why not refresh automatically", "Source file layouts change without warning. A person looks at the file first; the alert makes that quick."),
    ], [("7 of 7", "runs, one email each"), ("5 min", "polling interval")],
    '<div class="pair">' + shot("02_alert_run.png").replace('class="frame"', 'class="frame tall"')
    + '<div class="rest">' + shot("email_alert.png") + cap("<b>The email.</b> File, folder, editor, time, version, a link, and the refresh step to run.")
    + '<div class="panel" style="padding:16px 8px 6px"><table class="mini"><tr><th>File family</th><th>Next step in the email</th></tr>'
      '<tr><td class="n">Quote log, contract log, price list, registrations</td><td>Run the quotes ingestion pipeline, then refresh the Quotes and Sales models</td></tr>'
      '<tr><td class="n">Distributor backlog, month-end inventory</td><td>Run the inventory dataflow, then refresh the Sales model</td></tr>'
      '<tr><td class="n">YTD sales detail</td><td>Run the sales dataflow, then refresh the Sales model</td></tr>'
      '<tr><td class="n">Quarantined</td><td>Check the name (inventory names are case-sensitive), rename, drop again</td></tr>'
      '<tr><td class="n">Anything else</td><td>No mapping: check which dataflow reads it</td></tr></table></div>'
    + cap("<b>Refresh map.</b> One expression in the flow; the email carries the answer.") + '</div></div>'
    + cap("<b>Run view.</b> Trigger, two expressions, one email, all green.")))

slides[6] = page(6, TOTAL, "Flow 03 · Pipeline notification outbox", "A data pipeline sends email without owning a mailbox",
    "A Fabric pipeline renders a digest and writes it as a JSON file. The flow sends it and moves the file, so the pipeline can see what happened without an HTTP endpoint or a Premium licence.",
    two_col([
        ("No credentials in the data platform", "The flow owns the mail connection. The pipeline only writes a file: <code>runId</code>, <code>subject</code>, <code>recipients</code>, <code>htmlBody</code>."),
        ("The folder is the status", "<code>Sent</code> means delivered, <code>Rejected</code> means the payload was incomplete, and a file still in <code>Pending</code> means the send failed and the run can be resubmitted."),
        ("One receiving flow instead of twelve", "In the original engagement this replaced a per-region set of polling flows with one flow that does nothing but send what it is given."),
    ], [("2 of 2", "paths tested: Sent and Rejected"), ("0", "Premium connectors")],
    '<div class="pair">' + shot("03_outbox_run.png").replace('class="frame"', 'class="frame tall"')
    + '<div class="rest">' + shot("email_digest.png") + cap("<b>The digest.</b> Rendered by the pipeline, delivered by the flow.")
    + '''<pre class="code">{
  <span class="k">"runId"</span>: <span class="s">"20261006T030014Z-9ff268b8"</span>,
  <span class="k">"subject"</span>: <span class="s">"Agent tier updates - 06-10-2026 (2 changes)"</span>,
  <span class="k">"recipients"</span>: [<span class="s">"reporting@example.com"</span>, <span class="s">"ops@example.com"</span>],
  <span class="k">"htmlBody"</span>: <span class="s">"&lt;p&gt;Two agents changed tier in today's run.&lt;/p&gt;…"</span>
}</pre>'''
    + cap("<b>The contract.</b> One JSON file per run in <code>Pending</code>. Missing fields send it to <code>Rejected</code>; a failed send leaves it in <code>Pending</code> for a resubmit.") + '</div></div>'
    + cap("<b>Run view.</b> A valid digest: read, validated, sent, moved to Sent. The Rejected branch was skipped.")))

slides[7] = page(7, TOTAL, "Flow 04 · Email attachment capture", "Systems that can only email still feed the platform",
    "A building-management system sends its daily trend export as an attachment. The flow saves it to the landing zone, where the same alert and dataflows pick it up.",
    two_col([
        ("Filtered at the trigger", "A subject filter and an attachment requirement sit on the trigger itself, so the rest of the mailbox never starts a run."),
        ("Only data attachments are saved", "Inline images and signatures are filtered out; only <code>.csv</code> and <code>.xlsx</code> attachments reach the folder."),
        ("Large files are handled", "The copy uses chunked transfer, so multi-megabyte exports do not fail on size."),
    ], [("1 of 2", "attachments saved: the CSV, not the image"), ("< 2 s", "from email to folder")],
    '<div class="pair">' + shot("04_capture_run.png").replace('class="frame"', 'class="frame tall"')
    + '<div class="rest">' + shot("landing_folder.png") + cap("<b>The landing zone.</b> Trend Exports sits beside the folders fed by the drop-folder flow, so the same alert and dataflows apply.")
    + '<div class="panel" style="padding:16px 8px 6px"><table class="mini"><tr><th>Attachment in the test email</th><th>Filter</th><th>Outcome</th></tr>'
      '<tr><td class="n">Trend Export 2026-10-06.csv</td><td>.csv, not inline</td><td>Saved to Trend Exports; alert email sent by flow 02</td></tr>'
      '<tr><td class="n">logo.png</td><td>not a data file</td><td>Dropped by the filter array; nothing written</td></tr></table></div>'
    + cap("<b>Filter array.</b> <code>not(isInline) and (endsWith .csv or .xlsx)</code>, evaluated once per email.") + '</div></div>'
    + cap("<b>Run view.</b> One loop iteration: the image attachment was filtered out before the loop.")))

standards = [
    ("Filter at the trigger", "Lock files, folders, wrong extensions and unrelated mail never consume a run."),
    ("Rules match the reader", "Case policy and rule order follow the dataflows that read each folder."),
    ("Fail visibly", "Unknown files are quarantined and alerted, never dropped silently."),
    ("Safe to re-run", "Same-name copies overwrite with versioning; a failed send stays Pending."),
    ("No credentials downstream", "Pipelines hand off to a flow instead of holding mail secrets."),
    ("Standard connectors", "OneDrive, SharePoint and Outlook only. No Premium licence needed."),
    ("Tested before go-live", "Routing simulated in code, then exercised live with real file names."),
    ("Definitions as code", "Each flow is a JSON definition, deployed by script with placeholders for your tenant."),
]
summary = '<div class="grid4">' + "".join(
    f'<div class="panel std"><div class="tick">✓</div><h3>{h}</h3><p>{p}</p></div>' for h, p in standards) + "</div>"
summary += ('<table class="runs"><tr><th>Flow</th><th>Trigger</th><th>Live test</th><th>Result</th></tr>'
    '<tr><td class="n">01 File intake router</td><td>OneDrive file created or modified</td><td>7 files dropped three times</td><td>18 runs, every file in the right folder, overwrites clean</td></tr>'
    '<tr><td class="n">02 Landing zone alert</td><td>SharePoint file created or modified</td><td>Every landing-zone arrival</td><td>7 runs, 7 emails, quarantine flagged at high importance</td></tr>'
    '<tr><td class="n">03 Pipeline notification outbox</td><td>JSON file created in Pending</td><td>Valid and invalid digests</td><td>Sent and Rejected paths both exercised</td></tr>'
    '<tr><td class="n">04 Email attachment capture</td><td>Email with subject filter and attachment</td><td>Email with a CSV and an image</td><td>Only the CSV saved, chunked transfer</td></tr></table>')
summary += '<div class="band">' + "".join(
    f'<div class="statbox"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in [
        ("4", "cloud flows"), ("3", "standard connectors"), ("32", "live runs, 0 failed"),
        ("7", "routing rules, 16 test cases"), ("0", "Premium licences required")]) + "</div>"
summary += ('<div class="stack"><span class="lbl">Stack</span><span>Power Automate</span><span>SharePoint</span>'
            '<span>OneDrive for Business</span><span>Office 365 Outlook</span><span>Microsoft Fabric pipelines</span><span>Dataflows · Power BI</span></div>')
slides[8] = page(8, TOTAL, "Summary", "What you get with this build",
    "The same habits apply whether the files come from an analyst, a vendor portal, a building system or a pipeline: filter early, route by rule, fail visibly, hand off cleanly.", summary)

for n, html in slides.items():
    (here / f"slide_{n:02d}.html").write_text(html, encoding="utf-8")
print("slides:", sorted(slides))
