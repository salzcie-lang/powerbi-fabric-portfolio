"""Semantic model spec for 04_Finance-Operations (CFO command center).

Besides the usual base measures, this model carries the SVG measures that draw the bespoke
visuals (glow area chart, ring gauges, waterfall, capsule bars). Each returns an SVG data URI
sized to the image visual it is shown in, so 1 SVG unit is 1 report pixel.
"""
from pathlib import Path

from pbi_model import build, col, measure

PROJECT = Path(__file__).resolve().parents[1] / "04_Finance-Operations"
INK, SOFT, MUTED, FAINT = "#F3F5FA", "#C9D0DE", "#8D96AA", "#5F6880"
BLUE, BLUE2, VIOLET, ORANGE, ORANGE2, GOOD, BAD = "#4C8DFF", "#7AB0FF", "#9B7BFF", "#FF8A3D", "#FFB86B", "#5BE3B0", "#FF6B7A"
FONT = "font-family='Segoe UI'"
UP, DOWN = "M0 7 L4.5 0 L9 7 Z", "M0 0 L9 0 L4.5 7 Z"

tables = {
    "GL": ("gl_actuals.csv", [col("Month", "date", hidden=True), col("AccountCode", "int", hidden=True),
                              col("DepartmentKey", "int", hidden=True), col("Amount", "money", hidden=True)]),
    "Budget": ("budget.csv", [col("Month", "date", hidden=True), col("AccountCode", "int", hidden=True),
                              col("DepartmentKey", "int", hidden=True), col("Budget Amount", "money", "BudgetAmount", hidden=True)]),
    "Accounts": ("chart_of_accounts.csv", [
        col("AccountCode", "int", hidden=True), col("Account", "text"), col("Account Group", "text", "AccountGroup", sort_by="Section Order"),
        col("PnL Section", "text", "PnLSection", sort_by="Section Order"), col("Section Order", "int", "SectionOrder", hidden=True)]),
    "Departments": ("departments.csv", [col("DepartmentKey", "int", hidden=True), col("Department", "text"),
                                        col("Cost Center Owner", "text", "CostCenterOwner")]),
    "Receivables": ("ar_invoices.csv", [
        col("Invoice Number", "text", "InvoiceNumber"), col("Customer", "text"), col("Invoice Date", "date", "InvoiceDate"),
        col("Due Date", "date", "DueDate"), col("Terms Days", "int", "TermsDays"), col("Amount", "money", hidden=True),
        col("Paid Date", "date", "PaidDate"), col("Status", "text")]),
    "Inventory": ("inventory_snapshots.csv", [col("Month", "date", hidden=True), col("Product Category", "text", "ProductCategory"),
                                              col("Inventory Value", "money", "InventoryValue", hidden=True)]),
    "Cash": ("cash_monthly.csv", [col("Month", "date", hidden=True), col("Cash Balance", "money", "CashBalance", hidden=True),
                                  col("Accounts Payable", "money", "AccountsPayable", hidden=True),
                                  col("Operating Cash Flow", "money", "OperatingCashFlow", hidden=True),
                                  col("Capex", "money", hidden=True)]),
    "PnL Lines": ("pnl_lines.csv", [col("Line Order", "int", "LineOrder", hidden=True), col("Line", "text", sort_by="Line Order"),
                                    col("Line Type", "text", "LineType", hidden=True), col("AccountCode", "int", hidden=True),
                                    col("Line Name", "text", "LineName"), col("Bridge Order", "int", "BridgeOrder", hidden=True),
                                    col("Bridge Label", "text", "BridgeLabel", sort_by="Bridge Order"), col("Line Group", "text", "LineGroup", hidden=True)]),
}
relationships = [
    ("GL.Month", "Date.Date"), ("GL.AccountCode", "Accounts.AccountCode"), ("GL.DepartmentKey", "Departments.DepartmentKey"),
    ("Budget.Month", "Date.Date"), ("Budget.AccountCode", "Accounts.AccountCode"), ("Budget.DepartmentKey", "Departments.DepartmentKey"),
    ("Receivables.Invoice Date", "Date.Date"), ("Inventory.Month", "Date.Date"), ("Cash.Month", "Date.Date"),
]

# ------------------------------------------------------------------ base measures
PY = """
VAR _Last = [As Of Date]
RETURN
    CALCULATE (
        {expr},
        SAMEPERIODLASTYEAR ( 'Date'[Date] ),
        'Date'[Date] <= EDATE ( _Last, -12 )
    )
"""
SECTIONS = {"Revenue": "Revenue", "COGS": "COGS", "OpEx": "OpEx", "Below EBITDA": "Below EBITDA"}
measures = [
    measure("As Of Date", "EOMONTH ( CALCULATE ( MAX ( GL[Month] ), REMOVEFILTERS () ), 0 )", "dd mmm yyyy", "0. Base",
            "Last day of the latest month with posted actuals; used as today."),
    measure("Period End", "MIN ( MAX ( 'Date'[Date] ), [As Of Date] )", "dd mmm yyyy", "0. Base",
            "Last date of the selection, capped at the as-of date. Balances are read at this date."),
    measure("GL Amount", "SUM ( GL[Amount] )", "$#,##0", "0. Base"),
    measure("Budget Amount", "SUM ( Budget[Budget Amount] )", "$#,##0", "0. Base"),
]
for sfx, base in (("", "[GL Amount]"), (" Budget", "[Budget Amount]")):
    folder = "1. P&L" if not sfx else "2. Budget"
    for name, section in SECTIONS.items():
        measures.append(measure(f"{name}{sfx}", f'CALCULATE ( {base}, Accounts[PnL Section] = "{section}" )', "$#,##0", folder))
    measures += [
        measure(f"Gross Profit{sfx}", f"[Revenue{sfx}] - [COGS{sfx}]", "$#,##0", folder),
        measure(f"Gross Margin{sfx}", f"DIVIDE ( [Gross Profit{sfx}], [Revenue{sfx}] )", "0.0%", folder),
        measure(f"EBITDA{sfx}", f"[Gross Profit{sfx}] - [OpEx{sfx}]", "$#,##0", folder),
        measure(f"EBITDA Margin{sfx}", f"DIVIDE ( [EBITDA{sfx}], [Revenue{sfx}] )", "0.0%", folder),
        measure(f"Net Income{sfx}", f"[EBITDA{sfx}] - [Below EBITDA{sfx}]", "$#,##0", folder),
        measure(f"Net Margin{sfx}", f"DIVIDE ( [Net Income{sfx}], [Revenue{sfx}] )", "0.0%", folder),
        measure(f"OpEx Ratio{sfx}", f"DIVIDE ( [OpEx{sfx}], [Revenue{sfx}] )", "0.0%", folder, "Operating expenses as a share of revenue."),
    ]
