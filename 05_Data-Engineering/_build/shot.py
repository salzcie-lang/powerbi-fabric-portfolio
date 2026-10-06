"""Drive the dedicated Chrome window (remote debugging on :9333) to capture Fabric portal screenshots.

  python shot.py info                               current tab url + title
  python shot.py goto <url> [wait_seconds]          navigate
  python shot.py shot <out.png> [width height]      screenshot (device scale 2)
  python shot.py js "<expression>"                  evaluate JS, print result
  python shot.py click <x> <y>                      mouse click at CSS pixel
  python shot.py key <Key>                          press a key (e.g. Escape)
"""
import base64
import os
import json
import sys
import time
import urllib.request
from pathlib import Path

import websocket

PORT = 9333
tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
tab = next(t for t in tabs if t["type"] == "page" and "fabric.microsoft.com" in t["url"] or t["type"] == "page")
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], suppress_origin=True, timeout=120)
_id = 0


def cdp(method, **params):
    global _id
    _id += 1
    ws.send(json.dumps({"id": _id, "method": method, "params": params}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id:
            if "error" in msg:
                raise SystemExit(f"{method}: {msg['error']}")
            return msg.get("result", {})


def js(expr):
    r = cdp("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
    return r.get("result", {}).get("value")


cmd = sys.argv[1]
if cmd in ("click", "type", "ctrlenter", "ctrla", "key", "goto", "wheel"):
    # the override is dropped when a debugger session closes, so re-apply it for every action
    cdp("Emulation.setDeviceMetricsOverride", width=1800, height=1000, deviceScaleFactor=2, mobile=False)
    time.sleep(1.0)
if cmd == "info":
    print(js("location.href"), "|", js("document.title"))
elif cmd == "goto":
    cdp("Page.navigate", url=sys.argv[2])
    time.sleep(float(sys.argv[3]) if len(sys.argv) > 3 else 8)
    print(js("location.href"), "|", js("document.title"))
elif cmd == "shot":
    w, h = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1600, 900)
    cdp("Page.bringToFront")
    cdp("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=2, mobile=False)
    time.sleep(1.5)
    if os.environ.get("PRE_JS"):  # e.g. strip text from the page right before capture
        js(os.environ["PRE_JS"]); time.sleep(0.4)
    data = cdp("Page.captureScreenshot", format="png")["data"]
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(data))
    from PIL import Image
    im = Image.open(out); im.resize((1100, int(1100 * im.height / im.width))).save(out.with_name("_prev_" + out.name))
    print(f"saved {out} ({w}x{h} @2x)")
elif cmd == "js":
    print(js(sys.argv[2]))
elif cmd == "click":
    x, y = float(sys.argv[2]), float(sys.argv[3])
    cdp("Page.bringToFront")
    cdp("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
    time.sleep(0.3)
    for t in ("mousePressed", "mouseReleased"):
        cdp("Input.dispatchMouseEvent", type=t, x=x, y=y, button="left", clickCount=1)
    time.sleep(1.5)
elif cmd == "type":
    cdp("Input.insertText", text=sys.argv[2])
elif cmd == "wheel":
    cdp("Input.dispatchMouseEvent", type="mouseWheel", x=float(sys.argv[2]), y=float(sys.argv[3]), deltaX=0, deltaY=float(sys.argv[4]))
    time.sleep(1.5)
elif cmd == "ctrla":
    for t in ("rawKeyDown", "keyUp"):
        cdp("Input.dispatchKeyEvent", type=t, key="a", code="KeyA", windowsVirtualKeyCode=65, modifiers=2)
elif cmd == "ctrlenter":
    for t in ("rawKeyDown", "keyUp"):
        cdp("Input.dispatchKeyEvent", type=t, key="Enter", code="Enter", windowsVirtualKeyCode=13, modifiers=2)
elif cmd == "key":
    for t in ("keyDown", "keyUp"):
        cdp("Input.dispatchKeyEvent", type=t, key=sys.argv[2])
ws.close()
