"""Glass "bento" backgrounds for 04_Finance-Operations.

Near-black canvas with a blue and an orange aurora, translucent cards with a lit top edge, a slim
icon rail. Geometry here is the single source of truth: build_finance.sh places visuals on the same boxes.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from make_background import H, S, W, blob, font, glyph, gradient_chip, rgba, shadow, tracked

INK, SOFT, MUTED, FAINT = "#F3F5FA", "#C9D0DE", "#8D96AA", "#5F6880"
BLUE, VIOLET, ORANGE, GOOD = "#4C8DFF", "#9B7BFF", "#FF8A3D", "#5BE3B0"
CANVAS = "#05070D"
BLOBS = [((820, -360, 1500, 260), "#2456E8", 215, 150), ((980, 230, 1520, 660), "#F0701F", 175, 150),
         ((-320, 380, 360, 980), "#4A32C8", 150, 150), ((300, 520, 900, 1000), "#0E3A8A", 70, 150),
         ((330, -260, 760, 80), "#5B3FD0", 40, 130)]
RAIL = (16, 16, 64, 704)
NAV = [0xE80F, 0xE9F9]                      # overview, statement
NAV_Y = [104, 152]                          # icon centres; nav buttons in the build script use the same
SLICER = (1122, 8, 1264, 62)


def glass(img, box, radius=18, tint=("#0C1222", 122)):
    """Translucent dark pane: soft shadow, tinted fill, sheen fading down from the top, edge lit from above."""
    shadow(img, box, radius, "#000000", 120, 22, 12)
    x0, y0, x1, y1 = [int(v * S) for v in box]
    w, h = x1 - x0, y1 - y0
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius * S, fill=255)
    pane = Image.new("RGBA", (w, h), rgba(*tint))
    fall = Image.linear_gradient("L").resize((w, h))                      # 0 at top, 255 at bottom
    sheen = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    sheen.putalpha(fall.point(lambda v: max(0, 20 - v // 6)))
    pane.alpha_composite(sheen)
    edge = Image.new("L", (w, h), 0)
    ImageDraw.Draw(edge).rounded_rectangle([0, 0, w - 1, h - 1], radius * S, outline=255, width=S)
    rim = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    rim.putalpha(Image.composite(fall.point(lambda v: max(16, 78 - v // 3)), Image.new("L", (w, h), 0), edge))
    pane.alpha_composite(rim)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layer.paste(pane, (x0, y0), mask)
    img.alpha_composite(layer)


def chip(img, box, color, code, size=10.5, radius=8):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle([v * S for v in box], radius * S, fill=rgba(color, 44), outline=rgba(color, 70), width=1)
    img.alpha_composite(layer)
    glyph(ImageDraw.Draw(img), ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), code, size, rgba(color))


WELL = "#0A0F1C"                            # solid inset behind native tables; the table cells use the same colour


def well(img, box, radius=12):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle([v * S for v in box], radius * S, fill=rgba(WELL, 235), outline=rgba("#FFFFFF", 16), width=S)
    img.alpha_composite(layer)


def make(out, title, active, cards, tiles=(), hero=None, wells=()):
    """cards: [(box, title or None)], tiles: [(box, colour, glyph, label)], hero: (box, colour, glyph, label)."""
    img = Image.new("RGBA", (W * S, H * S), rgba(CANVAS))
    for box, color, alpha, blur in BLOBS:
        blob(img, box, color, alpha, blur)
    # fine grain so the gradients do not band
    noise = Image.effect_noise((W * S, H * S), 10).convert("L").point(lambda v: 12 if v > 128 else 0)
    grain = Image.new("RGBA", img.size, (255, 255, 255, 0))
    grain.putalpha(noise)
    img.alpha_composite(grain)

    # rail
    glass(img, RAIL, 22)
    shadow(img, (26, 28, 54, 56), 9, BLUE, 120, 8, 3)
    gradient_chip(img, (26, 28, 54, 56), 9, BLUE, VIOLET)
    d = ImageDraw.Draw(img)
    d.line([(33 * S, 47 * S), (38 * S, 41 * S), (42 * S, 44 * S), (48 * S, 36 * S)], fill=rgba("#FFFFFF"), width=int(1.8 * S), joint="curve")
    for i, code in enumerate(NAV):
        cy = NAV_Y[i]
        if i == active:
            shadow(img, (24, cy - 16, 56, cy + 16), 10, BLUE, 110, 9, 3)
            gradient_chip(img, (24, cy - 16, 56, cy + 16), 10, BLUE, "#3D6BF5")
            glyph(ImageDraw.Draw(img), (40, cy), code, 12, rgba("#FFFFFF"))
        else:
            glyph(ImageDraw.Draw(img), (40, cy), code, 12, rgba(MUTED))
    d = ImageDraw.Draw(img)
    d.line([28 * S, 664 * S, 52 * S, 664 * S], fill=rgba("#FFFFFF", 26), width=S)
    glyph(d, (40, 684), 0xE946, 12, rgba(MUTED))

    # header + slicer pill
    d.text((84 * S, 12 * S), title, font=font("seguisb.ttf", 16.5), fill=rgba(INK))
    glass(img, SLICER, 14)

    for box, name in cards:
        glass(img, box)
        d = ImageDraw.Draw(img)
        if name:
            d.text(((box[0] + 18) * S, (box[1] + 13) * S), name, font=font("seguisb.ttf", 10.5), fill=rgba(INK))
            glyph(d, (box[2] - 20, box[1] + 22), 0xE946, 9.5, rgba(FAINT))
    for box in wells:
        well(img, box)
    if hero:
        box, color, code, label = hero
        glass(img, box)
        chip(img, (box[0] + 18, box[1] + 16, box[0] + 46, box[1] + 44), color, code, 11.5, 9)
        glyph(ImageDraw.Draw(img), (box[2] - 20, box[1] + 22), 0xE946, 9.5, rgba(FAINT))
    for box, color, code, label in tiles:
        glass(img, box, 16)
        chip(img, (box[0] + 12, box[1] + 11, box[0] + 36, box[1] + 35), color, code, 9.5)
        tracked(ImageDraw.Draw(img), (box[0] + 44, box[1] + 18), label.upper(), font("seguisb.ttf", 6.8), rgba(MUTED), 0.7)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, optimize=True)
    print("wrote", out)


# Row bands: 72-272, 284-494, 506-704
OVERVIEW = dict(
    hero=((80, 72, 500, 272), BLUE, 0xEAFC, "Net revenue"),
    tiles=[((512, 72, 700, 166), BLUE, 0xE94C, "Gross margin"), ((712, 72, 900, 166), VIOLET, 0xE9D9, "EBITDA margin"),
           ((512, 178, 700, 272), GOOD, 0xE8C7, "Net income"), ((712, 178, 900, 272), ORANGE, 0xE8EC, "OpEx ratio")],
    cards=[((912, 72, 1264, 272), "Budget attainment"), ((80, 284, 640, 494), "Revenue to net income"),
           ((652, 284, 948, 494), "OpEx vs budget"), ((960, 284, 1264, 494), "Cash position"),
           ((80, 506, 470, 704), "Cash conversion cycle"), ((482, 506, 850, 704), "Open receivables"),
           ((862, 506, 1264, 704), "Most overdue customers")],
    wells=[(872, 540, 1254, 694)],
)
STATEMENT = dict(cards=[((80, 72, 772, 704), "Income statement  ·  $ thousands"), ((784, 72, 1264, 372), "EBITDA vs budget by month"),
                        ((784, 384, 1264, 704), "OpEx by department")],
                 wells=[(90, 108, 762, 694), (794, 420, 1254, 694)])

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "04_Finance-Operations" / "assets"
    make(root / "bg_overview.png", "Finance Command Center", 0, **OVERVIEW)
    make(root / "bg_statement.png", "Income Statement", 1, **STATEMENT)
