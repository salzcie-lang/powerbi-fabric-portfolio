"""Render an HTML page in diagram/ to PNG with headless Chrome, filling {{PLACEHOLDERS}} from stats.json.

  python render.py <page.html> <out.png> <width> <height> [scale]
"""
import json
import subprocess
import sys
from pathlib import Path

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
root = Path(__file__).resolve().parent.parent
page, out, width, height = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
scale = sys.argv[5] if len(sys.argv) > 5 else "2"

html = (root / "diagram" / page).read_text(encoding="utf-8")
stats_file = root / "_build" / "stats.json"
if stats_file.exists():
    for key, value in json.loads(stats_file.read_text()).items():
        html = html.replace("{{" + key + "}}", str(value))
tmp = root / "diagram" / f"_render_{page}"
tmp.write_text(html, encoding="utf-8")

out_path = (root / out).resolve()
out_path.parent.mkdir(parents=True, exist_ok=True)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={scale}",
                f"--window-size={width},{height}", "--virtual-time-budget=6000",
                f"--screenshot={out_path}", tmp.as_uri()], check=True, capture_output=True)
tmp.unlink()
print(f"rendered {out_path.name}")
