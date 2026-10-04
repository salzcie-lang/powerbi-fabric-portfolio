#!/usr/bin/env bash
# Builds the Finance Command Center report (dark glass bento). Run from 04_Finance-Operations once
# FinanceCFO.Report exists, is bound to the local model and pbir is connected to it.
# Geometry matches make_background_finance.py; the bespoke charts are SVG measures shown in image visuals.
R="FinanceCFO.Report"; M="_Measures"
INK="#F3F5FA"; TEXT="#C9D0DE"; MUTED="#8D96AA"; GRID="#232A3B"; CARD="#0E1424"; BAR="#24407A"
source "$(dirname "$0")/pbir_lib.sh"
c() { echo "{\"solid\": {\"color\": \"$1\"}}"; }

# img <page> <name> <measure> <x> <y> <w> <h>: SVG measure in a chrome-free image visual
img() {
  local v="$R/$1.Page/$2.Visual"
  p add visual image "$R/$1.Page" -n "$2" --image "$M.$3" --x "$4" --y "$5" --width "$6" --height "$7" -f
  p visuals background "$v" --no-show; p visuals border "$v" --no-show; p visuals title "$v" --no-show
  for s in top bottom left right; do p set "$v.padding.$s" --value 0; done
  p visuals header "$v" --no-show
}
# bind_images <page folder> name=Measure ...: pbir cannot put a measure in image.sourceField, see bind_svg_images.py
bind_images() { python "$(dirname "$0")/bind_svg_images.py" "$R" "$@"; }
# navto <page> <name> <target page> <rail icon centre y>
navto() {
  local v="$R/$1.Page/$2.Visual"
  p add visual actionButton "$R/$1.Page" -n "$2" --x 24 --y $(($4-16)) --width 32 --height 32 -f
  p visuals action "$v" --type PageNavigation --target "$(page_id "$3")" --tooltip "$3"
  for o in fill outline text icon; do p set "$v.$o.show" --value false; done
}

# ---------------------------------------------------------------- theme (dark)
p theme set-colors "$R" --data-colors '["#4C8DFF","#FF8A3D","#9B7BFF","#5BE3B0","#7AB0FF","#FFB86B","#FF6B7A","#5F6880"]' --good "#5BE3B0" --bad "#FF6B7A" --neutral "$MUTED" --foreground "$INK" --background "$CARD"
p theme set-fonts "$R" title --font-face "Segoe UI Semibold" --font-size 11 --color "$INK"
p theme set-fonts "$R" label --font-face "Segoe UI" --font-size 9 --color "$MUTED"
p theme set-fonts "$R" callout --font-face "Segoe UI Semibold" --font-size 24 --color "$INK"
for ax in categoryAxis valueAxis; do p theme set-formatting "$R" "*.*.$ax.labelColor" --json "$(c $MUTED)"; p theme set-formatting "$R" "*.*.$ax.gridlineColor" --json "$(c $GRID)"; done
p theme set-formatting "$R" "*.*.labels.color" --json "$(c $TEXT)"
p theme set-formatting "$R" "*.*.legend.labelColor" --json "$(c $MUTED)"
p theme set-formatting "$R" "*.*.title.fontColor" --json "$(c $INK)"
# the glass panes are drawn in the background image, so no visual gets chrome of its own
for k in border dropShadow divider subTitle background; do p theme set-formatting "$R" "*.*.$k.show" --value false; done

# ---------------------------------------------------------------- pages
p pages rename "$R/Page 1.Page" --to "Overview" -f
p add page "$R/p1.Page" -n "Income Statement"; p rm "$R/Income Statement.Page/Title.Visual" -f
p pages background "$R/Overview.Page" --image "assets/bg_overview.png" --scaling Fit --transparency 0
p pages background "$R/Income Statement.Page" --image "assets/bg_statement.png" --scaling Fit --transparency 0
p add filter Date "Fiscal Year" -r "$R" --values "FY 2026"
navto "Overview" navStatement "Income Statement" 152
navto "Income Statement" navOverview "Overview" 104

