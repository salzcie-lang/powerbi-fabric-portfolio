"""Adds a Deneb (Vega-Lite) visual to a page.

add_deneb.py <Report folder> <page folder> <name> <spec.json> <config.json> <x> <y> <w> <h> <Table.Column ...> -- <Table.Measure ...>

pbir 0.9.31 cannot create custom-visual containers or register them in report.json, so this writes the
documented shape: the visual shell with its `dataset` projections and the spec, and the Deneb id under
publicCustomVisuals. Formatting, filters and interactions are still applied with pbir afterwards.
"""
import json
import sys
from pathlib import Path

DENEB = "deneb7E15AEF80B9E4D4F8E12924291ECE89A"
report, page, name, spec, config = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4]), Path(sys.argv[5])
x, y, w, h = map(int, sys.argv[6:10])
fields, kind, projections = sys.argv[10:], "Column", []
for f in fields:
    if f == "--":
        kind = "Measure"
        continue
    table, prop = f.split(".", 1)
    projections.append({"field": {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": prop}},
                        "queryRef": f, "nativeQueryRef": prop})

lit = lambda v: {"expr": {"Literal": {"Value": v}}}
text = lambda s: lit("'" + s.replace("'", "''") + "'")
visuals = report / "definition" / "pages" / page / "visuals"
schema = json.loads(next(visuals.glob("*/visual.json")).read_text(encoding="utf-8"))["$schema"]
hide = [{"properties": {"show": lit("false")}}]
visual = {
    "$schema": schema, "name": name,
    "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
    "visual": {
        "visualType": DENEB,
        "query": {"queryState": {"dataset": {"projections": projections}}},
        "objects": {
            # Deneb sizes the chart from this stored viewport; without it the view renders at a stale, smaller size
            "stateManagement": [{"properties": {"viewportHeight": lit(f"{h - 10}D"), "viewportWidth": lit(f"{w - 10}D")}}],
            "vega": [{"properties": {
            "provider": text("vegaLite"), "jsonSpec": text(spec.read_text(encoding="utf-8")),
            "jsonConfig": text(config.read_text(encoding="utf-8")), "isNewDialogOpen": lit("false"),
            "enableTooltips": lit("true"), "enableContextMenu": lit("true"), "enableHighlight": lit("false"),
            "enableSelection": lit("true"), "selectionMaxDataPoints": lit("50D"),
        }}]},
        "visualContainerObjects": {"title": hide, "background": hide, "border": hide, "visualHeader": hide},
        "drillFilterOtherVisuals": True,
    },
}
target = visuals / name / "visual.json"
if target.exists():  # re-run after a spec change: keep the filters pbir added
    previous = json.loads(target.read_text(encoding="utf-8"))
    if "filterConfig" in previous:
        visual["filterConfig"] = previous["filterConfig"]
(visuals / name).mkdir(exist_ok=True)
(visuals / name / "visual.json").write_text(json.dumps(visual, indent=2) + "\n", encoding="utf-8")

rj = report / "definition" / "report.json"
j = json.loads(rj.read_text(encoding="utf-8"))
if DENEB not in j.setdefault("publicCustomVisuals", []):
    j["publicCustomVisuals"].append(DENEB)
    rj.write_text(json.dumps(j, indent=2) + "\n", encoding="utf-8")
print(f"added Deneb visual {name} on {page} ({len(projections)} fields)")
