"""Dark backgrounds for 02_CRM-Pipeline.

Layout is deliberately different from the Sales report: a top bar with pill tabs instead of a side
rail, a tall KPI column on the left, and a wide content area on the right.
"""
from pathlib import Path

from PIL import Image, ImageDraw

from make_background import H, S, W, blob, font, glyph, gradient_chip, rgba, rounded, shadow, surface, tracked

T = dict(
    canvas="#0B0E13", ink="#F2F4F7", muted="#8B95A7", faint="#4B5565", card="#161B22", card_alpha=255,
    edge=("#2A313C", 255), shadow="#000000", shadow_alpha=(120, 90),
    accent="#2DD4BF", accent2="#5EEAD4", on_accent="#06231F", chip="#12302E", line="#232A34",
    blobs=[((700, -380, 1560, 320), "#134E4A", 170, 130), ((-360, 420, 420, 1040), "#1E293B", 200, 130),
           ((420, 560, 1000, 1000), "#0F3D3A", 90, 140)],
)
TABS = ["Overview", "Funnel", "Reps", "Deals"]
TAB_X, TAB_W, TAB_GAP = 304, 76, 4          # nav buttons in build/relayout scripts use the same numbers
KPI_BOX = (24, 78, 300, 696)
KPI_SLOT = 154                              # height of one KPI in the left column
SUB = "Helix CRM  ·  FY 2026 year to date  ·  demo data"
PILLS = [(956, 10, 1098, 64), (1114, 10, 1256, 64)]


def make(out, title, active, kpis, cards, pills=PILLS):
    img = Image.new("RGBA", (W * S, H * S), rgba(T["canvas"]))
    for box, color, alpha, blur in T["blobs"]:
        blob(img, box, color, alpha, blur)

    # brand chip + title
    shadow(img, (24, 20, 54, 50), 9, T["accent"], 70, 8, 4)
    gradient_chip(img, (24, 20, 54, 50), 9, T["accent"], T["accent2"])
    d = ImageDraw.Draw(img)
    for i, h in enumerate((7, 11, 15)):
        bx = (31 + i * 6) * S
        d.rounded_rectangle([bx, (44 - h) * S, bx + 3 * S, 44 * S], S, fill=rgba(T["on_accent"]))
    d.text((66 * S, 15 * S), title, font=font("seguisb.ttf", 16), fill=rgba(T["ink"]))
    d.text((66 * S, 41 * S), SUB, font=font("segoeui.ttf", 8.5), fill=rgba(T["muted"]))

    # pill tabs
    group = (TAB_X - 4, 18, TAB_X + 4 * TAB_W + 3 * TAB_GAP + 4, 56)
    shadow(img, group, 19, T["shadow"], 90, 12, 6)
    rounded(img, group, 19, rgba(T["card"]), outline=rgba(*T["edge"]))
    for i, name in enumerate(TABS):
        x0 = TAB_X + i * (TAB_W + TAB_GAP)
        if i == active:
            gradient_chip(img, (x0, 22, x0 + TAB_W, 52), 15, T["accent"], T["accent2"])
        d = ImageDraw.Draw(img)
        d.text(((x0 + TAB_W / 2) * S, 37 * S), name, font=font("seguisb.ttf", 9), anchor="mm",
               fill=rgba(T["on_accent"] if i == active else T["muted"]))

    for box in pills:
        shadow(img, box, 14, T["shadow"], 90, 14, 8)
        rounded(img, box, 14, rgba(T["card"]), outline=rgba(*T["edge"]))

    # KPI column
    surface(img, KPI_BOX, T)
    d = ImageDraw.Draw(img)
    for i, (code, label) in enumerate(kpis):
        y0 = KPI_BOX[1] + i * KPI_SLOT
        if i:
            d.line([40 * S, y0 * S, 284 * S, y0 * S], fill=rgba(T["line"]), width=S)
        rounded(img, (40, y0 + 18, 70, y0 + 48), 10, rgba(T["chip"]))
        d = ImageDraw.Draw(img)
        glyph(d, (55, y0 + 33), code, 11, rgba(T["accent2"]))
        tracked(d, (80, y0 + 27), label.upper(), font("seguisb.ttf", 7), rgba(T["muted"]))

    for box in cards:
        surface(img, box, T)
    d = ImageDraw.Draw(img)
    for (_, y0, x1, _) in cards:
        glyph(d, (x1 - 20, y0 + 20), 0xE946, 9.5, rgba(T["faint"]))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, optimize=True)
    print("wrote", out)


LAYOUT = {
    "overview": [(316, 78, 876, 380), (892, 78, 1256, 380), (316, 396, 566, 696), (582, 396, 962, 696), (978, 396, 1256, 696)],
    "funnel": [(316, 78, 636, 380), (652, 78, 946, 380), (962, 78, 1256, 380), (316, 396, 776, 696), (792, 396, 1256, 696)],
    "reps": [(316, 78, 896, 696), (912, 78, 1256, 380), (912, 396, 1256, 696)],
    "deals": [(316, 78, 1256, 696)],
}

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "02_CRM-Pipeline" / "assets"
    make(root / "bg_overview.png", "Pipeline Overview", 0,
         [(0xEAFC, "Won revenue"), (0xE8A9, "Open pipeline"), (0xE7C1, "Win rate"), (0xE8C7, "Avg deal size")], LAYOUT["overview"])
    make(root / "bg_funnel.png", "Funnel & Conversion", 1,
         [(0xE716, "Leads"), (0xE8FA, "Qualification rate"), (0xE7C1, "Lead to win rate"), (0xE823, "Avg sales cycle (days)")], LAYOUT["funnel"])
    make(root / "bg_reps.png", "Rep Performance", 2,
         [(0xE7C1, "Quota attainment"), (0xE77B, "Reps at quota"), (0xE8BC, "Activities"), (0xE8A9, "Weighted pipeline")], LAYOUT["reps"])
    make(root / "bg_deals.png", "Deal Detail", 3,
         [(0xEAFC, "Won deals"), (0xE8A9, "Weighted pipeline"), (0xE8C7, "Open pipeline"), (0xE946, "Stalled deals")], LAYOUT["deals"],
         [(640, 10, 782, 64), (798, 10, 940, 64)] + PILLS)
