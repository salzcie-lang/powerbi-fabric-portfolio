"""Editorial split-screen backgrounds for 03_Real-Estate.

A different design language from Sales (side rail, cards) and CRM (dark, top tabs, KPI column):
no boxed cards and no shadows. The left 520px is a full-height "stage" for the Azure map or a
photo; the right column is typeset like a magazine page, with a serif headline, a deck line, a
KPI strip divided by hairlines, and sections introduced by a rule and a small-caps label.
"""
from pathlib import Path

from PIL import Image, ImageDraw

from make_background import H, S, W, font, glyph, rgba, tracked

T = dict(page="#FBFAF7", stage="#EFEAE1", ink="#1B221E", muted="#8A8578", faint="#BDB6A6", rule="#DDD6C8", accent="#2F6B4F")
STAGE_W = 520
COL_X, COL_W = 560, 688                       # right column
NAV = ["Portfolio", "Occupancy", "Collections", "Property"]
NAV_X, NAV_W = [912, 996, 1080, 1164], 84     # nav slots; buttons in relayout_re.sh use the same numbers
KPI_X = [560, 732, 904, 1076]                 # KPI strip columns, 172 wide


def hline(d, x0, x1, y, color=None):
    d.line([x0 * S, y * S, x1 * S, y * S], fill=rgba(color or T["rule"]), width=S)


def make(out, number, title, deck, active, kpis, blocks, filter_label="FILTER"):
    """blocks: (label, x, y, w) section headers; a rule, a small-caps label and an (i) marker."""
    img = Image.new("RGB", (W * S, H * S), rgba(T["page"])[:3])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, STAGE_W * S, H * S], fill=rgba(T["stage"])[:3])

    # eyebrow + text navigation
    tracked(d, (COL_X, 26), f"MERIDIAN PROPERTIES   /   {number:02d}", font("seguisb.ttf", 7), rgba(T["muted"]), tracking=1.2)
    for i, name in enumerate(NAV):
        cx = NAV_X[i] + NAV_W / 2
        f = font("seguisb.ttf" if i == active else "segoeui.ttf", 9)
        d.text((cx * S, 30 * S), name, font=f, anchor="mm", fill=rgba(T["ink"] if i == active else T["muted"]))
        if i == active:
            tw = d.textlength(name, font=f) / S
            d.line([(cx - tw / 2) * S, 41 * S, (cx + tw / 2) * S, 41 * S], fill=rgba(T["accent"]), width=2 * S)

    # headline and deck
    d.text((COL_X * S, 52 * S), title, font=font("georgiab.ttf", 25), fill=rgba(T["ink"]))
    d.text((COL_X * S, 95 * S), deck, font=font("segoeui.ttf", 9.5), fill=rgba(T["muted"]))

    # KPI strip
    hline(d, COL_X, COL_X + COL_W, 122)
    for i, label in enumerate(kpis):
        tracked(d, (KPI_X[i] + 4, 134), label.upper(), font("seguisb.ttf", 7), rgba(T["muted"]), tracking=0.9)
        if i:
            d.line([(KPI_X[i] - 10) * S, 134 * S, (KPI_X[i] - 10) * S, 214 * S], fill=rgba(T["rule"]), width=S)
    hline(d, COL_X, COL_X + COL_W, 226)

    # filter row
    tracked(d, (COL_X + 4, 254), filter_label, font("seguisb.ttf", 7), rgba(T["muted"]), tracking=0.9)

    for label, x, y, w in blocks:
        hline(d, x, x + w, y, T["ink"] if x >= COL_X else T["faint"])
        tracked(d, (x, y + 9), label.upper(), font("seguisb.ttf", 7), rgba(T["ink"]), tracking=0.9)
        glyph(d, (x + w - 8, y + 14), 0xE946, 9, rgba(T["faint"]))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    print("wrote", out)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "03_Real-Estate" / "assets"
    make(root / "bg_portfolio.png", 1, "The portfolio at a glance",
         "36 properties across six metros. Each pin is a building; terracotta means it is under 90% occupied.", 0,
         ["Portfolio value", "Occupancy", "Net operating income", "Collection rate"],
         [("Properties, ranked by net operating income", 560, 300, 688)])
    make(root / "bg_occupancy.png", 2, "Who is in, and who is leaving",
         "Occupancy is counted on the last day of the period. Leases ending soon are the rent most at risk.", 1,
         ["Occupancy", "Vacant units", "Avg rent per unit", "Leases ending, 90 days"],
         [("Vacant units by city", 560, 300, 332), ("Occupancy by property type", 916, 300, 332),
          ("Leases ending in the next 90 days", 560, 502, 688), ("Occupancy by month, this year vs last (dashed)", 24, 310, 472)])
    make(root / "bg_collections.png", 3, "What came in, what went out",
         "Rent collected against rent due, and what is left after operating expenses.", 2,
         ["Rent collected", "Outstanding rent", "Net operating income", "NOI margin"],
         [("Payments by status", 560, 300, 332), ("Operating expenses by category", 916, 300, 332),
          ("Net operating income by property", 560, 502, 688), ("Rent collected against rent due (dashed)", 24, 310, 472)])
    make(root / "bg_property.png", 4, "One building, up close",
         "Pick a property to see its unit mix, income and maintenance load.", 3,
         ["Occupancy", "Net operating income", "Avg rent per unit", "Open requests"],
         [("Units by type", 560, 300, 688), ("Rent collected and NOI by month", 560, 502, 688),
          ("About this property", 24, 378, 472), ("Maintenance requests by category", 24, 500, 472)],
         filter_label="PROPERTY")
