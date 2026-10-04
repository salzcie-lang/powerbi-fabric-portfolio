"""Small Fabric REST helper for this project (deploy item definitions, run jobs).

Auth: bearer token in the FABRIC_TOKEN environment variable (see env.sh). Nothing is persisted.

  python fabric_api.py deploy <ItemType> <displayName> <folder>     create or update an item definition
  python fabric_api.py run <ItemType> <displayName> <jobType> [json-execution-data]
  python fabric_api.py items
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.fabric.microsoft.com/v1"
WS = os.environ["WS_ID"]
TOKEN = os.environ["FABRIC_TOKEN"]


def call(method, url, body=None):
    if not url.startswith("http"):
        url = f"{API}/{url}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
            return resp.status, dict(resp.headers), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        raise SystemExit(f"HTTP {e.code} {method} {url}\n{raw}")


def wait_lro(status, headers, body, poll=1.0):
    if status != 202:
        return body
    loc = headers.get("Location")
    while True:
        time.sleep(poll)
        _, _, op = call("GET", loc)
        state = (op or {}).get("status")
        if state in ("Succeeded", "Completed"):
            return op
        if state in ("Failed", "Cancelled"):
            raise SystemExit(f"Operation {state}: {json.dumps(op)[:1500]}")


def find_item(item_type, name):
    _, _, body = call("GET", f"workspaces/{WS}/items?type={item_type}")
    for it in body.get("value", []):
        if it["displayName"] == name:
            return it["id"]
    return None


def deploy(item_type, name, folder):
    parts = []
    for f in sorted(Path(folder).rglob("*")):
        if f.is_file():
            parts.append({"path": f.relative_to(folder).as_posix(),
                          "payload": base64.b64encode(f.read_bytes()).decode(), "payloadType": "InlineBase64"})
    definition = {"parts": parts}
    if item_type == "Notebook":
        definition["format"] = "ipynb"
    item_id = find_item(item_type, name)
    if item_id:
        wait_lro(*call("POST", f"workspaces/{WS}/items/{item_id}/updateDefinition", {"definition": definition}))
        print(f"updated {name}.{item_type} ({item_id})")
    else:
        wait_lro(*call("POST", f"workspaces/{WS}/items",
                       {"displayName": name, "type": item_type, "definition": definition}))
        print(f"created {name}.{item_type} ({find_item(item_type, name)})")


def run(item_type, name, job_type, execution_data=None):
    item_id = find_item(item_type, name)
    body = {"executionData": json.loads(execution_data)} if execution_data else None
    status, headers, _ = call("POST", f"workspaces/{WS}/items/{item_id}/jobs/instances?jobType={job_type}", body)
    loc = headers.get("Location")
    print(f"started {name}: {loc.rsplit('/', 1)[-1]}", flush=True)
    start = time.time()
    while True:
        time.sleep(15)
        _, _, inst = call("GET", loc)
        state = inst.get("status")
        if state in ("Completed", "Failed", "Cancelled", "Deduped"):
            print(f"{name}: {state} after {time.time() - start:.0f}s")
            if state != "Completed":
                print(json.dumps(inst.get("failureReason"), indent=2))
                sys.exit(1)
            if item_type == "Notebook":
                _, _, det = call("GET", f"workspaces/{WS}/notebooks/{item_id}/jobs/execute/instances/{inst['id']}?beta=true")
                print("exitValue:", (det.get("properties") or {}).get("exitValue"))
            return


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "deploy":
        deploy(*sys.argv[2:5])
    elif cmd == "run":
        run(*sys.argv[2:6])
    elif cmd == "items":
        _, _, body = call("GET", f"workspaces/{WS}/items")
        for it in body["value"]:
            print(f"{it['type']:<16} {it['displayName']:<40} {it['id']}")