measures += [
    measure("Depreciation", "CALCULATE ( [GL Amount], Accounts[AccountCode] = 7000 )", "$#,##0", "1. P&L"),
    measure("Interest and Tax", "CALCULATE ( [GL Amount], Accounts[AccountCode] IN { 7100, 7200 } )", "$#,##0", "1. P&L"),
    measure("OpEx Variance", "[OpEx] - [OpEx Budget]", "$#,##0", "2. Budget"),
    measure("OpEx Variance %", "DIVIDE ( [OpEx] - [OpEx Budget], [OpEx Budget] )", "+0.0%;-0.0%", "2. Budget"),
    measure("Revenue Attainment", "DIVIDE ( [Revenue], [Revenue Budget] )", "0.0%", "2. Budget"),
    measure("Gross Profit Attainment", "DIVIDE ( [Gross Profit], [Gross Profit Budget] )", "0.0%", "2. Budget"),
    measure("EBITDA Attainment", "DIVIDE ( [EBITDA], [EBITDA Budget] )", "0.0%", "2. Budget"),
    measure("Net Income Attainment", "DIVIDE ( [Net Income], [Net Income Budget] )", "0.0%", "2. Budget"),
    # ---- cash and working capital (balances are read at [Period End])
    measure("Cash Balance", """
VAR _pe = [Period End]
RETURN
    CALCULATE ( SUM ( Cash[Cash Balance] ), REMOVEFILTERS ( 'Date' ), Cash[Month] = EOMONTH ( _pe, -1 ) + 1 )
""", "$#,##0", "3. Cash", "Cash at the end of the selected period."),
    measure("Cash Change", """
VAR _first = MIN ( 'Date'[Date] )
VAR _open = CALCULATE ( SUM ( Cash[Cash Balance] ), REMOVEFILTERS ( 'Date' ), Cash[Month] = EOMONTH ( _first, -2 ) + 1 )
RETURN
    IF ( NOT ISBLANK ( _open ), [Cash Balance] - _open )
""", "$#,##0", "3. Cash", "Change in cash since the start of the selected period."),
    measure("Operating Cash Flow", "SUM ( Cash[Operating Cash Flow] )", "$#,##0", "3. Cash"),
    measure("Capex", "SUM ( Cash[Capex] )", "$#,##0", "3. Cash"),
    measure("Free Cash Flow", "[Operating Cash Flow] - [Capex]", "$#,##0", "3. Cash"),
    measure("Cash Cover Months", """
VAR _pe = [Period End]
VAR _cost = CALCULATE ( [COGS] + [OpEx], REMOVEFILTERS ( 'Date' ), DATESINPERIOD ( 'Date'[Date], _pe, -3, MONTH ) )
RETURN
    DIVIDE ( [Cash Balance], _cost / 3 )
""", "0.0", "3. Cash", "Cash divided by average monthly operating cost over the last three months."),
    measure("AR Balance", """
VAR _pe = [Period End]
RETURN
    CALCULATE (
        SUM ( Receivables[Amount] ),
        REMOVEFILTERS ( 'Date' ),
        FILTER (
            ALL ( Receivables[Invoice Date], Receivables[Paid Date] ),
            Receivables[Invoice Date] <= _pe && ( ISBLANK ( Receivables[Paid Date] ) || Receivables[Paid Date] > _pe )
        )
    )
""", "$#,##0", "4. Working capital", "Invoices issued and not yet paid at the end of the period."),
    measure("Inventory Value", """
VAR _pe = [Period End]
RETURN
    CALCULATE ( SUM ( Inventory[Inventory Value] ), REMOVEFILTERS ( 'Date' ), Inventory[Month] = EOMONTH ( _pe, -1 ) + 1 )
""", "$#,##0", "4. Working capital"),
    measure("AP Balance", """
VAR _pe = [Period End]
RETURN
    CALCULATE ( SUM ( Cash[Accounts Payable] ), REMOVEFILTERS ( 'Date' ), Cash[Month] = EOMONTH ( _pe, -1 ) + 1 )
""", "$#,##0", "4. Working capital"),
    measure("Revenue T3M", """
VAR _pe = [Period End]
RETURN
    CALCULATE ( [Revenue], REMOVEFILTERS ( 'Date' ), DATESINPERIOD ( 'Date'[Date], _pe, -3, MONTH ) )
""", "$#,##0", "4. Working capital"),
    measure("COGS T3M", """
VAR _pe = [Period End]
RETURN
    CALCULATE ( [COGS], REMOVEFILTERS ( 'Date' ), DATESINPERIOD ( 'Date'[Date], _pe, -3, MONTH ) )
""", "$#,##0", "4. Working capital"),
    measure("DSO", "DIVIDE ( [AR Balance], [Revenue T3M] ) * 91", "0", "4. Working capital", "Days sales outstanding."),
    measure("DIO", "DIVIDE ( [Inventory Value], [COGS T3M] ) * 91", "0", "4. Working capital", "Days inventory outstanding."),
    measure("DPO", "DIVIDE ( [AP Balance], [COGS T3M] ) * 91", "0", "4. Working capital", "Days payables outstanding."),
    measure("Cash Conversion Cycle", "[DSO] + [DIO] - [DPO]", "0", "4. Working capital"),
]

