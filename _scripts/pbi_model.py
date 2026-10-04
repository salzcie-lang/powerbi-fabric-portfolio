"""Writes a TMDL semantic model (import mode over local CSV files) from a small Python spec.

Used by the model_*.py scripts, one per dashboard. Re-running overwrites the model definition.
"""
import json
import uuid
from pathlib import Path

M_TYPE = {"int": "Int64.Type", "number": "type number", "money": "Currency.Type", "text": "type text", "date": "type date"}
TMDL_TYPE = {"int": "int64", "number": "double", "money": "decimal", "text": "string", "date": "dateTime"}
DEFAULT_FORMAT = {"int": "0", "date": "dd mmm yyyy", "money": "#,##0", "number": "#,##0.00"}


def _tag(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "/".join(parts)))


def _q(name):
    return name if name.replace("_", "").isalnum() and not name[0].isdigit() else "'" + name.replace("'", "''") + "'"


def col(name, kind, source=None, hidden=False, agg="none", fmt=None, sort_by=None, category=None, key=False):
    return dict(name=name, kind=kind, source=source or name, hidden=hidden, agg=agg, fmt=fmt, sort_by=sort_by,
                category=category, key=key)


def measure(name, dax, fmt=None, folder=None, desc=None, category=None):
    """category='ImageUrl' marks a measure that returns an image URL or SVG data URI."""
    return dict(name=name, dax=dax.strip("\n"), fmt=fmt, folder=folder, desc=desc, category=category)


def _column_block(table, c):
    out = [f"\tcolumn {_q(c['name'])}", f"\t\tdataType: {TMDL_TYPE[c['kind']]}"]
    if c["hidden"]:
        out.append("\t\tisHidden")
    if c["key"]:
        out.append("\t\tisKey")
    fmt = c["fmt"] or DEFAULT_FORMAT.get(c["kind"])
    if fmt:
        out.append(f"\t\tformatString: {fmt}")
    out.append(f"\t\tlineageTag: {_tag(table, 'col', c['name'])}")
    if c["category"]:
        out.append(f"\t\tdataCategory: {c['category']}")
    out.append(f"\t\tsummarizeBy: {c['agg']}")
    out.append(f"\t\tsourceColumn: {c['source']}")
    if c["sort_by"]:
        out.append(f"\t\tsortByColumn: {_q(c['sort_by'])}")
    out += ["", "\t\tannotation SummarizationSetBy = User", ""]
    return out


def _measure_block(table, m):
    out = []
    if m["desc"]:
        out.append(f"\t/// {m['desc']}")
    lines = m["dax"].splitlines()
    if len(lines) == 1:
        out.append(f"\tmeasure {_q(m['name'])} = {lines[0].strip()}")
    else:
        out.append(f"\tmeasure {_q(m['name'])} =")
        out += ["\t\t\t" + ln for ln in lines]
    if m["fmt"]:
        out.append(f"\t\tformatString: {m['fmt']}")
    if m["folder"]:
        out.append(f"\t\tdisplayFolder: {m['folder']}")
    if m.get("category"):
        out.append(f"\t\tdataCategory: {m['category']}")
    out += [f"\t\tlineageTag: {_tag(table, 'measure', m['name'])}", ""]
    return out


def _partition(table, m_lines):
    return [f"\tpartition {_q(table)} = m", "\t\tmode: import", "\t\tsource ="] + ["\t\t\t\t" + ln for ln in m_lines] + [""]


def _csv_m(file, columns):
    types = ", ".join(f'{{"{c["source"]}", {M_TYPE[c["kind"]]}}}' for c in columns)
    renames = ", ".join(f'{{"{c["source"]}", "{c["name"]}"}}' for c in columns if c["source"] != c["name"])
    lines = [
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "\\{file}"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
        f'    Selected = Table.SelectColumns(Promoted, {{{", ".join(chr(34) + c["source"] + chr(34) for c in columns)}}}),',
        f'    Typed = Table.TransformColumnTypes(Selected, {{{types}}}, "en-US")' + ("," if renames else ""),
    ]
    if renames:
        lines.append(f"    Renamed = Table.RenameColumns(Typed, {{{renames}}})")
    lines += ["in", "    Renamed" if renames else "    Typed"]
    # sourceColumn must match the query output, which is the renamed column
    for c in columns:
        c["source"] = c["name"]
    return lines


DATE_COLUMNS = [
    col("Date", "date", key=True), col("Year", "int"), col("Fiscal Year", "text"), col("Quarter", "text"),
    col("Year Quarter", "text"), col("Month Number", "int", hidden=True),
    col("Month", "text", sort_by="Month Number"), col("Month Start", "date", fmt="mmm yyyy"),
    col("Year Month", "text", sort_by="Month Start"), col("Weekday", "text", sort_by="Weekday Number"),
    col("Weekday Number", "int", hidden=True),
]


