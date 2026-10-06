"""Create a flow from flows/*.flow.json. Usage: python _build/deploy.py <flow.json> "<display name>"

Reads _build/env.local.json (git-ignored; see env.example.json) for the environment id,
placeholder values and connection names. Needs `az login` in the target tenant.
"""
import json, subprocess, sys, urllib.request
from pathlib import Path

cfg = json.loads((Path(__file__).parent / "env.local.json").read_text())
text = Path(sys.argv[1]).read_text(encoding="utf-8")
for old, new in cfg["replace"].items():
    text = text.replace(old, new)
definition = json.loads(text)
refs = {c: {"connectionName": cfg["connections"][c], "source": "Embedded",
            "id": f"/providers/Microsoft.PowerApps/apis/{c}"}
        for c in cfg["connections"] if f'"{c}"' in text}
missing = [c for c, r in refs.items() if not r["connectionName"]]
if missing:
    sys.exit(f"no connection configured for {missing}")
token = subprocess.run("az account get-access-token --resource https://service.flow.microsoft.com/ "
                       "--query accessToken -o tsv", shell=True, capture_output=True, text=True).stdout.strip()
body = {"properties": {"displayName": sys.argv[2], "definition": definition,
                       "connectionReferences": refs, "state": "Started"}}
req = urllib.request.Request(
    f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/{cfg['env']}/flows?api-version=2016-11-01",
    data=json.dumps(body).encode(), method="POST",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
try:
    r = json.load(urllib.request.urlopen(req))
    print(r["name"], r["properties"]["state"])
except urllib.error.HTTPError as e:
    sys.exit(f"{e.code} {e.read().decode()[:1500]}")
