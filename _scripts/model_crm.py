"""Semantic model spec for 02_CRM-Pipeline."""
from pathlib import Path

from pbi_model import build, col, measure

PROJECT = Path(__file__).resolve().parents[1] / "02_CRM-Pipeline"
GOOD, BAD, MUTED, ACCENT, TEXT = "#6EE7B7", "#FB8FA4", "#8B95A7", "#5EEAD4", "#D7DCE5"

tables = {
    "Opportunities": ("opportunities.csv", [
        col("OpportunityKey", "int", hidden=True), col("Opportunity", "text"), col("AccountKey", "int", hidden=True),
        col("RepKey", "int", hidden=True), col("LeadKey", "int", hidden=True), col("Lead Source", "text", "LeadSource"),
        col("Created Date", "date", "CreatedDate"), col("Close Date", "date", "CloseDate"), col("Stage", "text", hidden=True),
        col("Amount", "money", hidden=True), col("Probability", "number", hidden=True),
        col("Lost Reason", "text", "LostReason"), col("Last Activity Date", "date", "LastActivityDate"),
    ]),
    "Leads": ("leads.csv", [
        col("LeadKey", "int", hidden=True), col("Created Date", "date", "CreatedDate"), col("Lead Source", "text", "LeadSource"),
        col("AccountKey", "int", hidden=True), col("First Response Hours", "number", "FirstResponseHours", hidden=True),
        col("Status", "text"),
    ]),
    "Stage History": ("stage_history.csv", [
        col("OpportunityKey", "int", hidden=True), col("Stage Reached", "text", "Stage", sort_by="Stage Order"),
        col("Entered Date", "date", "EnteredDate"), col("Stage Order", "int", "StageOrder", hidden=True),
    ]),
    "Activities": ("activities.csv", [
        col("ActivityKey", "int", hidden=True), col("OpportunityKey", "int", hidden=True), col("RepKey", "int", hidden=True),
        col("Activity Date", "date", "ActivityDate"), col("Activity Type", "text", "ActivityType"),
    ]),
    "Accounts": ("accounts.csv", [
        col("AccountKey", "int", hidden=True), col("Account", "text"), col("Segment", "text"), col("Industry", "text"),
        col("Country", "text", category="Country"), col("Employees", "int", hidden=True),
    ]),
    "Reps": ("reps.csv", [
        col("RepKey", "int", hidden=True), col("Rep", "text"), col("Team", "text"),
        col("Quarterly Quota", "money", "QuarterlyQuota", hidden=True),
    ]),
    "Stages": ("stages.csv", [
        col("Stage", "text", sort_by="Stage Order"), col("Stage Order", "int", "StageOrder", hidden=True),
        col("Stage Group", "text", "StageGroup"), col("Default Probability", "number", "DefaultProbability", hidden=True),
    ]),
}

relationships = [
    ("Opportunities.Close Date", "Date.Date"), ("Opportunities.AccountKey", "Accounts.AccountKey"),
    ("Opportunities.RepKey", "Reps.RepKey"), ("Opportunities.Stage", "Stages.Stage"),
    ("Leads.Created Date", "Date.Date"), ("Stage History.OpportunityKey", "Opportunities.OpportunityKey"),
    ("Activities.Activity Date", "Date.Date"), ("Activities.RepKey", "Reps.RepKey"),
]

# Prior-year measures stop at the as-of date shifted back a year, so year to date compares like with like.
PY = """
VAR _Last = [As Of Date]
RETURN
    CALCULATE (
        {expr},
        SAMEPERIODLASTYEAR ( 'Date'[Date] ),
        'Date'[Date] <= EDATE ( _Last, -12 )
    )
"""
OPEN = "Stages[Stage Group] = \"Open\", REMOVEFILTERS ( 'Date' )"


