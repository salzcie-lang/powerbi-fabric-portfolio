"""Semantic model spec for 03_Real-Estate."""
from pathlib import Path

from pbi_model import build, col, measure

PROJECT = Path(__file__).resolve().parents[1] / "03_Real-Estate"
GOOD, BAD, MUTED, ACCENT, INK = "#3E9B6E", "#D9735B", "#8C8676", "#2F6B4F", "#1F2A24"

tables = {
    "Properties": ("properties.csv", [
        col("PropertyKey", "int", hidden=True), col("Property", "text"), col("Property Type", "text", "PropertyType", hidden=True),
        col("City", "text", category="City"), col("State", "text"), col("Year Built", "int", "YearBuilt"),
        col("Acquired Date", "date", "AcquiredDate"), col("Property Manager", "text", "PropertyManager"),
        col("Current Value", "money", "CurrentValue", hidden=True), col("Purchase Price", "money", "PurchasePrice", hidden=True),
        col("Latitude", "number", category="Latitude", fmt="0.0000"), col("Longitude", "number", category="Longitude", fmt="0.0000"),
        col("Photo", "text", category="ImageUrl"), col("Photo Large", "text", "PhotoLarge", category="ImageUrl", hidden=True),
    ]),
    "Property Types": ("property_types.csv", [
        col("Property Type", "text", "PropertyType", sort_by="Type Order"), col("Picture", "text", category="ImageUrl"),
        col("Type Order", "int", "TypeOrder", hidden=True),
    ]),
    "Units": ("units.csv", [
        col("UnitKey", "int", hidden=True), col("PropertyKey", "int", hidden=True), col("Unit Number", "text", "UnitNumber"),
        col("Unit Type", "text", "UnitType"), col("Square Feet", "int", "SquareFeet", hidden=True),
        col("Market Rent", "money", "MarketRent", hidden=True),
    ]),
    "Leases": ("leases.csv", [
        col("LeaseKey", "int", hidden=True), col("UnitKey", "int", hidden=True), col("Tenant", "text"),
        col("Start Date", "date", "StartDate"), col("End Date", "date", "EndDate"),
        col("Monthly Rent", "money", "MonthlyRent", hidden=True),
    ]),
    "Rent Payments": ("rent_payments.csv", [
        col("PaymentKey", "int", hidden=True), col("UnitKey", "int", hidden=True), col("Due Date", "date", "DueDate"),
        col("Amount Due", "money", "AmountDue", hidden=True), col("Amount Paid", "money", "AmountPaid", hidden=True),
        col("Payment Status", "text", "PaymentStatus"),
    ]),
    "Operating Expenses": ("operating_expenses.csv", [
        col("PropertyKey", "int", hidden=True), col("Month", "date", hidden=True),
        col("Expense Category", "text", "ExpenseCategory"), col("Amount", "money", hidden=True),
    ]),
    "Maintenance Requests": ("maintenance_requests.csv", [
        col("RequestKey", "int", hidden=True), col("UnitKey", "int", hidden=True), col("Opened Date", "date", "OpenedDate"),
        col("Completed Date", "date", "CompletedDate"), col("Category", "text"), col("Priority", "text"),
        col("Status", "text"), col("Cost", "money", hidden=True),
    ]),
}

relationships = [
    ("Properties.Property Type", "Property Types.Property Type"), ("Units.PropertyKey", "Properties.PropertyKey"),
    ("Leases.UnitKey", "Units.UnitKey"), ("Rent Payments.UnitKey", "Units.UnitKey"), ("Rent Payments.Due Date", "Date.Date"),
    ("Operating Expenses.PropertyKey", "Properties.PropertyKey"), ("Operating Expenses.Month", "Date.Date"),
    ("Maintenance Requests.UnitKey", "Units.UnitKey"), ("Maintenance Requests.Opened Date", "Date.Date"),
]

PY = """
VAR _Last = [As Of Date]
RETURN
    CALCULATE (
        {expr},
        SAMEPERIODLASTYEAR ( 'Date'[Date] ),
        'Date'[Date] <= EDATE ( _Last, -12 )
    )
"""
# Occupancy is a snapshot: a unit is occupied on a date if a lease covers that date.
OCCUPIED = """
VAR _d = {date}
RETURN
    IF (
        MIN ( 'Date'[Date] ) <= [As Of Date],
        CALCULATE ( DISTINCTCOUNT ( Leases[UnitKey] ), Leases[Start Date] <= _d, Leases[End Date] >= _d )
    )
"""


