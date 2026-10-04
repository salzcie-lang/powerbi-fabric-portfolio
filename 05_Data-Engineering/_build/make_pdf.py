"""Assemble exports/*.png (01..09) into one PDF and a contact sheet for review."""
import glob
from PIL import Image
Image.init()
fs = sorted(glob.glob("exports/0[1-9]*.png"))
ims = [Image.open(f).convert("RGB") for f in fs]
ims[0].save("exports/Data Engineering - Fabric Data Platform.pdf", save_all=True, append_images=ims[1:], resolution=200, quality=92)
tiles = [Image.open("exports/00 Upwork Thumbnail.png").convert("RGB").resize((720, 540))] + [im.resize((960, 540)) for im in ims]
sheet = Image.new("RGB", (1920, 540 * 5), "black")
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % 2) * 960, (i // 2) * 540))
sheet.save("exports/_sheet.png")
print(len(fs), "pages")