AGING = [("Current", None, 0), ("1-30", 0, 30), ("31-60", 30, 60), ("61-90", 60, 90), ("90+", 90, None)]
for label, lo, hi in AGING:
    cond = " && ".join(c for c in (f"_pe - Receivables[Due Date] > {lo}" if lo is not None else "",
                                   f"_pe - Receivables[Due Date] <= {hi}" if hi is not None else "") if c)
    for what, agg in (("AR", "SUM ( Receivables[Amount] )"), ("Invoices", "COUNTROWS ( Receivables )")):
        if what == "Invoices" and label != "90+":
            continue
        measures.append(measure(f"{what} {label}", f"""
VAR _pe = [Period End]
RETURN
    CALCULATE (
        {agg},
        REMOVEFILTERS ( 'Date' ),
        FILTER (
            ALL ( Receivables[Invoice Date], Receivables[Paid Date], Receivables[Due Date] ),
            Receivables[Invoice Date] <= _pe && ( ISBLANK ( Receivables[Paid Date] ) || Receivables[Paid Date] > _pe )
                && {cond}
        )
    )
""", "$#,##0" if what == "AR" else "#,##0", "4. Working capital"))
measures += [
    measure("AR Overdue", "[AR Balance] - [AR Current]", "$#,##0", "4. Working capital", "Open receivables past their due date."),
    measure("Oldest Days Overdue", """
VAR _pe = [Period End]
RETURN
    CALCULATE (
        MAXX ( Receivables, DATEDIFF ( Receivables[Due Date], _pe, DAY ) ),
        REMOVEFILTERS ( 'Date' ),
        FILTER (
            ALL ( Receivables[Invoice Date], Receivables[Paid Date] ),
            Receivables[Invoice Date] <= _pe && ( ISBLANK ( Receivables[Paid Date] ) || Receivables[Paid Date] > _pe )
        )
    )
""", "0", "4. Working capital", "Days past due of the oldest open invoice."),
    measure("Days Overdue Color", f'SWITCH ( TRUE (), [Oldest Days Overdue] > 90, "{BAD}", [Oldest Days Overdue] > 30, "{ORANGE2}", "{SOFT}" )',
            None, "9. Formatting"),
]
measures.append(measure("AR Overdue %", "DIVIDE ( [AR Balance] - [AR Current], [AR Balance] )", "0.0%", "4. Working capital"))

PY_OF = ["GL Amount", "Revenue", "COGS", "Gross Profit", "Gross Margin", "OpEx", "EBITDA", "EBITDA Margin", "Net Income", "Net Margin",
         "OpEx Ratio", "DSO", "DIO", "DPO", "Cash Conversion Cycle", "AR Balance"]
FMT = {m["name"]: m["fmt"] for m in measures}
measures += [measure(f"{n} PY", PY.format(expr=f"[{n}]"), FMT[n], "5. Prior year") for n in PY_OF]

# ------------------------------------------------------------------ P&L statement (page 2)
COST_LINES = "{ 5, 8, 9, 10, 11, 12, 13, 14, 17, 18, 19 }"


def pnl_switch(sfx, account_measure):
    return f"""
VAR _o = SELECTEDVALUE ( 'PnL Lines'[Line Order] )
VAR _acc = SELECTEDVALUE ( 'PnL Lines'[AccountCode] )
RETURN
    SWITCH (
        TRUE (),
        _o = 1, [Revenue{sfx}],
        _o = 5, [COGS{sfx}],
        _o = 6, [Gross Profit{sfx}],
        _o = 7, [Gross Margin{sfx}],
        _o = 8, [OpEx{sfx}],
        _o = 15, [EBITDA{sfx}],
        _o = 16, [EBITDA Margin{sfx}],
        _o = 20, [Net Income{sfx}],
        _o = 21, [Net Margin{sfx}],
        _acc > 0, CALCULATE ( {account_measure}, Accounts[AccountCode] = _acc )
    )
"""


def pnl_text(m):
    return f"""
VAR _v = [{m}]
RETURN
    IF (
        NOT ISBLANK ( _v ),
        IF ( SELECTEDVALUE ( 'PnL Lines'[Line Type] ) = "ratio", FORMAT ( _v, "0.0%" ), FORMAT ( _v / 1000, "#,##0" ) )
    )
"""


def pnl_var(base, mode):
    """Variance text of PnL Value against [base]; mode 'abs' or 'pct'."""
    body = ('IF ( _ratio, FORMAT ( ( _a - _b ) * 100, "+0.0;-0.0" ) & " pts", FORMAT ( ( _a - _b ) / 1000, "+#,##0;-#,##0" ) )'
            if mode == "abs" else 'IF ( NOT _ratio, FORMAT ( DIVIDE ( _a - _b, ABS ( _b ) ), "+0.0%;-0.0%" ) )')
    return f"""
VAR _a = [PnL Value]
VAR _b = [{base}]
VAR _ratio = SELECTEDVALUE ( 'PnL Lines'[Line Type] ) = "ratio"
RETURN
    IF ( NOT ISBLANK ( _a ) && NOT ISBLANK ( _b ), {body} )
"""


def pnl_color(base):
    return f"""
VAR _a = [PnL Value]
VAR _b = [{base}]
VAR _cost = SELECTEDVALUE ( 'PnL Lines'[Line Order] ) IN {COST_LINES}
VAR _rel = IF ( SELECTEDVALUE ( 'PnL Lines'[Line Type] ) = "ratio", ( _a - _b ) * 10, DIVIDE ( _a - _b, ABS ( _b ) ) )
RETURN
    SWITCH ( TRUE (), ABS ( _rel ) < 0.005, "{MUTED}", ( _rel > 0 ) <> _cost, "{GOOD}", "{BAD}" )
"""


