"""Semantic model spec for 01_Sales-Analytics."""
from pathlib import Path

from pbi_model import build, col, measure

PROJECT = Path(__file__).resolve().parents[1] / "01_Sales-Analytics"

tables = {
    "Orders": ("orders.csv", [
        col("Order ID", "int", "OrderID"), col("Order Date", "date", "OrderDate"),
        col("CustomerKey", "int", hidden=True), col("ProductKey", "int", hidden=True), col("RepKey", "int", hidden=True),
        col("Channel", "text"), col("Quantity", "int", hidden=True), col("Unit Price", "money", "UnitPrice", hidden=True),
        col("Discount Pct", "number", "DiscountPct", hidden=True), col("Revenue Amount", "money", "Revenue", hidden=True),
        col("Cost Amount", "money", "Cost", hidden=True),
    ]),
    "Customers": ("customers.csv", [
        col("CustomerKey", "int", hidden=True), col("Customer", "text"), col("Segment", "text"), col("Industry", "text"),
        col("Country", "text", category="Country"), col("RegionKey", "int", hidden=True),
        col("First Order Date", "date", "FirstOrderDate"),
    ]),
    "Products": ("products.csv", [
        col("ProductKey", "int", hidden=True), col("SKU", "text"), col("Product", "text"), col("Category", "text"),
        col("Subcategory", "text"), col("List Price", "money", "ListPrice", fmt="#,##0.00"),
        col("Unit Cost", "money", "UnitCost", fmt="#,##0.00"),
    ]),
    "Sales Reps": ("sales_reps.csv", [
        col("RepKey", "int", hidden=True), col("Sales Rep", "text", "SalesRep"), col("RegionKey", "int", hidden=True),
        col("Hire Date", "date", "HireDate"),
    ]),
    "Regions": ("regions.csv", [
        col("RegionKey", "int", hidden=True), col("Region", "text"), col("Region Manager", "text", "RegionManager"),
    ]),
    "Targets": ("targets.csv", [
        col("Month", "date", hidden=True), col("RegionKey", "int", hidden=True),
        col("Target Amount", "money", "TargetRevenue", hidden=True),
    ]),
}

relationships = [
    ("Orders.Order Date", "Date.Date"), ("Orders.CustomerKey", "Customers.CustomerKey"),
    ("Orders.ProductKey", "Products.ProductKey"), ("Orders.RepKey", "Sales Reps.RepKey"),
    ("Customers.RegionKey", "Regions.RegionKey"), ("Targets.RegionKey", "Regions.RegionKey"),
    ("Targets.Month", "Date.Date"),
]

# Prior-year measures stop at the last order date shifted back a year, so a partial
# current year is compared with the same partial window, not a full prior year.
PY = """
VAR _LastData = CALCULATE ( MAX ( Orders[Order Date] ), REMOVEFILTERS () )
RETURN
    CALCULATE (
        {expr},
        SAMEPERIODLASTYEAR ( 'Date'[Date] ),
        'Date'[Date] <= EDATE ( _LastData, -12 )
    )
"""

