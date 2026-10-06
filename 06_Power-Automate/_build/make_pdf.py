"""Render diagram pages to exports/ and assemble the case-study PDF plus a contact sheet. Run from 06_Power-Automate."""
import json, subprocess, sys
from PIL import Image
Image.init()
from pathlib import Path
B = Path("_build"); stats = B / "stats.json"
def render(page, out, w, h):
    subprocess.run([sys.executable, str(B / "render.py"), page, out, str(w), str(h), "2"], check=True)
subprocess.run([sys.executable, "diagram/build_slides.py"], check=True)
render("architecture.html", "exports/02 Architecture.png", 1920, 1080)
stats.write_text(json.dumps({"COVER_CLASS": "wide"})); render("cover.html", "exports/01 Cover.png", 1920, 1080)
stats.write_text(json.dumps({"COVER_CLASS": ""})); render("cover.html", "exports/00 Upwork Thumbnail.png", 1600, 1200)
stats.unlink()
names = {3: "03 File Intake Router", 4: "04 Routing Evidence", 5: "05 Landing Zone Alert", 6: "06 Pipeline Notification", 7: "07 Email Attachment Capture", 8: "08 Summary"}
for n, name in names.items():
    render(f"slide_{n:02d}.html", f"exports/{name}.png", 1920, 1080)
fs = sorted(Path("exports").glob("0[1-9]*.png"))
ims = [Image.open(f).convert("RGB") for f in fs]
ims[0].save("exports/Power Automate - File Intake Automation.pdf", save_all=True, append_images=ims[1:], resolution=200, quality=92)
tiles = [Image.open("exports/00 Upwork Thumbnail.png").convert("RGB").resize((720, 540))] + [im.resize((960, 540)) for im in ims]
sheet = Image.new("RGB", (1920, 540 * ((len(tiles) + 1) // 2)), "black")
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % 2) * 960, (i // 2) * 540))
sheet.save("exports/_sheet.png"); print(len(fs), "pages")