measures += [
    measure("PnL Value", pnl_switch("", "[GL Amount]"), "#,##0", "6. Statement"),
    measure("PnL Budget", pnl_switch(" Budget", "[Budget Amount]"), "#,##0", "6. Statement"),
    measure("PnL PY", pnl_switch(" PY", "[GL Amount PY]"), "#,##0", "6. Statement"),
    measure("PnL Variance", "[PnL Value] - [PnL Budget]", "$#,##0", "6. Statement"),
    measure("PnL Variance %", "DIVIDE ( [PnL Value] - [PnL Budget], ABS ( [PnL Budget] ) )", "+0.0%;-0.0%", "6. Statement"),
    measure("Pct of Revenue", "DIVIDE ( [PnL Value], [Revenue] )", "0.0%", "6. Statement"),
    measure("Interest", "CALCULATE ( [GL Amount], Accounts[AccountCode] = 7100 )", "$#,##0", "1. P&L"),
    measure("Income Tax", "CALCULATE ( [GL Amount], Accounts[AccountCode] = 7200 )", "$#,##0", "1. P&L"),
    measure("Bridge Low", """
SWITCH (
    SELECTEDVALUE ( 'PnL Lines'[Bridge Order] ),
    2, [Gross Profit],
    4, [EBITDA],
    6, [EBITDA] - [Depreciation],
    7, [EBITDA] - [Depreciation] - [Interest],
    8, [Net Income],
    0
)
""", "$#,##0", "6. Statement", "Lower edge of a bridge bar: zero for totals, the level after the deduction for cost steps."),
    measure("Bridge High", """
SWITCH (
    SELECTEDVALUE ( 'PnL Lines'[Bridge Order] ),
    1, [Revenue],
    2, [Revenue],
    3, [Gross Profit],
    4, [Gross Profit],
    5, [EBITDA],
    6, [EBITDA],
    7, [EBITDA] - [Depreciation],
    8, [Net Income] + [Income Tax],
    9, [Net Income]
)
""", "$#,##0", "6. Statement", "Upper edge of a bridge bar."),
    # Focus card: the headline follows the P&L line clicked in the bridge or the OpEx chart, revenue otherwise
    measure("Focus Value", "IF ( HASONEVALUE ( 'PnL Lines'[Line Order] ), [PnL Value], [Revenue] )", "$#,##0", "6. Statement"),
    measure("Focus Budget", "IF ( HASONEVALUE ( 'PnL Lines'[Line Order] ), [PnL Budget], [Revenue Budget] )", "$#,##0", "6. Statement"),
    measure("Focus PY", "IF ( HASONEVALUE ( 'PnL Lines'[Line Order] ), [PnL PY], [Revenue PY] )", "$#,##0", "6. Statement"),
    measure("Actual", pnl_text("PnL Value"), None, "6. Statement", "In thousands; ratios in percent."),
    measure("Budget", pnl_text("PnL Budget"), None, "6. Statement"),
    measure("Prior Year", pnl_text("PnL PY"), None, "6. Statement"),
    measure("Var vs Budget", pnl_var("PnL Budget", "abs"), None, "6. Statement"),
    measure("Var % vs Budget", pnl_var("PnL Budget", "pct"), None, "6. Statement"),
    measure("Var % vs PY", pnl_var("PnL PY", "pct"), None, "6. Statement"),
    measure("Budget Var Color", pnl_color("PnL Budget"), None, "9. Formatting"),
    measure("PY Var Color", pnl_color("PnL PY"), None, "9. Formatting"),
    measure("PnL Line Color", f"""
SWITCH ( SELECTEDVALUE ( 'PnL Lines'[Line Type] ), "detail", "{MUTED}", "ratio", "{BLUE2}", "{INK}" )
""", None, "9. Formatting"),
    measure("OpEx Variance Color", f"""
SWITCH ( TRUE (), ABS ( [OpEx Variance %] ) < 0.005, "{MUTED}", [OpEx Variance %] > 0, "{BAD}", "{GOOD}" )
""", None, "9. Formatting"),
]


# ------------------------------------------------------------------ SVG helpers
class X(str):
    """Raw DAX expression (anything else passed to cat() is emitted as a DAX string literal)."""


def q(s):
    return '"' + s.replace('"', '""') + '"'


def cat(*parts):
    return X(" &\n    ".join(p if isinstance(p, X) else q(p) for p in parts))


def F(e):
    return X(f'FORMAT ( {e}, "0.0", "en-US" )')


def money(e, decimals=2):
    d = "0" * decimals
    return X(f'IF ( ABS ( {e} ) >= 1000000, FORMAT ( {e} / 1000000, "$0.{d}", "en-US" ) & "M", FORMAT ( {e} / 1000, "$0", "en-US" ) & "K" )')


def text(x, y, body, size, fill=INK, weight=400, anchor="start", extra=""):
    """body: str or X. x, y, fill may be X as well."""
    out = ["<text x='", x if isinstance(x, X) else str(x), "' y='", y if isinstance(y, X) else str(y),
           f"' {FONT} font-size='{size}' font-weight='{weight}' text-anchor='{anchor}' {extra} fill='", fill, "'>", body, "</text>"]
    return cat(*out)


def svg(w, h, *parts, blur=5):
    head = (f"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}'><defs>"
            f"<linearGradient id='gB' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='{BLUE}'/><stop offset='1' stop-color='{VIOLET}'/></linearGradient>"
            f"<linearGradient id='gBv' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='{BLUE2}'/><stop offset='1' stop-color='#3D6BF5'/></linearGradient>"
            f"<linearGradient id='gO' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='{ORANGE2}'/><stop offset='1' stop-color='#FF6A3D'/></linearGradient>"
            f"<linearGradient id='gOv' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='{ORANGE2}'/><stop offset='1' stop-color='#FF7A3D'/></linearGradient>"
            f"<linearGradient id='gG' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#3CC8E0'/><stop offset='1' stop-color='{GOOD}'/></linearGradient>"
            f"<linearGradient id='gA' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='{BLUE}' stop-opacity='0.38'/><stop offset='1' stop-color='{BLUE}' stop-opacity='0'/></linearGradient>"
            f"<filter id='gl' filterUnits='userSpaceOnUse' x='0' y='0' width='{w}' height='{h}'><feGaussianBlur stdDeviation='{blur}'/></filter>"
            "</defs>")
    return cat(head, *parts, "</svg>")