def yoy_set(base, fmt, folder, higher_is_better=True, points=False):
    """PY, triangle label and colour measures for one base measure."""
    up, down = (GOOD, BAD) if higher_is_better else (BAD, GOOD)
    change = f"( [{base}] - [{base} PY] ) * 100" if points else f"DIVIDE ( [{base}] - [{base} PY], [{base} PY] )"
    text = 'FORMAT ( ABS ( _d ), "0.0" ) & " pts vs PY"' if points else 'FORMAT ( ABS ( _d ), "0.0%" ) & " vs PY"'
    return [
        measure(f"{base} PY", PY.format(expr=f"[{base}]"), fmt, folder),
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


measures = [
    measure("As Of Date", "CALCULATE ( MAX ( Activities[Activity Date] ), REMOVEFILTERS () )", "dd mmm yyyy", "0. Base",
            "Latest activity date in the data; used as today."),
    measure("Won Revenue", 'CALCULATE ( SUM ( Opportunities[Amount] ), Stages[Stage Group] = "Won" )', "$#,##0", "1. Closed"),
    measure("Won Deals", 'CALCULATE ( COUNTROWS ( Opportunities ), Stages[Stage Group] = "Won" )', "#,##0", "1. Closed"),
    measure("Lost Deals", 'CALCULATE ( COUNTROWS ( Opportunities ), Stages[Stage Group] = "Lost" )', "#,##0", "1. Closed"),
    measure("Win Rate", "DIVIDE ( [Won Deals], [Won Deals] + [Lost Deals] )", "0.0%", "1. Closed"),
    measure("Avg Deal Size", "DIVIDE ( [Won Revenue], [Won Deals] )", "$#,##0", "1. Closed"),
    measure("Avg Sales Cycle", """
CALCULATE (
    AVERAGEX ( Opportunities, DATEDIFF ( Opportunities[Created Date], Opportunities[Close Date], DAY ) ),
    Stages[Stage Group] = "Won"
)
""", "0", "1. Closed", "Average days from creation to close for won deals."),
    measure("Open Pipeline", f"CALCULATE ( SUM ( Opportunities[Amount] ), {OPEN} )", "$#,##0", "2. Pipeline",
            "Value of all open deals. Ignores the date filter because open deals close in the future."),
    measure("Weighted Pipeline", f"CALCULATE ( SUMX ( Opportunities, Opportunities[Amount] * Opportunities[Probability] ), {OPEN} )",
            "$#,##0", "2. Pipeline"),
    measure("Open Deals", f"CALCULATE ( COUNTROWS ( Opportunities ), {OPEN} )", "#,##0", "2. Pipeline"),
    measure("Stalled Deals", f"""
VAR _Cut = [As Of Date] - 21
RETURN
    CALCULATE ( COUNTROWS ( FILTER ( Opportunities, Opportunities[Last Activity Date] < _Cut ) ), {OPEN} ) + 0
""", "#,##0", "2. Pipeline", "Open deals with no activity in the last 21 days."),
    measure("Days Since Activity", f"""
VAR _Last = CALCULATE ( MAX ( Opportunities[Last Activity Date] ), {OPEN} )
RETURN
    IF ( NOT ISBLANK ( _Last ), MAX ( 0, DATEDIFF ( _Last, [As Of Date], DAY ) ) )
""", "0", "2. Pipeline"),
    measure("Leads", "COUNTROWS ( Leads )", "#,##0", "3. Leads"),
    measure("Qualified Leads", 'CALCULATE ( COUNTROWS ( Leads ), Leads[Status] = "Qualified" )', "#,##0", "3. Leads"),
    measure("Qualification Rate", "DIVIDE ( [Qualified Leads], [Leads] )", "0.0%", "3. Leads"),
    measure("Lead to Win Rate", "DIVIDE ( [Won Deals], [Leads] )", "0.0%", "3. Leads",
            "Won deals closed in the period divided by leads created in the period."),
    measure("Deals Reaching Stage", "DISTINCTCOUNT ( 'Stage History'[OpportunityKey] )", "#,##0", "3. Leads"),
    measure("Quota", """
VAR _AsOf = [As Of Date]
VAR _Quarters = COUNTROWS ( FILTER ( VALUES ( 'Date'[Year Quarter] ), CALCULATE ( MIN ( 'Date'[Date] ) ) <= _AsOf ) )
RETURN
    SUM ( Reps[Quarterly Quota] ) * _Quarters
""", "$#,##0", "4. Quota", "Quarterly quota multiplied by the quarters in the selection that have started."),
    measure("Quota Attainment", "DIVIDE ( [Won Revenue], [Quota] )", "0.0%", "4. Quota"),
    measure("Reps at Quota", "COUNTROWS ( FILTER ( Reps, [Quota Attainment] >= 1 ) ) + 0", "#,##0", "4. Quota"),
    measure("Activities", "COUNTROWS ( Activities )", "#,##0", "5. Activity"),
    measure("Deal Amount", "SUM ( Opportunities[Amount] )", "$#,##0", "1. Closed"),
    measure("Activities per Rep", "DIVIDE ( [Activities], COUNTROWS ( Reps ) )", "#,##0", "5. Activity"),
]
measures += yoy_set("Won Revenue", "$#,##0", "1. Closed")
measures += yoy_set("Win Rate", "0.0%", "1. Closed", points=True)
measures += yoy_set("Avg Deal Size", "$#,##0", "1. Closed")
measures += yoy_set("Avg Sales Cycle", "0", "1. Closed", higher_is_better=False)
measures += yoy_set("Won Deals", "#,##0", "1. Closed")
measures += yoy_set("Leads", "#,##0", "3. Leads")
measures += yoy_set("Qualification Rate", "0.0%", "3. Leads", points=True)
measures += yoy_set("Lead to Win Rate", "0.0%", "3. Leads", points=True)
measures += yoy_set("Activities", "#,##0", "5. Activity")
measures += [
    measure("Open Pipeline Label", '[Open Deals] & " open deals"', None, "8. Labels"),
    measure("Weighted Pipeline Label", '"expected from open deals"', None, "8. Labels"),
    measure("Open Deals Label", 'FORMAT ( [Open Pipeline], "$#,##0" ) & " in pipeline"', None, "8. Labels"),
    measure("Stalled Deals Label", '"no activity in 21+ days"', None, "8. Labels"),
    measure("Quota Label", '"of " & FORMAT ( [Quota], "$#,##0" ) & " quota"', None, "8. Labels"),
    measure("Reps at Quota Label", '"of " & COUNTROWS ( Reps ) & " reps at or above quota"', None, "8. Labels"),
    measure("Won YoY", """
IF (
    ISBLANK ( [Won Revenue PY] ) || ISBLANK ( [Won Revenue] ),
    BLANK (),
    VAR _d = DIVIDE ( [Won Revenue] - [Won Revenue PY], [Won Revenue PY] )
    RETURN
        IF ( _d >= 0, "▲ ", "▼ " ) & FORMAT ( ABS ( _d ), "0.0%" )
)
""", None, "8. Labels"),
    measure("Neutral Color", f'"{MUTED}"', None, "9. Formatting"),
    measure("Warning Color", f'"{BAD}"', None, "9. Formatting"),
    measure("Attainment Color", f'IF ( [Quota Attainment] >= 1, "{GOOD}", IF ( [Quota Attainment] >= 0.8, "{TEXT}", "{BAD}" ) )',
            None, "9. Formatting"),
    measure("Win Rate Bar Color", f"""
VAR _All = CALCULATE ( [Win Rate], ALLSELECTED ( Opportunities[Lead Source] ) )
RETURN
    IF ( [Win Rate] < _All, "#3B4654", "#2DD4BF" )
""", None, "9. Formatting"),
    measure("Stale Color", f'IF ( [Days Since Activity] > 21, "{BAD}", "{TEXT}" )', None, "9. Formatting"),
]

build(PROJECT, "CRMPipeline", tables, relationships, measures, date_range=((2024, 1, 1), (2027, 6, 30)))