measures = [
    measure("Revenue", "SUM ( Orders[Revenue Amount] )", "$#,##0", "1. Revenue"),
    measure("Revenue PY", PY.format(expr="[Revenue]"), "$#,##0", "1. Revenue",
            "Revenue for the same period one year earlier, limited to dates that have data this year."),
    measure("Revenue YoY %", "DIVIDE ( [Revenue] - [Revenue PY], [Revenue PY] )", "+0.0%;-0.0%;0.0%", "1. Revenue"),
    measure("Revenue Target", "SUM ( Targets[Target Amount] )", "$#,##0", "2. Target"),
    measure("Revenue vs Target", "[Revenue] - [Revenue Target]", "+$#,##0;-$#,##0;$0", "2. Target"),
    measure("Target Attainment %", "DIVIDE ( [Revenue], [Revenue Target] )", "0.0%", "2. Target"),
    measure("Revenue vs Target %", "DIVIDE ( [Revenue] - [Revenue Target], [Revenue Target] )", "+0.0%;-0.0%;0.0%", "2. Target"),
    measure("Cost", "SUM ( Orders[Cost Amount] )", "$#,##0", "3. Margin"),
    measure("Gross Profit", "[Revenue] - [Cost]", "$#,##0", "3. Margin"),
    measure("Gross Margin %", "DIVIDE ( [Gross Profit], [Revenue] )", "0.0%", "3. Margin"),
    measure("Gross Margin % PY", PY.format(expr="[Gross Margin %]"), "0.0%", "3. Margin"),
    measure("Gross Margin Change (pts)", "( [Gross Margin %] - [Gross Margin % PY] ) * 100", "+0.0 pts;-0.0 pts;0.0 pts", "3. Margin"),
    measure("List Sales", "SUMX ( Orders, Orders[Quantity] * Orders[Unit Price] )", "$#,##0", "4. Discount"),
    measure("Discount Amount", "[List Sales] - [Revenue]", "$#,##0", "4. Discount"),
    measure("Discount %", "DIVIDE ( [Discount Amount], [List Sales] )", "0.0%", "4. Discount"),
    measure("Orders", "DISTINCTCOUNT ( Orders[Order ID] )", "#,##0", "5. Volume"),
    measure("Orders PY", PY.format(expr="[Orders]"), "#,##0", "5. Volume"),
    measure("Orders YoY %", "DIVIDE ( [Orders] - [Orders PY], [Orders PY] )", "+0.0%;-0.0%;0.0%", "5. Volume"),
    measure("Units", "SUM ( Orders[Quantity] )", "#,##0", "5. Volume"),
    measure("Avg Order Value", "DIVIDE ( [Revenue], [Orders] )", "$#,##0", "5. Volume"),
    measure("Avg Order Value PY", PY.format(expr="[Avg Order Value]"), "$#,##0", "5. Volume"),
    measure("Avg Order Value YoY %", "DIVIDE ( [Avg Order Value] - [Avg Order Value PY], [Avg Order Value PY] )",
            "+0.0%;-0.0%;0.0%", "5. Volume"),
    measure("Active Customers", "DISTINCTCOUNT ( Orders[CustomerKey] )", "#,##0", "6. Customers"),
    measure("New Customers", """
VAR _From = MIN ( 'Date'[Date] )
VAR _To = MAX ( 'Date'[Date] )
RETURN
    COUNTROWS (
        FILTER ( Customers, Customers[First Order Date] >= _From && Customers[First Order Date] <= _To )
    )
""", "#,##0", "6. Customers"),
    measure("Revenue per Customer", "DIVIDE ( [Revenue], [Active Customers] )", "$#,##0", "6. Customers"),
    measure("Data As Of", """
"Data as of " & FORMAT ( CALCULATE ( MAX ( Orders[Order Date] ), REMOVEFILTERS () ), "d mmm yyyy" )
""", None, "7. Labels"),
    measure("Revenue YoY Color", 'IF ( [Revenue YoY %] >= 0, "#3CC08A", "#F0788A" )', None, "8. Formatting"),
    measure("Target Color", 'IF ( [Revenue vs Target] >= 0, "#3CC08A", "#F0788A" )', None, "8. Formatting"),
    measure("Margin Color", 'IF ( [Gross Margin Change (pts)] >= 0, "#3CC08A", "#F0788A" )', None, "8. Formatting"),
    measure("Orders YoY Color", 'IF ( [Orders YoY %] >= 0, "#3CC08A", "#F0788A" )', None, "8. Formatting"),
    measure("AOV YoY Color", 'IF ( [Avg Order Value YoY %] >= 0, "#3CC08A", "#F0788A" )', None, "8. Formatting"),
    measure("Revenue YoY Label", 'IF ( [Revenue YoY %] >= 0, "▲ ", "▼ " ) & FORMAT ( ABS ( [Revenue YoY %] ), "0.0%" ) & " vs PY"', None, "7. Labels"),
    measure("Target Label", 'IF ( [Revenue vs Target] >= 0, "▲ ", "▼ " ) & FORMAT ( ABS ( [Revenue vs Target %] ), "0.0%" ) & " vs target"', None, "7. Labels"),
    measure("Margin Label", 'IF ( [Gross Margin Change (pts)] >= 0, "▲ ", "▼ " ) & FORMAT ( ABS ( [Gross Margin Change (pts)] ), "0.0" ) & " pts vs PY"', None, "7. Labels"),
    measure("AOV YoY Label", 'IF ( [Avg Order Value YoY %] >= 0, "▲ ", "▼ " ) & FORMAT ( ABS ( [Avg Order Value YoY %] ), "0.0%" ) & " vs PY"', None, "7. Labels"),
    measure("YoY", 'IF ( ISBLANK ( [Revenue PY] ) || ISBLANK ( [Revenue] ), BLANK (), IF ( [Revenue YoY %] >= 0, "▲ ", "▼ " ) & FORMAT ( ABS ( [Revenue YoY %] ), "0.0%" ) )', None, "7. Labels"),
    measure("Attainment Color", 'IF ( [Target Attainment %] >= 0.95, "#5E6AD2", "#F4A0AE" )', None, "8. Formatting"),
]