def series(p, ms, x0, y0, w, h):
    """VAR lines for a smoothed monthly line of each measure in ms on a shared scale. Gives {p}Path{k}, {p}Area, {p}LX, {p}LY{k}, {p}Q."""
    cols = ", ".join(f'"@v{k}", {m}' for k, m in enumerate(ms))
    lo = "[@v0]" if len(ms) == 1 else "MIN ( [@v0], [@v1] )"
    hi = "[@v0]" if len(ms) == 1 else "MAX ( [@v0], [@v1] )"
    ys = ", ".join(f'"@y{k}", {y0 + h} - {h} * DIVIDE ( [@v{k}] - {p}Lo, {p}R )' for k in range(len(ms)))
    nys = ", ".join(f'"@ny{k}", VAR _i = [@i] RETURN MAXX ( FILTER ( {p}P2, [@i] = _i + 1 ), [@y{k}] )' for k in range(len(ms)))
    out = [
        f"VAR {p}T = ADDCOLUMNS ( FILTER ( VALUES ( 'Date'[Month Start] ), NOT ISBLANK ( {ms[0]} ) ), {cols} )",
        f"VAR {p}N = COUNTROWS ( {p}T )",
        f"VAR {p}F = MINX ( {p}T, 'Date'[Month Start] )",
        f"VAR {p}Lo = MINX ( {p}T, {lo} )",
        f"VAR {p}Hi = MAXX ( {p}T, {hi} )",
        f"VAR {p}R = IF ( {p}Hi - {p}Lo = 0, 1, {p}Hi - {p}Lo )",
        f"VAR {p}P1 = ADDCOLUMNS ( {p}T, \"@i\", DATEDIFF ( {p}F, 'Date'[Month Start], MONTH ) )",
        f'VAR {p}P2 = ADDCOLUMNS ( {p}P1, "@x", {x0} + {w} * DIVIDE ( [@i], {p}N - 1, 0.5 ), {ys} )',
        f'VAR {p}Q = ADDCOLUMNS ( {p}P2, "@nx", VAR _i = [@i] RETURN MAXX ( FILTER ( {p}P2, [@i] = _i + 1 ), [@x] ), {nys} )',
        f"VAR {p}FX = MAXX ( FILTER ( {p}Q, [@i] = 0 ), [@x] )",
        f"VAR {p}LX = MAXX ( FILTER ( {p}Q, [@i] = {p}N - 1 ), [@x] )",
    ]
    for k in range(len(ms)):
        out += [
            f"VAR {p}FY{k} = MAXX ( FILTER ( {p}Q, [@i] = 0 ), [@y{k}] )",
            f"VAR {p}LY{k} = MAXX ( FILTER ( {p}Q, [@i] = {p}N - 1 ), [@y{k}] )",
            f'VAR {p}Path{k} = "M" & {F(f"{p}FX")} & "," & {F(f"{p}FY{k}")} & CONCATENATEX ( FILTER ( {p}Q, NOT ISBLANK ( [@nx] ) ), '
            f'IF ( [@i] = 0, " L", " Q" & {F("[@x]")} & "," & {F(f"[@y{k}]")} & " " ) & {F("( [@x] + [@nx] ) / 2")} & "," & {F(f"( [@y{k}] + [@ny{k}] ) / 2")}, '
            f'"", [@i], ASC ) & " L" & {F(f"{p}LX")} & "," & {F(f"{p}LY{k}")}',
        ]
    out.append(f'VAR {p}Area = {p}Path0 & " L" & {F(f"{p}LX")} & ",{y0 + h + 8} L" & {F(f"{p}FX")} & ",{y0 + h + 8} Z"')
    return out


def delta_vars(p, cur, py, mode, invert=False, suffix="vs PY"):
    """VARs {p}D (change), {p}C (colour), {p}S (label) and {p}A (triangle path). mode: pct | pts | days."""
    change = {"pct": f"DIVIDE ( {cur} - {py}, ABS ( {py} ) )", "pts": f"( {cur} - {py} ) * 100", "days": f"{cur} - {py}"}[mode]
    label = {"pct": f'FORMAT ( ABS ( {p}D ), "0.0%", "en-US" ) & " {suffix}"', "pts": f'FORMAT ( ABS ( {p}D ), "0.0", "en-US" ) & " pts {suffix}"',
             "days": f'FORMAT ( ABS ( {p}D ), "0", "en-US" ) & "d {suffix}"'}[mode]
    good, bad = (BAD, GOOD) if invert else (GOOD, BAD)
    return [f"VAR {p}D = IF ( NOT ISBLANK ( {py} ), {change} )", f'VAR {p}C = IF ( {p}D >= 0, "{good}", "{bad}" )',
            f"VAR {p}S = {label}", f'VAR {p}A = IF ( {p}D >= 0, "{UP}", "{DOWN}" )']


def delta(p, x, y, size=9.5):
    """Triangle + label at baseline y, hidden when there is nothing to compare with."""
    return X(f"IF ( ISBLANK ( {p}D ), \"\", " + cat(
        f"<path transform='translate({x},{y - 7.5})' d='", X(f"{p}A"), "' fill='", X(f"{p}C"), "'/>",
        text(x + 13, y, X(f"{p}S"), size, X(f"{p}C"), 600)) + " )")


def pill(p, x, y, w):
    return X(f"IF ( ISBLANK ( {p}D ), \"\", " + cat(
        f"<g transform='translate({x},{y})'><rect width='{w}' height='20' rx='10' fill='", X(f"{p}C"), "' fill-opacity='0.13'/>",
        "<path transform='translate(9,6.5)' d='", X(f"{p}A"), "' fill='", X(f"{p}C"), "'/>",
        text(23, 14, X(f"{p}S"), 10, X(f"{p}C"), 600), "</g>") + " )")


def dax(vars_, ret):
    return "\n".join(vars_) + "\nRETURN\n    " + ret


def glow_line(path, stroke, width=2.5, blur_opacity=0.6):
    return cat("<path d='", X(path), f"' fill='none' stroke='{stroke}' stroke-width='{width + 2}' stroke-linecap='round' opacity='{blur_opacity}' filter='url(#gl)'/>",
               "<path d='", X(path), f"' fill='none' stroke='{stroke}' stroke-width='{width}' stroke-linecap='round' stroke-linejoin='round'/>")


SVG = "7. SVG visuals"
svg_measures = []


def add(name, vars_, ret, desc):
    svg_measures.append(measure(name, dax(vars_, ret), None, SVG, desc, category="ImageUrl"))


# ---- header subtitle (520 x 18)
add("SVG Header", [
    "VAR _first = CALCULATE ( MIN ( GL[Month] ) )",
    'VAR _fy = SELECTEDVALUE ( \'Date\'[Fiscal Year], "All years" )',
    'VAR _txt = "Meridian Supply Co.   ·   " & _fy & "   ·   " & FORMAT ( _first, "MMM yyyy", "en-US" ) & " to " & FORMAT ( [Period End], "MMM yyyy", "en-US" ) & "   ·   demo data"',
], svg(520, 18, text(0, 13, X("_txt"), 11.5, MUTED)), "Header subtitle that follows the fiscal year selection.")

# ---- hero / focus card with glow area chart (420 x 200). Shows revenue, or the P&L line clicked in a Deneb chart
v = ["VAR _rev = [Focus Value]", "VAR _bud = [Focus Budget]", "VAR _py = [Focus PY]",
     "VAR _sel = HASONEVALUE ( 'PnL Lines'[Line Order] )",
     f"VAR _cost = _sel && SELECTEDVALUE ( 'PnL Lines'[Line Order] ) IN {COST_LINES}",
     "VAR _name = IF ( _sel, UPPER ( SUBSTITUTE ( SELECTEDVALUE ( 'PnL Lines'[Line Name] ), \"&\", \"&amp;\" ) ), \"NET REVENUE\" )"]