# ---------------------------------------------------------------- Overview
PG="Overview"; P="$R/$PG.Page"
img "$PG" header "SVG Header" 84 40 520 18
img "$PG" hero "SVG Revenue Hero" 80 72 420 200
img "$PG" tileGM "SVG Tile Gross Margin" 512 72 188 94
img "$PG" tileEBITDA "SVG Tile EBITDA Margin" 712 72 188 94
img "$PG" tileNI "SVG Tile Net Income" 512 178 188 94
img "$PG" tileOpex "SVG Tile OpEx Ratio" 712 178 188 94
img "$PG" ring "SVG Budget Ring" 912 72 352 200
img "$PG" bridge "SVG PnL Bridge" 80 284 560 210
img "$PG" opexVar "SVG OpEx Variance" 652 284 296 210
img "$PG" cash "SVG Cash" 960 284 304 210
img "$PG" cycle "SVG Cash Cycle" 80 506 390 198
img "$PG" aging "SVG AR Aging" 482 506 368 198

bind_images Overview "header=SVG Header" "hero=SVG Revenue Hero" "tileGM=SVG Tile Gross Margin" "tileEBITDA=SVG Tile EBITDA Margin" "tileNI=SVG Tile Net Income" "tileOpex=SVG Tile OpEx Ratio" "ring=SVG Budget Ring" "bridge=SVG PnL Bridge" "opexVar=SVG OpEx Variance" "cash=SVG Cash" "cycle=SVG Cash Cycle" "aging=SVG AR Aging"

p add visual tableEx "$P" -n overdue -d "Values:Receivables.Customer" -d "Values:$M.AR Overdue" -d "Values:$M.Oldest Days Overdue" -d "Values:$M.SVG Overdue Bar" --x 872 --y 540 --width 384 --height 160 -f
p add filter Receivables Customer -v "$P/overdue.Visual" --type TopN --n 6 --by-table "$M" --by-field "AR Overdue"
p visuals sort "$P/overdue.Visual" -f "$M.AR Overdue" -d Descending
p visuals title "$P/overdue.Visual" --no-show; p visuals background "$P/overdue.Visual" --no-show; p visuals border "$P/overdue.Visual" --no-show
table_style "$P/overdue.Visual" "" 9
colour_col "$P/overdue.Visual" "Days Overdue Color" "Oldest Days Overdue"
p fields rename "$R" "$M.AR Overdue" "Overdue"
p fields rename "$R" "$M.Oldest Days Overdue" "Oldest (days)"
p fields rename "$R" "$M.SVG Overdue Bar" "Share of largest"

info "$PG" infoHero 500 72 "Revenue for the selected period with the change on the same months last year and on budget. Glow line: actual by month. Dashed: budget."
info "$PG" infoRing 1264 72 "Ring: EBITDA as a share of budgeted EBITDA. Rows: revenue, gross profit and net income against budget; the tick marks 100%."
info "$PG" infoBridge 640 284 "How revenue becomes net income. Blue bars are totals, orange bars are deductions. Small print is each item as a share of revenue."
info "$PG" infoOpex 948 284 "Operating expense accounts against budget. Orange runs over budget, green runs under."
info "$PG" infoCash 1264 284 "Cash at period end, how many months of operating cost it covers, and free cash flow (operating cash flow less capex) by month."
info "$PG" infoCycle 470 506 "Days sales outstanding plus days inventory outstanding minus days payables outstanding, on trailing three months."
info "$PG" infoAging 850 506 "Open invoices at period end by days past due."
info "$PG" infoOverdue 1264 506 "Customers with the most overdue receivables and the age of their oldest open invoice."

p pages active-page "$R" "Overview"
pbir -q validate "$R" --fields 2>&1 | tail -3

# ---------------------------------------------------------------- period slicer (dropdown inside the drawn pill)
for PG in "Overview" "Income Statement"; do
  slicer "$PG" slQuarter "Date.Quarter" "Quarter" 1122
  p visuals position "$R/$PG.Page/slQuarter.Visual" --y 9
  p set "$R/$PG.Page/slQuarter.Visual.general.outlineColor" --value "$CARD"; p set "$R/$PG.Page/slQuarter.Visual.items.textSize" --value 9
done