def yoy_set(base, fmt, folder, higher_is_better=True, points=False):
    """PY, triangle label and colour measures for one base measure."""
    up, down = (GOOD, BAD) if higher_is_better else (BAD, GOOD)
    change = f"( [{base}] - [{base} PY] ) * 100" if points else f"DIVIDE ( [{base}] - [{base} PY], [{base} PY] )"
    text = 'FORMAT ( ABS ( _d ), "0.0" ) & " pts vs PY"' if points else 'FORMAT ( ABS ( _d ), "0.0%" ) & " vs PY"'
    out = [] if base == "Occupancy %" else [measure(f"{base} PY", PY.format(expr=f"[{base}]"), fmt, folder)]
    return out + [
        measure(f"{base} Label", f"""
VAR _d = {change}
RETURN
    IF ( _d >= 0, "▲ ", "▼ " ) & {text}
""", None, "8. Labels"),
        measure(f"{base} Color", f"""
VAR _d = {change}
RETURN
    IF ( _d >= 0, "{up}", "{down}" )
""", None, "9. Formatting"),
    ]


BAR = (
    "\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='104' height='16'>"
    "<rect x='2' y='5' width='100' height='6' rx='3' fill='%23E8E1D3'/>"
    "<rect x='2' y='5' width='\" & _w & \"' height='6' rx='3' fill='\" & _c & \"'/></svg>\""
)