for p, base, suffix in (("_a", "_py", "vs PY"), ("_b", "_bud", "vs budget")):
    v += [f"VAR {p}D = IF ( NOT ISBLANK ( {base} ), DIVIDE ( _rev - {base}, ABS ( {base} ) ) )",
          f'VAR {p}C = IF ( ( {p}D >= 0 ) <> _cost, "{GOOD}", "{BAD}" )',
          f'VAR {p}S = FORMAT ( ABS ( {p}D ), "0.0%", "en-US" ) & " {suffix}"', f'VAR {p}A = IF ( {p}D >= 0, "{UP}", "{DOWN}" )']
v += series("_s", ["[Focus Value]", "[Focus Budget]"], 20, 122, 380, 50)
v.append("VAR _months = CONCATENATEX ( _sQ, " + cat("<text x='", F("[@x]"), f"' y='194' {FONT} font-size='8' text-anchor='middle' fill='{FAINT}'>",
                                                   X("LEFT ( FORMAT ( 'Date'[Month Start], \"MMM\", \"en-US\" ), 1 )"), "</text>") + ', "" )')
add("SVG Revenue Hero", v, svg(
    420, 200,
    text(56, 34, X("_name"), 10, MUTED, 600, extra="letter-spacing='1.1'"),
    X('IF ( _sel, ' + text(400, 34, "selected line", 8.5, BLUE2, 400, "end") + ', "" )'),
    text(20, 84, money("_rev"), 36, INK, 600, extra="letter-spacing='-0.5'"),
    pill("_a", 20, 94, 104), pill("_b", 132, 94, 128),
    text(400, 62, cat("Budget  ", money("_bud")), 10, MUTED, 400, "end"),
    X('IF ( ISBLANK ( _py ), "", ' + text(400, 78, cat("Prior year  ", money("_py")), 10, MUTED, 400, "end") + " )"),
    "<path d='", X("_sArea"), "' fill='url(#gA)'/>",
    "<path d='", X("_sPath1"), f"' fill='none' stroke='{MUTED}' stroke-width='1.2' stroke-dasharray='3 4' opacity='0.8'/>",
    glow_line("_sPath0", "url(#gB)", 2.6),
    "<circle cx='", F("_sLX"), "' cy='", F("_sLY0"), f"' r='8' fill='{VIOLET}' opacity='0.28'/>",
    "<circle cx='", F("_sLX"), "' cy='", F("_sLY0"), f"' r='3.4' fill='#FFFFFF'/>",
    X("_months"),
), "Headline card. Revenue by default; when a P&L line is clicked in the bridge or OpEx chart it shows that line against prior year and budget.")


# ---- KPI tiles (188 x 94)
def tile(name, cur, mode, value, colour, invert=False):
    v = [f"VAR _cur = [{cur}]", f"VAR _py = [{cur} PY]"] + delta_vars("_a", "_cur", "_py", mode, invert) + series("_s", [f"[{cur}]"], 108, 44, 62, 26)
    add(name, v, svg(
        188, 94,
        glow_line("_sPath0", colour, 2, 0.5),
        "<circle cx='", F("_sLX"), "' cy='", F("_sLY0"), f"' r='2.6' fill='#FFFFFF'/>",
        text(14, 66, value, 22, INK, 600, extra="letter-spacing='-0.3'"),
        delta("_a", 14, 84, 9.5), blur=3,
    ), f"KPI tile for {cur}: value, change on prior year and monthly trend.")


tile("SVG Tile Gross Margin", "Gross Margin", "pts", X('FORMAT ( _cur, "0.0%", "en-US" )'), BLUE)
tile("SVG Tile EBITDA Margin", "EBITDA Margin", "pts", X('FORMAT ( _cur, "0.0%", "en-US" )'), VIOLET)
tile("SVG Tile Net Income", "Net Income", "pct", money("_cur"), GOOD)
tile("SVG Tile OpEx Ratio", "OpEx Ratio", "pts", X('FORMAT ( _cur, "0.0%", "en-US" )'), ORANGE, invert=True)

# ---- budget attainment ring + progress rows (352 x 200)
C = 2 * 3.14159265 * 54
v = ["VAR _att = [EBITDA Attainment]", f"VAR _dash = MAX ( MIN ( _att, 1 ), 0 ) * {C:.2f}"]
rows = []
for i, (label, m) in enumerate((("Revenue", "Revenue"), ("Gross profit", "Gross Profit"), ("Net income", "Net Income"))):
    y = 62 + 42 * i
    v += [f"VAR _r{i} = [{m} Attainment]",
          f'VAR _c{i} = SWITCH ( TRUE (), _r{i} >= 0.995, "url(#gG)", _r{i} >= 0.95, "url(#gB)", "url(#gO)" )',
          f"VAR _w{i} = 148 * MAX ( MIN ( _r{i} / 1.2, 1 ), 0.02 )"]
    rows += [
        text(190, y, label, 10, SOFT), text(338, y, X(f'FORMAT ( _r{i}, "0.0%", "en-US" )'), 10.5, INK, 600, "end"),
        f"<rect x='190' y='{y + 8}' width='148' height='5' rx='2.5' fill='#FFFFFF' fill-opacity='0.08'/>",
        f"<rect x='190' y='{y + 8}' width='", F(f"_w{i}"), "' height='5' rx='2.5' fill='", X(f"_c{i}"), "'/>",
        f"<rect x='{190 + 148 / 1.2 - 0.75:.1f}' y='{y + 5}' width='1.5' height='11' rx='0.75' fill='#FFFFFF' fill-opacity='0.55'/>",
        text(190, y + 25, cat(money(f"[{m}]"), " of ", money(f"[{m} Budget]")), 8.5, FAINT),
    ]
add("SVG Budget Ring", v, svg(
    352, 200,
    "<circle cx='96' cy='116' r='54' fill='none' stroke='#FFFFFF' stroke-opacity='0.07' stroke-width='12'/>",
    "<circle cx='96' cy='116' r='54' fill='none' stroke='url(#gO)' stroke-width='14' stroke-linecap='round' opacity='0.55' filter='url(#gl)' transform='rotate(-90 96 116)' stroke-dasharray='", F("_dash"), " 400'/>",
    "<circle cx='96' cy='116' r='54' fill='none' stroke='url(#gO)' stroke-width='12' stroke-linecap='round' transform='rotate(-90 96 116)' stroke-dasharray='", F("_dash"), " 400'/>",
    text(96, 121, X('FORMAT ( _att, "0.0%", "en-US" )'), 25, INK, 600, "middle", "letter-spacing='-0.4'"),
    text(96, 138, "EBITDA vs budget", 8.5, MUTED, 400, "middle"),
    *rows, blur=6,
), "Ring: EBITDA against budget. Rows: revenue, gross profit and net income against budget, tick marks 100%.")