GOOD, BAD, MUTED = "#3CC08A", "#F0788A", "#8A8FA3"


def yoy_set(base, fmt, folder, higher_is_better=True, points=False):
    """PY, change, triangle label and colour measures for one base measure."""
    up, down = (GOOD, BAD) if higher_is_better else (BAD, GOOD)
    change = f"( [{base}] - [{base} PY] ) * 100" if points else f"DIVIDE ( [{base}] - [{base} PY], [{base} PY] )"
    text = 'FORMAT ( ABS ( _d ), "0.0" ) & " pts vs PY"' if points else 'FORMAT ( ABS ( _d ), "0.0%" ) & " vs PY"'
    return [
        measure(f"{base} PY", PY.format(expr=f"[{base}]"), fmt, folder),
        measure(f"{base} Label", f"""
VAR _d = {change}
RETURN
    IF ( _d >= 0, "▲ ", "▼ " ) & {text}
""", None, "7. Labels"),
        measure(f"{base} Color", f"""
VAR _d = {change}
RETURN
    IF ( _d >= 0, "{up}", "{down}" )
""", None, "8. Formatting"),
    ]


measures += yoy_set("Gross Profit", "$#,##0", "3. Margin")
measures += yoy_set("Discount %", "0.0%", "4. Discount", higher_is_better=False, points=True)
measures += yoy_set("Units", "#,##0", "5. Volume")
measures += yoy_set("Active Customers", "#,##0", "6. Customers")
measures += yoy_set("Revenue per Customer", "$#,##0", "6. Customers")
measures += [
    measure("Orders Label", 'IF ( [Orders YoY %] >= 0, "▲ ", "▼ " ) & FORMAT ( ABS ( [Orders YoY %] ), "0.0%" ) & " vs PY"', None, "7. Labels"),
    measure("New Customers Label", 'FORMAT ( DIVIDE ( [New Customers], [Active Customers] ), "0.0%" ) & " of active customers"', None, "7. Labels"),
    measure("Neutral Color", f'"{MUTED}"', None, "8. Formatting"),
    measure("Margin Bar Color", """
VAR _All = CALCULATE ( [Gross Margin %], ALLSELECTED ( Products ) )
RETURN
    IF ( [Gross Margin %] < _All, "#F4A0AE", "#5E6AD2" )
""", None, "8. Formatting"),
    measure("Revenue YoY Sort", "[Revenue YoY %]", "+0.0%;-0.0%;0.0%", "1. Revenue",
            "Numeric year-over-year change, used to sort tables by decline."),
    measure("Order Lines", "COUNTROWS ( Orders )", "#,##0", "5. Volume"),
]

measures += [
    measure("Orders per Customer", "DIVIDE ( [Orders], [Active Customers] )", "0.0", "6. Customers"),
    measure("Orders per Customer PY", "DIVIDE ( [Orders PY], [Active Customers PY] )", "0.0", "6. Customers"),
    measure("Orders per Customer Label", """
VAR _d = DIVIDE ( [Orders per Customer] - [Orders per Customer PY], [Orders per Customer PY] )
RETURN
    IF ( _d >= 0, "▲ ", "▼ " ) & FORMAT ( ABS ( _d ), "0.0%" ) & " vs PY"
""", None, "7. Labels"),
    measure("Orders per Customer Color", f'IF ( [Orders per Customer] >= [Orders per Customer PY], "{GOOD}", "{BAD}" )', None, "8. Formatting"),
]

build(PROJECT, "SalesAnalytics", tables, relationships, measures, date_range=((2024, 1, 1), (2026, 12, 31)))
