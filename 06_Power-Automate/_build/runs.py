"""Show recent runs and action results for the demo flows. Usage: python _build/runs.py <since-iso-utc> [min02runs]"""
import json, subprocess, sys, time, urllib.request
from pathlib import Path
cfg = json.loads((Path(__file__).parent / "env.local.json").read_text())
B = f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/{cfg['env']}/flows"
T = subprocess.run("az account get-access-token --resource https://service.flow.microsoft.com/ --query accessToken -o tsv",
                   shell=True, capture_output=True, text=True).stdout.strip()
def get(u, auth=True):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Authorization": "Bearer " + T} if auth else {})))
since = sys.argv[1]; want = int(sys.argv[2]) if len(sys.argv) > 2 else 0
flows = {f["properties"]["displayName"]: f["name"] for f in get(B + "?api-version=2016-11-01")["value"]
         if f["properties"]["displayName"].startswith("Portfolio demo - 0")}
def runs(fid):
    return [r for r in get(f"{B}/{fid}/runs?api-version=2016-11-01")["value"] if r["properties"]["startTime"] >= since]
for _ in range(28):  # up to 14 minutes
    r02 = runs(next(v for k, v in flows.items() if "02" in k))
    if len(r02) >= want and all(r["properties"]["status"] != "Running" for r in r02): break
    time.sleep(30)
for name, fid in sorted(flows.items()):
    rs = runs(fid); print(f"\n{name}: {len(rs)} runs")
    for r in rs:
        acts = get(f"{B}/{fid}/runs/{r['name']}/actions?api-version=2016-11-01")["value"]
        line = ", ".join(f"{a['name']}={a['properties']['status']}" for a in acts)
        errs = [f"{a['name']}: {json.dumps(a['properties'].get('error'))[:300]}" for a in acts if a["properties"]["status"] == "Failed"]
        print(" ", r["properties"]["status"], r["properties"]["startTime"][11:19], "|", line, *errs, sep=" ")