# ---- OpEx total under the Deneb variance chart (296 x 26). The bridge and the OpEx bars themselves are Deneb specs in _scripts/deneb
add("SVG OpEx Total", ["VAR _tv = [OpEx Variance %]", "VAR _ta = [OpEx Variance]", f'VAR _tc = IF ( _tv > 0, "{ORANGE2}", "{GOOD}" )'], svg(
    296, 26,
    text(16, 15, "Total OpEx", 9.5, MUTED),
    text(280, 15, cat(X('FORMAT ( _tv, "+0.0%;-0.0%", "en-US" )'), "  ·  ", money("ABS ( _ta )", 2), X('IF ( _ta > 0, " over", " under" )')),
         9.5, X("_tc"), 600, "end"),
), "Total operating expenses against budget.")

# ---- cash panel with monthly free cash flow capsules (304 x 210)
bar = cat(
    "<rect x='", F("_cx - 6"), "' y='", F("IF ( [@v] >= 0, 150 - _h, 150 )"), "' width='12' height='", F("_h"), "' rx='6' fill='",
    X('IF ( [@v] >= 0, "url(#gBv)", "url(#gOv)" )'), "' fill-opacity='", X('IF ( _i = _fN - 1, "1", "0.6" )'), "'/>",
    "<text x='", F("_cx"), f"' y='197' {FONT} font-size='8' text-anchor='middle' fill='{FAINT}'>",
    X("LEFT ( FORMAT ( 'Date'[Month Start], \"MMM\", \"en-US\" ), 1 )"), "</text>")
v = ["VAR _cash = [Cash Balance]", "VAR _chg = [Cash Change]", "VAR _cover = [Cash Cover Months]",
     f'VAR _cc = IF ( _chg >= 0, "{GOOD}", "{BAD}" )',
     "VAR _fT = ADDCOLUMNS ( FILTER ( VALUES ( 'Date'[Month Start] ), NOT ISBLANK ( [Free Cash Flow] ) ), \"@v\", [Free Cash Flow] )",
     "VAR _fN = COUNTROWS ( _fT )", "VAR _fF = MINX ( _fT, 'Date'[Month Start] )", "VAR _fL = MAXX ( _fT, 'Date'[Month Start] )",
     "VAR _fM = MAXX ( _fT, ABS ( [@v] ) )", "VAR _step = DIVIDE ( 268, _fN )",
     "VAR _last = MAXX ( FILTER ( _fT, 'Date'[Month Start] = _fL ), [@v] )",
     "VAR _bars = CONCATENATEX ( _fT, VAR _i = DATEDIFF ( _fF, 'Date'[Month Start], MONTH ) VAR _cx = 18 + _step * ( _i + 0.5 ) "
     f"VAR _h = MAX ( 28 * DIVIDE ( ABS ( [@v] ), _fM ), 4 ) RETURN {bar}, \"\" )"]
add("SVG Cash", v, svg(
    304, 210,
    text(18, 76, money("_cash"), 27, INK, 600, extra="letter-spacing='-0.4'"),
    X('IF ( ISBLANK ( _chg ), "", ' + cat(
        "<path transform='translate(18,85.5)' d='", X(f'IF ( _chg >= 0, "{UP}", "{DOWN}" )'), "' fill='", X("_cc"), "'/>",
        text(31, 93, cat(money("ABS ( _chg )"), " since period start"), 9.5, X("_cc"), 600)) + " )"),
    text(286, 64, cat(X('FORMAT ( _cover, "0.0", "en-US" )'), " mo"), 15, INK, 600, "end"),
    text(286, 77, "cost cover", 8.5, MUTED, 400, "end"),
    text(18, 114, "Free cash flow by month", 8.5, MUTED),
    text(286, 114, cat(X('FORMAT ( _fL, "MMM", "en-US" )'), "  ", X('IF ( _last < 0, "-", "" )'), money("ABS ( _last )", 2)), 9, X(f'IF ( _last >= 0, "{BLUE2}", "{ORANGE2}" )'), 600, "end"),
    "<line x1='18' x2='286' y1='150' y2='150' stroke='#FFFFFF' stroke-opacity='0.14'/>",
    X("_bars"),
), "Cash at period end, months of operating cost it covers, and free cash flow for each month.")

# ---- cash conversion cycle rings (390 x 198)
RC = 2 * 3.14159265 * 28
v, parts = [], []
for i, (code, word, m, colour, invert) in enumerate((("DSO", "receivables", "DSO", BLUE, True), ("DIO", "inventory", "DIO", VIOLET, True),
                                                      ("DPO", "payables", "DPO", GOOD, False))):
    cx = 56 + 92 * i
    v += [f"VAR _v{i} = [{m}]", f"VAR _p{i} = [{m} PY]", f"VAR _d{i} = MAX ( MIN ( DIVIDE ( _v{i}, 120 ), 1 ), 0 ) * {RC:.2f}"]
    v += delta_vars(f"_x{i}", f"_v{i}", f"_p{i}", "days", invert)
    parts += [
        f"<circle cx='{cx}' cy='98' r='28' fill='none' stroke='#FFFFFF' stroke-opacity='0.07' stroke-width='7'/>",
        f"<circle cx='{cx}' cy='98' r='28' fill='none' stroke='{colour}' stroke-width='8' stroke-linecap='round' opacity='0.5' filter='url(#gl)' transform='rotate(-90 {cx} 98)' stroke-dasharray='",
        F(f"_d{i}"), " 200'/>",
        f"<circle cx='{cx}' cy='98' r='28' fill='none' stroke='{colour}' stroke-width='7' stroke-linecap='round' transform='rotate(-90 {cx} 98)' stroke-dasharray='",
        F(f"_d{i}"), " 200'/>",
        text(cx, 104, X(f'FORMAT ( _v{i}, "0", "en-US" )'), 17, INK, 600, "middle"),
        text(cx, 146, code, 10, INK, 600, "middle"), text(cx, 159, word, 8.5, MUTED, 400, "middle"),
        delta(f"_x{i}", cx - 30, 177, 8.5),
    ]
for x, sign in ((102, "+"), (194, "-"), (282, "=")):
    parts.append(text(x, 104, sign, 17, FAINT, 400, "middle"))