def _date_m(start, end):
    return [
        "let",
        f"    Start = #date({start[0]}, {start[1]}, {start[2]}),",
        f"    End = #date({end[0]}, {end[1]}, {end[2]}),",
        "    Dates = List.Dates(Start, Duration.Days(End - Start) + 1, #duration(1, 0, 0, 0)),",
        "    AsTable = Table.FromList(Dates, Splitter.SplitByNothing(), type table [Date = date]),",
        "    Added = Table.FromRecords(",
        "        Table.TransformRows(AsTable, each [",
        "            Date = [Date],",
        "            Year = Date.Year([Date]),",
        '            #"Fiscal Year" = "FY " & Text.From(Date.Year([Date])),',
        '            Quarter = "Q" & Text.From(Date.QuarterOfYear([Date])),',
        '            #"Year Quarter" = Text.From(Date.Year([Date])) & " Q" & Text.From(Date.QuarterOfYear([Date])),',
        '            #"Month Number" = Date.Month([Date]),',
        '            Month = Date.ToText([Date], "MMM", "en-US"),',
        '            #"Month Start" = Date.StartOfMonth([Date]),',
        '            #"Year Month" = Date.ToText([Date], "MMM yyyy", "en-US"),',
        '            Weekday = Date.ToText([Date], "ddd", "en-US"),',
        '            #"Weekday Number" = Date.DayOfWeek([Date], Day.Monday) + 1',
        "        ]),",
        '        type table [Date = date, Year = Int64.Type, #"Fiscal Year" = text, Quarter = text, #"Year Quarter" = text, #"Month Number" = Int64.Type,',
        '            Month = text, #"Month Start" = date, #"Year Month" = text, Weekday = text, #"Weekday Number" = Int64.Type]',
        "    )",
        "in",
        "    Added",
    ]


def build(project_dir, name, tables, relationships, measures, date_range, measure_table="_Measures"):
    """tables: {table_name: (csv_file, [col(...)])}; relationships: [("Fact.Col", "Dim.Col")]."""
    project_dir = Path(project_dir)
    sm = project_dir / f"{name}.SemanticModel"
    defn = sm / "definition"
    (defn / "tables").mkdir(parents=True, exist_ok=True)
    for old in (defn / "tables").glob("*.tmdl"):
        old.unlink()

    def write(path, lines):
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    (sm / "definition.pbism").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}}, indent=2) + "\n", encoding="utf-8")
    (sm / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": name},
        "config": {"version": "2.0", "logicalId": _tag(name, "semantic-model")}}, indent=2) + "\n", encoding="utf-8")

    write(defn / "database.tmdl", ["database", "\tcompatibilityLevel: 1606", ""])

    data_folder = str(project_dir / "data")
    write(defn / "expressions.tmdl", [
        f'expression DataFolder = "{data_folder}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
        f"\tlineageTag: {_tag(name, 'expr', 'DataFolder')}",
        "", "\tannotation PBI_ResultType = Text", ""])

    names = []
    for tname, (file, columns) in tables.items():
        lines = [f"table {_q(tname)}", f"\tlineageTag: {_tag(tname)}", ""]
        m_lines = _csv_m(file, columns)
        for c in columns:
            lines += _column_block(tname, c)
        lines += _partition(tname, m_lines)
        write(defn / "tables" / f"{tname}.tmdl", lines)
        names.append(tname)

    lines = ["table Date", f"\tlineageTag: {_tag('Date')}", "\tdataCategory: Time", ""]
    for c in DATE_COLUMNS:
        lines += _column_block("Date", dict(c))
    lines += _partition("Date", _date_m(*date_range))
    write(defn / "tables" / "Date.tmdl", lines)
    names.append("Date")

    lines = [f"table {measure_table}", f"\tlineageTag: {_tag(measure_table)}", ""]
    for m in measures:
        lines += _measure_block(measure_table, m)
    lines += _column_block(measure_table, col("Placeholder", "text", hidden=True))
    lines += _partition(measure_table, ["let", "    Source = #table(type table [Placeholder = text], {})", "in", "    Source"])
    write(defn / "tables" / f"{measure_table}.tmdl", lines)
    names.append(measure_table)

    rel = []
    for frm, to in relationships:
        ft, fc = frm.split(".")
        tt, tc = to.split(".")
        rel += [f"relationship {_tag('rel', frm, to)}", f"\tfromColumn: {_q(ft)}.{_q(fc)}", f"\ttoColumn: {_q(tt)}.{_q(tc)}", ""]
    write(defn / "relationships.tmdl", rel)

    model = ["model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tdiscourageImplicitMeasures",
             "\tsourceQueryCulture: en-US", "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
             "annotation __PBI_TimeIntelligenceEnabled = 0", "",
             "annotation PBI_QueryOrder = " + json.dumps(["DataFolder"] + names), ""]
    model += [f"ref table {_q(n)}" for n in names] + [""]
    write(defn / "model.tmdl", model)
    print(f"wrote {sm} ({len(names)} tables, {len(measures)} measures, {len(relationships)} relationships)")