# ---------------------------------------------------------------- Income Statement
PG="Income Statement"; P="$R/$PG.Page"; WELL="#0A0F1C"
img "$PG" header "SVG Header" 84 40 520 18
bind_images "$(page_id "$PG")" "header=SVG Header"
# well_table <visual>: native table sitting on a drawn solid well
well_table() {
  p visuals title "$1" --no-show
  table_style "$1" "" "$2"
  p set "$1.columnHeaders.backColor" --value "$WELL"; for k in backColorPrimary backColorSecondary; do p set "$1.values.$k" --value "$WELL"; done
  p set "$1.grid.outlineColor" --value "$WELL"; p set "$1.values.outlineColor" --value "$WELL"; p set "$1.columnHeaders.outlineColor" --value "$GRID"
  p set "$1.grid.gridHorizontalColor" --value "#1A2132"; p set "$1.columnHeaders.fontSize" --value 8
}
T="$P/statement.Visual"
p add visual tableEx "$P" -n statement -d "Values:PnL Lines.Line" -d "Values:$M.Actual" -d "Values:$M.Budget" -d "Values:$M.Var vs Budget" -d "Values:$M.Var % vs Budget" -d "Values:$M.SVG Line Bar" -d "Values:$M.Prior Year" -d "Values:$M.Var % vs PY" -d "Values:$M.SVG Line Trend" --x 98 --y 114 --width 656 --height 574 -f
p visuals sort "$T" -f "PnL Lines.Line" -d Ascending
well_table "$T" 9
p set "$T.grid.rowPadding" --value 4; p set "$T.grid.imageHeight" --value 16; p set "$T.grid.imageWidth" --value 96
for f in Actual Budget "Prior Year"; do p set "$T.columnFormatting.field($M.$f).alignment" --value Right; done
p visuals cf "$T" --measure "values.fontColor $M.PnL Line Color" --target-field "PnL Lines.Line"
colour_col "$T" "PnL Line Color" "Actual"
colour_col "$T" "Budget Var Color" "Var vs Budget"; colour_col "$T" "Budget Var Color" "Var % vs Budget"; colour_col "$T" "PY Var Color" "Var % vs PY"

C="$P/ebitdaTrend.Visual"
p add visual lineChart "$P" -n ebitdaTrend -d "Category:Date.Month Start" -d "Y:$M.EBITDA" -d "Y:$M.EBITDA Budget" --x 796 --y 108 --width 456 --height 256 -f
p visuals title "$C" --no-show; line_style "$C" "EBITDA Budget"
p set "$C.lineStyles.areaShow" --value true; p set "$C.lineStyles.field($M.EBITDA Budget).areaShow" --value false
p set "$C.legend.fontSize" --value 8.5; p set "$C.valueAxis.showAxisTitle" --value false; p set "$C.categoryAxis.showAxisTitle" --value false

D="$P/deptTable.Visual"
p add visual tableEx "$P" -n deptTable -d "Values:Departments.Department" -d "Values:$M.OpEx" -d "Values:$M.OpEx Budget" -d "Values:$M.OpEx Variance %" -d "Values:$M.SVG Dept Bar" --x 802 --y 426 --width 444 --height 262 -f
p visuals sort "$D" -f "$M.OpEx Variance %" -d Descending
well_table "$D" 9
p set "$D.grid.rowPadding" --value 5; p set "$D.grid.imageHeight" --value 16; p set "$D.grid.imageWidth" --value 96
colour_col "$D" "OpEx Variance Color" "OpEx Variance %"
p pages interactions "$P" --disable-from deptTable

p fields rename "$R" "$M.SVG Line Bar" "vs budget"; p fields rename "$R" "$M.SVG Line Trend" "Trend"; p fields rename "$R" "$M.SVG Dept Bar" "vs budget "
p fields rename "$R" "$M.Var vs Budget" "Var"; p fields rename "$R" "$M.Var % vs Budget" "Var %"; p fields rename "$R" "$M.Var % vs PY" "YoY %"
p fields rename "$R" "$M.OpEx" "Actual "; p fields rename "$R" "$M.OpEx Budget" "Budget "; p fields rename "$R" "$M.OpEx Variance %" "Var % "
info "$PG" infoStatement 772 72 "Income statement for the selected period in thousands. Variance colours: green is favourable (more revenue or profit, less cost), red is unfavourable."
info "$PG" infoTrend 1264 72 "EBITDA by month against budget (dashed)."
info "$PG" infoDept 1264 384 "Operating expenses by department against budget. Orange bars run over budget."
pbir -q validate "$R" --fields 2>&1 | tail -3

