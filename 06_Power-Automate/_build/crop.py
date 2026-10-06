"""Crop the raw portal captures (screenshots/raw_*.png, 3600x2000 @2x) into the published screenshots.
The portal header carries the tenant name, so every crop starts below it (y >= 100)."""
from PIL import Image
from pathlib import Path
S = Path(__file__).resolve().parent.parent / "screenshots"
def crop(src, box, dst):
    Image.open(S / f"raw_{src}.png").crop(box).save(S / f"{dst}.png"); print(dst)
CANVAS = (1000, 240, 2600, 1990)  # the node column of the designer / run view, below the breadcrumb bar
for tag, name in [("01", "01_router"), ("02", "02_alert"), ("03", "03_outbox"), ("04", "04_capture")]:
    crop(f"{tag}_editor", CANVAS, f"{name}_editor")
    crop(f"{tag}_run", CANVAS, f"{name}_run")
crop("01_run_detail", (0, 240, 1270, 1990), "01_router_run_detail")   # the step's inputs/outputs panel
crop("01_details", (560, 1080, 2500, 2000), "01_router_run_history")
crop("landing_folder", (560, 110, 3600, 1120), "landing_folder")