measures = [
    measure("As Of Date", "EOMONTH ( CALCULATE ( MAX ( 'Rent Payments'[Due Date] ), REMOVEFILTERS () ), 0 )", "dd mmm yyyy", "0. Base"),
    measure("Snapshot Date", "MIN ( MAX ( 'Date'[Date] ), [As Of Date] )", "dd mmm yyyy", "0. Base",
            "Last date in the selection, capped at the as-of date. Occupancy is measured on this date."),
    measure("Properties", "COUNTROWS ( 'Properties' )", "#,##0", "1. Portfolio"),
    measure("Units", "COUNTROWS ( Units )", "#,##0", "1. Portfolio"),
    measure("Portfolio Value", "SUM ( 'Properties'[Current Value] )", "$#,##0", "1. Portfolio"),
    measure("Purchase Price", "SUM ( 'Properties'[Purchase Price] )", "$#,##0", "1. Portfolio"),
    measure("Appreciation %", "DIVIDE ( [Portfolio Value] - [Purchase Price], [Purchase Price] )", "0.0%", "1. Portfolio"),
    measure("Map Latitude", "AVERAGE ( 'Properties'[Latitude] )", "0.0000", "1. Portfolio"),
    measure("Map Longitude", "AVERAGE ( 'Properties'[Longitude] )", "0.0000", "1. Portfolio"),
    measure("Occupied Units", OCCUPIED.format(date="[Snapshot Date]"), "#,##0", "2. Occupancy"),
    measure("Occupied Units PY", OCCUPIED.format(date="EDATE ( [Snapshot Date], -12 )"), "#,##0", "2. Occupancy"),
    measure("Occupancy %", "DIVIDE ( [Occupied Units], [Units] )", "0.0%", "2. Occupancy"),
    measure("Occupancy % PY", "DIVIDE ( [Occupied Units PY], [Units] )", "0.0%", "2. Occupancy"),
    measure("Vacant Units", "IF ( NOT ISBLANK ( [Occupied Units] ), [Units] - [Occupied Units] )", "#,##0", "2. Occupancy"),
    measure("Rent Roll", """
VAR _d = [Snapshot Date]
RETURN
    CALCULATE ( SUM ( Leases[Monthly Rent] ), Leases[Start Date] <= _d, Leases[End Date] >= _d )
""", "$#,##0", "2. Occupancy", "Monthly contracted rent of leases active on the snapshot date."),
    measure("Avg Rent per Unit", "DIVIDE ( [Rent Roll], [Occupied Units] )", "$#,##0", "2. Occupancy"),
    measure("Expiring Leases", """
VAR _a = [As Of Date]
RETURN
    CALCULATE (
        COUNTROWS ( Leases ),
        KEEPFILTERS ( Leases[Start Date] <= _a ),
        KEEPFILTERS ( Leases[End Date] >= _a && Leases[End Date] <= _a + 90 )
    )
""", "#,##0", "2. Occupancy", "Active leases that end within 90 days of the as-of date."),
    measure("Expiring Rent", """
VAR _a = [As Of Date]
RETURN
    CALCULATE (
        SUM ( Leases[Monthly Rent] ),
        KEEPFILTERS ( Leases[Start Date] <= _a ),
        KEEPFILTERS ( Leases[End Date] >= _a && Leases[End Date] <= _a + 90 )
    )
""", "$#,##0", "2. Occupancy"),
    measure("Rent Due", "SUM ( 'Rent Payments'[Amount Due] )", "$#,##0", "3. Collections"),
    measure("Rent Collected", "SUM ( 'Rent Payments'[Amount Paid] )", "$#,##0", "3. Collections"),
    measure("Outstanding Rent", "[Rent Due] - [Rent Collected]", "$#,##0", "3. Collections"),
    measure("Collection Rate", "DIVIDE ( [Rent Collected], [Rent Due] )", "0.0%", "3. Collections"),
    measure("Payments", "COUNTROWS ( 'Rent Payments' )", "#,##0", "3. Collections"),
    measure("Operating Expenses Total", "SUM ( 'Operating Expenses'[Amount] )", "$#,##0", "4. NOI"),
    measure("NOI", "[Rent Collected] - [Operating Expenses Total]", "$#,##0", "4. NOI", "Net operating income: rent collected less operating expenses."),
    measure("NOI Margin", "DIVIDE ( [NOI], [Rent Collected] )", "0.0%", "4. NOI"),
    measure("Requests", "COUNTROWS ( 'Maintenance Requests' )", "#,##0", "5. Maintenance"),
    measure("Open Requests", 'CALCULATE ( COUNTROWS ( \'Maintenance Requests\' ), \'Maintenance Requests\'[Status] = "Open" ) + 0', "#,##0", "5. Maintenance"),
    measure("Maintenance Cost", "SUM ( 'Maintenance Requests'[Cost] )", "$#,##0", "5. Maintenance"),
    measure("Avg Days to Complete", """
AVERAGEX (
    FILTER ( 'Maintenance Requests', NOT ISBLANK ( 'Maintenance Requests'[Completed Date] ) ),
    DATEDIFF ( 'Maintenance Requests'[Opened Date], 'Maintenance Requests'[Completed Date], DAY )
)
""", "0.0", "5. Maintenance"),
]
measures += yoy_set("Occupancy %", "0.0%", "2. Occupancy", points=True)
measures += yoy_set("Rent Collected", "$#,##0", "3. Collections")
measures += yoy_set("Collection Rate", "0.0%", "3. Collections", points=True)
measures += yoy_set("Operating Expenses Total", "$#,##0", "4. NOI", higher_is_better=False)
measures += yoy_set("NOI", "$#,##0", "4. NOI")
measures += yoy_set("NOI Margin", "0.0%", "4. NOI", points=True)
measures += yoy_set("Maintenance Cost", "$#,##0", "5. Maintenance", higher_is_better=False)
measures += yoy_set("Requests", "#,##0", "5. Maintenance", higher_is_better=False)
measures += [
    measure("Portfolio Value Label", '"▲ " & FORMAT ( [Appreciation %], "0.0%" ) & " vs cost"', None, "8. Labels"),
    measure("Units Label", '[Properties] & " properties"', None, "8. Labels"),
    measure("Vacant Units Label", '"of " & FORMAT ( [Units], "#,##0" ) & " units"', None, "8. Labels"),
    measure("Outstanding Rent Label", 'FORMAT ( DIVIDE ( [Outstanding Rent], [Rent Due] ), "0.0%" ) & " of rent due"', None, "8. Labels"),
    measure("Expiring Leases Label", 'FORMAT ( [Expiring Rent] / 1000, "$#,##0" ) & "K / mo at risk"', None, "8. Labels"),
    measure("Open Requests Label", '"of " & FORMAT ( [Requests], "#,##0" ) & " requests"', None, "8. Labels"),
    measure("Avg Rent per Unit Label", '"per occupied unit"', None, "8. Labels"),
    measure("Hero Photo", """
IF (
    HASONEVALUE ( 'Properties'[Property] ),
    SELECTEDVALUE ( 'Properties'[Photo Large] ),
    "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=1040&h=760&fit=crop&q=75"
)
""", None, "9. Formatting", "Large photo of the selected property, or a default photo when several are selected.", category="ImageUrl"),
    measure("Neutral Color", f'"{MUTED}"', None, "9. Formatting"),
    measure("Warning Color", f'"{BAD}"', None, "9. Formatting"),
    measure("Good Color", f'"{GOOD}"', None, "9. Formatting"),
    measure("Occupancy Color", f'IF ( [Occupancy %] < 0.9, "{BAD}", "{ACCENT}" )', None, "9. Formatting"),
    measure("Occupancy Text Color", f'IF ( [Occupancy %] < 0.9, "{BAD}", "{INK}" )', None, "9. Formatting"),
    measure("Collection Text Color", f'IF ( [Collection Rate] < 0.93, "{BAD}", "{INK}" )', None, "9. Formatting"),
    measure("Occupancy Bar", f"""
VAR _p = [Occupancy %]
VAR _w = FORMAT ( ROUND ( MIN ( 1, _p ) * 100, 0 ), "0" )
VAR _c = IF ( _p < 0.9, "%23D9735B", "%232F6B4F" )
RETURN
    IF ( NOT ISBLANK ( _p ), {BAR} )
""", None, "9. Formatting", "Inline SVG progress bar for occupancy.", category="ImageUrl"),
    measure("Collection Bar", f"""
VAR _p = [Collection Rate]
VAR _w = FORMAT ( ROUND ( MIN ( 1, _p ) * 100, 0 ), "0" )
VAR _c = IF ( _p < 0.93, "%23D9735B", "%234E9A76" )
RETURN
    IF ( NOT ISBLANK ( _p ), {BAR} )
""", None, "9. Formatting", "Inline SVG progress bar for the collection rate.", category="ImageUrl"),
]

build(PROJECT, "RealEstate", tables, relationships, measures, date_range=((2024, 1, 1), (2026, 12, 31)))