v += ["VAR _ccc = [Cash Conversion Cycle]", "VAR _cpy = [Cash Conversion Cycle PY]"] + delta_vars("_z", "_ccc", "_cpy", "days", True)
parts += [text(336, 108, X('FORMAT ( _ccc, "0", "en-US" )'), 36, INK, 600, "middle", "letter-spacing='-0.6'"),
          text(336, 124, "days", 9.5, MUTED, 400, "middle"), text(336, 146, "Cash cycle", 10, INK, 600, "middle"),
          text(336, 159, "DSO + DIO - DPO", 8.5, MUTED, 400, "middle"), delta("_z", 306, 177, 8.5)]
add("SVG Cash Cycle", v, svg(390, 198, *parts, blur=4), "Days sales, inventory and payables outstanding, and the cash conversion cycle they add up to.")

# ---- receivables aging (368 x 198)
AGE_COLORS = [BLUE, BLUE2, "#FFD39A", ORANGE, BAD]
AGE_LABELS = ["Current", "1-30 d", "31-60 d", "61-90 d", "90+ d"]
v = ["VAR _ar = [AR Balance]", "VAR _od = [AR Overdue %]", "VAR _n90 = [Invoices 90+]"]
parts = [text(18, 76, money("_ar"), 25, INK, 600, extra="letter-spacing='-0.4'"),
         text(350, 64, X('FORMAT ( _od, "0.0%", "en-US" )'), 15, BAD, 600, "end"), text(350, 77, "overdue", 8.5, MUTED, 400, "end")]
x_prev = "18"
for i, (label, _, _) in enumerate(AGING):
    v += [f"VAR _a{i} = [AR {label}] + 0", f"VAR _w{i} = MAX ( 316 * DIVIDE ( _a{i}, _ar ), 4 )", f"VAR _x{i} = {x_prev}"]
    x_prev = f"_x{i} + _w{i} + 4"
    lx = 18 + 68 * i
    parts += [
        "<rect x='", F(f"_x{i}"), "' y='92' width='", F(f"_w{i}"), f"' height='14' rx='5' fill='{AGE_COLORS[i]}'/>",
        f"<circle cx='{lx + 4}' cy='125' r='3.5' fill='{AGE_COLORS[i]}'/>", text(lx + 12, 128, AGE_LABELS[i], 8.5, MUTED),
        text(lx, 147, money(f"_a{i}", 2), 12, INK, 600), text(lx, 160, X(f'FORMAT ( DIVIDE ( _a{i}, _ar ), "0.0%", "en-US" )'), 8.5, FAINT),
    ]
parts += [f"<circle cx='22' cy='180' r='3' fill='{BAD}'/>",
          text(31, 183.5, cat(X('FORMAT ( _n90, "0", "en-US" )'), " invoices are more than 90 days overdue"), 9, MUTED)]
add("SVG AR Aging", v, svg(368, 198, *parts), "Open receivables at period end, split by days past due.")

# ---- in-table SVGs
add("SVG Dept Bar", [
    "VAR _v = [OpEx Variance %]",
    "VAR _m = MAX ( MAXX ( ALLSELECTED ( Departments[Department] ), ABS ( [OpEx Variance %] ) ), 0.02 )",
    "VAR _w = MAX ( 44 * DIVIDE ( ABS ( _v ), _m ), 2 )",
], svg(96, 16,
       "<line x1='48' x2='48' y1='1' y2='15' stroke='#FFFFFF' stroke-opacity='0.25'/>",
       "<rect x='", F("IF ( _v >= 0, 48, 48 - _w )"), "' y='4' width='", F("_w"), "' height='8' rx='4' fill='", X('IF ( _v >= 0, "url(#gO)", "url(#gG)" )'), "'/>"),
    "Department operating expense against budget, as a diverging bar.")
add("SVG Overdue Bar", [
    "VAR _v = [AR Overdue]",
    "VAR _m = MAXX ( ALLSELECTED ( Receivables[Customer] ), [AR Overdue] )",
    "VAR _w = MAX ( 104 * DIVIDE ( _v, _m ), 3 )",
    'VAR _c = IF ( [Oldest Days Overdue] > 90, "url(#gO)", "url(#gB)" )',
], svg(110, 14,
       "<rect x='2' y='4' width='104' height='6' rx='3' fill='#FFFFFF' fill-opacity='0.07'/>",
       "<rect x='2' y='4' width='", F("_w"), "' height='6' rx='3' fill='", X("_c"), "'/>"),
    "Overdue amount per customer relative to the largest; orange when the oldest invoice is 90+ days late.")
add("SVG Line Bar", [
    "VAR _a = [PnL Value]", "VAR _b = [PnL Budget]",
    f"VAR _cost = SELECTEDVALUE ( 'PnL Lines'[Line Order] ) IN {COST_LINES}",
    "VAR _rel = IF ( SELECTEDVALUE ( 'PnL Lines'[Line Type] ) = \"ratio\", ( _a - _b ) * 10, DIVIDE ( _a - _b, ABS ( _b ) ) )",
    "VAR _w = MAX ( 46 * MIN ( DIVIDE ( ABS ( _rel ), 0.16 ), 1 ), 2 )",
    'VAR _good = ( _rel > 0 ) <> _cost',
], X('IF ( NOT ISBLANK ( _a ) && NOT ISBLANK ( _b ), ' + svg(
    100, 16,
    "<line x1='50' x2='50' y1='1' y2='15' stroke='#FFFFFF' stroke-opacity='0.25'/>",
    "<rect x='", F("IF ( _rel >= 0, 50, 50 - _w )"), "' y='4' width='", F("_w"), "' height='8' rx='4' fill='", X('IF ( _good, "url(#gG)", "url(#gO)" )'), "'/>") + " )"),
    "Variance to budget for a statement line; green is favourable.")
v = series("_s", ["[PnL Value]"], 4, 3, 92, 12)
add("SVG Line Trend", v, X('IF ( _sN > 1, ' + svg(
    100, 18, "<path d='", X("_sPath0"), f"' fill='none' stroke='{BLUE2}' stroke-width='1.6' stroke-linecap='round'/>",
    "<circle cx='", F("_sLX"), "' cy='", F("_sLY0"), "' r='2' fill='#FFFFFF'/>") + " )"), "Monthly trend of a statement line.")

measures += svg_measures
build(PROJECT, "FinanceCFO", tables, relationships, measures, date_range=((2024, 1, 1), (2026, 9, 30)))