# ---------------------------------------------------------------- polish
p set "$T.grid.rowPadding" --value 2; p set "$T.values.fontSize" --value 8.5; p set "$T.grid.imageHeight" --value 14; p set "$T.grid.imageWidth" --value 84
for f in "Var vs Budget" "Var % vs Budget" "Var % vs PY"; do p set "$T.columnFormatting.field($M.$f).alignment" --value Right; done
p set "$C.lineStyles.areaMatchStrokeColor" --value false; p set "$C.lineStyles.areaColor" --value "#1B3A8A"
p set "$D.grid.rowPadding" --value 8
for f in "OpEx" "OpEx Budget" "OpEx Variance %"; do p set "$D.columnFormatting.field($M.$f).alignment" --value Right; done
p set "$R/**/slQuarter.Visual.items.outlineStyle" --value 0 -f
pbir -q validate "$R" --fields 2>&1 | tail -2
p set "$R/**/slQuarter.Visual.items.accessibilityContrastProperties" --value false -f; p set "$R/**/slQuarter.Visual.general.outlineWeight" --value 1 -f
p set "$T.grid.rowPadding" --value 3; p set "$T.values.fontSize" --value 9; p set "$D.grid.rowPadding" --value 6
p set "$T.columnHeaders.columnAdjustment" --value growToFit; p set "$D.columnHeaders.columnAdjustment" --value growToFit

# ---------------------------------------------------------------- clickable Deneb charts (replace the bridge and OpEx SVG panels)
# Both charts are built on the disconnected 'PnL Lines' table, so a click only refocuses the headline card
# (see [Focus Value]) and never blanks the other panels.
SPECS="$(dirname "$0")/deneb"; P="$R/Overview.Page"
p rm "$P/bridge.Visual" -f; p rm "$P/opexVar.Visual" -f
# deneb <name> <spec> <x> <y> <w> <h> <columns...> -- <measures...>: pbir cannot create custom visuals, see add_deneb.py
deneb() {
  local n=$1 spec=$2; shift 2
  python "$(dirname "$0")/add_deneb.py" "$R" Overview "$n" "$SPECS/$spec" "$SPECS/config.json" "$@"
}
deneb bridge bridge.vl.json 80 284 560 210 "PnL Lines.Bridge Label" "PnL Lines.Bridge Order" "PnL Lines.Line Name" -- "$M.Bridge Low" "$M.Bridge High" "$M.PnL Value" "$M.PnL Budget" "$M.PnL Variance %" "$M.Pct of Revenue"
p add filter "PnL Lines" "Bridge Label" -v "$P/bridge.Visual" --values "Revenue" --values "COGS" --values "Gross profit" --values "OpEx" --values "EBITDA" --values "D&A" --values "Interest" --values "Tax" --values "Net income"
deneb opexVar opex.vl.json 652 284 296 184 "PnL Lines.Line Name" -- "$M.PnL Value" "$M.PnL Budget" "$M.PnL Variance" "$M.PnL Variance %"
p add filter "PnL Lines" "Line Group" -v "$P/opexVar.Visual" --values "OpEx"
img "Overview" opexTotal "SVG OpEx Total" 652 466 296 26
bind_images Overview "opexTotal=SVG OpEx Total"
# a click in one chart must not empty the other
p pages interactions "$P" --source bridge --target opexVar --type NoFilter
p pages interactions "$P" --source opexVar --target bridge --type NoFilter
p pages background "$P" --image "assets/bg_overview.png" --scaling Fit --transparency 0
pbir -q validate "$R" --fields 2>&1 | tail -2
# (i) buttons sit above the Deneb visuals, and their tooltips explain the click behaviour
OV="$(page_id Overview)"
for b in infoBridge infoOpex; do p visuals z-order "$P/$b.Visual" --front; done
p visuals action "$P/infoHero.Visual" --type PageNavigation --target "$OV" --tooltip "Headline card. Shows net revenue; click a bar in the bridge or in OpEx vs budget and it switches to that line, with change on prior year and on budget. Glow line: actual by month. Dashed: budget. Click the bar again to return."
p visuals action "$P/infoBridge.Visual" --type PageNavigation --target "$OV" --tooltip "How revenue becomes net income. Blue bars are totals, orange bars are deductions; small print is share of revenue. Hover for budget and variance, click a bar to focus the headline card on it."
p visuals action "$P/infoOpex.Visual" --type PageNavigation --target "$OV" --tooltip "Operating expense accounts against budget. Orange runs over budget, green under. Hover for amounts, click a bar to focus the headline card on that account."
