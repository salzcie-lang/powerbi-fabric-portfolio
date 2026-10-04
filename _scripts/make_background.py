"""Designed page backgrounds for the portfolio dashboards (1280x720, rendered at 2x).

Everything static lives here: soft mesh canvas, glass nav rail, layered-shadow cards, KPI icon
chips and labels, slicer pills, (i) markers. Power BI visuals sit on top with transparent
backgrounds, so depth and material come from this image and data comes from the visuals.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2
W, H = 1280, 720
FONTS = Path("C:/Windows/Fonts")


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), int(size * S))


def rgba(hex_color, alpha=255):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def blob(img, box, color, alpha, blur):
    layer = Image.new("RGBA", img.size, rgba(color, 0))
    ImageDraw.Draw(layer).ellipse([v * S for v in box], fill=rgba(color, alpha))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur * S)))


def rounded(img, box, radius, fill, outline=None):
    layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
    ImageDraw.Draw(layer).rounded_rectangle([v * S for v in box], radius * S, fill=fill, outline=outline, width=S)
    img.alpha_composite(layer)


def shadow(img, box, radius, color, alpha, blur, dy):
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", img.size, rgba(color, 0))
    ImageDraw.Draw(layer).rounded_rectangle([x0 * S, (y0 + dy) * S, x1 * S, (y1 + dy) * S], radius * S, fill=rgba(color, alpha))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur * S)))


def surface(img, box, t, radius=18, fill_alpha=244):
    """A card: wide ambient shadow + tight contact shadow + near-white fill + bright hairline edge."""
    wide, tight = t.get("shadow_alpha", (26, 20))
    shadow(img, box, radius, t["shadow"], wide, 26, 14)
    shadow(img, box, radius, t["shadow"], tight, 4, 2)
    rounded(img, box, radius, rgba(t["card"], t.get("card_alpha", fill_alpha)), outline=rgba(*t.get("edge", ("#FFFFFF", 255))))


def gradient_chip(img, box, radius, c1, c2):
    x0, y0, x1, y1 = [int(v * S) for v in box]
    w, h = x1 - x0, y1 - y0
    g = Image.linear_gradient("L").resize((w, h))
    chip = Image.composite(Image.new("RGBA", (w, h), rgba(c1)), Image.new("RGBA", (w, h), rgba(c2)), g)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], int(radius * S), fill=255)
    img.paste(chip, (x0, y0), mask)


def glyph(d, xy, code, size, fill):
    d.text((xy[0] * S, xy[1] * S), chr(code), font=font("segmdl2.ttf", size), fill=fill, anchor="mm")


def tracked(d, xy, text, fnt, fill, tracking=0.6):
    """Draw text with letter-spacing (small caps labels want positive tracking)."""
    x, y = xy[0] * S, xy[1] * S
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + tracking * S


def make(out, t, title, subtitle, nav, active, cards, kpis=(), info=(), pills=()):
    img = Image.new("RGBA", (W * S, H * S), rgba(t["canvas"]))
    for box, color, alpha, blur in t["blobs"]:
        blob(img, box, color, alpha, blur)

    # glass nav rail
    rail = (20, 20, 68, 700)
    shadow(img, rail, 24, t["shadow"], 30, 24, 12)
    rounded(img, rail, 24, rgba(*t.get("rail_fill", ("#FFFFFF", 150))), outline=rgba(*t.get("edge", ("#FFFFFF", 255))))
    shadow(img, (30, 30, 58, 58), 9, t["accent"], 90, 6, 4)
    gradient_chip(img, (30, 30, 58, 58), 9, t["accent"], t["accent2"])
    d = ImageDraw.Draw(img)
    for i, h in enumerate((7, 11, 15)):
        bx = (36 + i * 6) * S
        d.rounded_rectangle([bx, (52 - h) * S, bx + 3 * S, 52 * S], S, fill=rgba(t.get("on_accent", "#FFFFFF")))
    for i, code in enumerate(nav):
        cy = 108 + i * 50
        if i == active:
            shadow(img, (27, cy - 17, 61, cy + 17), 11, t["accent"], 80, 8, 5)
            gradient_chip(img, (27, cy - 17, 61, cy + 17), 11, t["accent"], t["accent2"])
            d = ImageDraw.Draw(img)
            glyph(d, (44, cy), code, 12.5, rgba(t.get("on_accent", "#FFFFFF")))
        else:
            glyph(d, (44, cy), code, 12.5, rgba(t["muted"]))
    glyph(d, (44, 672), 0xE946, 12.5, rgba(t["muted"]))

    # header
    d.text((92 * S, 18 * S), title, font=font("seguisb.ttf", 18), fill=rgba(t["ink"]))
    d.text((92 * S, 46 * S), subtitle, font=font("segoeui.ttf", 9), fill=rgba(t["muted"]))

    for box in pills:
        shadow(img, box, 14, t["shadow"], 18, 14, 8)
        rounded(img, box, 14, rgba(*t.get("pill_fill", ("#FFFFFF", 225))), outline=rgba(*t.get("edge", ("#FFFFFF", 255))))
    for box in cards:
        surface(img, box, t)
    d = ImageDraw.Draw(img)
    for x, y, code, label in kpis:
        rounded(img, (x + 16, y + 14, x + 46, y + 44), 10, rgba(t["chip"]))
        d = ImageDraw.Draw(img)
        glyph(d, (x + 31, y + 29), code, 11, rgba(t["accent"]))
        tracked(d, (x + 56, y + 23), label.upper(), font("seguisb.ttf", 7), rgba(t["muted"]))
    for x, y in info:
        glyph(d, (x, y), 0xE946, 9.5, rgba(t["faint"]))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, optimize=True)
    print("wrote", out)


SALES = dict(
    canvas="#F3F4F9", ink="#1D1D1F", muted="#8A8FA3", faint="#C3C7D6", card="#FFFFFF", shadow="#5B6690",
    accent="#5E6AD2", accent2="#8B93F0", chip="#EEF0FD",
    blobs=[((760, -320, 1500, 280), "#DCD8FF", 210, 110), ((-300, 380, 420, 1000), "#D6E6FF", 200, 120),
           ((520, 520, 1100, 980), "#FFE3EE", 120, 130)],
)
SALES_NAV = [0xE80F, 0xE7B8, 0xE716, 0xE71D]  # overview, products, customers, detail

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "01_Sales-Analytics" / "assets"
    kx = [92, 308, 524, 740]
    cards = [(x, 76, x + 200, 196) for x in kx] + [
        (92, 212, 612, 448), (628, 212, 940, 448), (92, 464, 392, 696), (408, 464, 940, 696), (956, 76, 1256, 696)]
    kpis = [(kx[0], 76, 0xEAFC, "Revenue"), (kx[1], 76, 0xE7C1, "Target attainment"),
            (kx[2], 76, 0xE94C, "Gross margin"), (kx[3], 76, 0xE7BF, "Avg order value")]
    info = [(592, 232), (920, 232), (372, 484), (920, 484), (1236, 96)]
    pills = [(956, 10, 1098, 66), (1114, 10, 1256, 66)]
    make(root / "bg_overview.png", SALES, "Sales Overview", "Northwind Trading   ·   FY 2026 year to date   ·   demo data",
         SALES_NAV, 0, cards, kpis, info, pills)
    sub = "Northwind Trading   ·   FY 2026 year to date   ·   demo data"
    kw = [92, 387, 682, 977]
    wide = lambda labels: ([(x, 76, x + 279, 196) for x in kw], [(x, 76, c, l) for x, (c, l) in zip(kw, labels)])
    corner = lambda boxes: [(x1 - 20, y0 + 20) for (_, y0, x1, _) in boxes]

    k_cards, k = wide([(0xEAFC, "Gross profit"), (0xE94C, "Gross margin"), (0xE8EC, "Avg discount"), (0xE7B8, "Units sold")])
    body = [(92, 212, 432, 448), (448, 212, 1256, 448), (92, 464, 612, 696), (628, 464, 1256, 696)]
    make(root / "bg_products.png", SALES, "Products & Margin", sub, SALES_NAV, 1, k_cards + body, k, corner(body), pills)

    k_cards, k = wide([(0xE716, "Active customers"), (0xE8EF, "Orders per customer"), (0xE77B, "Revenue per customer"), (0xE7BF, "Orders")])
    body = [(92, 212, 472, 448), (488, 212, 868, 448), (884, 212, 1256, 448), (92, 464, 708, 696), (724, 464, 1256, 696)]
    make(root / "bg_customers.png", SALES, "Customers & Reps", sub, SALES_NAV, 2, k_cards + body, k, corner(body), pills)

    k_cards, k = wide([(0xE7BF, "Orders"), (0xE7B8, "Units sold"), (0xEAFC, "Revenue"), (0xE8EC, "Avg discount")])
    body = [(92, 212, 1256, 696)]
    make(root / "bg_detail.png", SALES, "Order Detail", sub, SALES_NAV, 3, k_cards + body, k, corner(body),
         [(640, 10, 782, 66), (798, 10, 940, 66)] + pills)
