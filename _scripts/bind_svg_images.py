"""Points image visuals at SVG measures: bind_svg_images.py <Report folder> <page folder> name=Measure ...

pbir 0.9.31 cannot write a measure into image.sourceField (it only accepts a string there), so this
writes the documented shape directly: sourceType 'imageData' plus a Measure expression.
"""
import json
import sys
from pathlib import Path

report, page, pairs = Path(sys.argv[1]), sys.argv[2], dict(a.split("=", 1) for a in sys.argv[3:])
lit = lambda v: {"expr": {"Literal": {"Value": v}}}
for name, measure in pairs.items():
    f = report / "definition" / "pages" / page / "visuals" / name / "visual.json"
    j = json.loads(f.read_text(encoding="utf-8"))
    j["visual"]["objects"] = {"image": [{"properties": {
        "sourceType": lit("'imageData'"),
        "sourceField": {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": measure}}},
        "transparency": lit("0D"), "effects": lit("false"),
    }}]}
    j["visual"].pop("query", None)
    f.write_text(json.dumps(j, indent=2) + "\n", encoding="utf-8")
print(f"bound {len(pairs)} image visuals on {page}")
