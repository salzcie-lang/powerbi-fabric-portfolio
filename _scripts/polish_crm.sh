#!/usr/bin/env bash
# Polish pass for the CRM report: quieter chrome, lighter marks, tighter KPI column, tables without scrollbars.
# Run from 02_CRM-Pipeline after build_crm.sh and relayout_crm.sh.
R="CRMPipeline.Report"; M="_Measures"
INK="#F2F4F7"; TEXT="#C9D0DB"; MUTED="#8B95A7"; GRID="#232A34"; CARD="#161B22"
source "$(dirname "$0")/pbir_lib.sh"
PAGES=("Pipeline Overview" "Funnel & Conversion" "Rep Performance" "Deal Detail")
declare -A KPIS=( ["Pipeline Overview"]="Won Pipe Win Deal" ["Funnel & Conversion"]="Leads Qual L2W Cycle"
                  ["Rep Performance"]="Quota AtQuota Act Weighted" ["Deal Detail"]="Won Open Pipe Stalled" )

# Slicers: no bright box around the dropdown; the drawn pill is the container
p set "$R/**/sl*.Visual.general.outlineColor" --value "$CARD" -f
p set "$R/**/sl*.Visual.general.outlineWeight" --value 1 -f
p set "$R/**/sl*.Visual.items.outlineStyle" --value None -f
p set "$R/**/sl*.Visual.items.textSize" --value 9 -f

# KPI column: larger value sitting directly under its label, delta close beneath, sparkline level with the value
for pg in "${PAGES[@]}"; do
  s=0
  for k in ${KPIS[$pg]}; do
    y0=$((78 + s*154))
    p visuals position "$R/$pg.Page/kpi${k}Value.Visual" --x 34 --y $((y0+50)) --width 160 --height 56
    p visuals position "$R/$pg.Page/kpi${k}Delta.Visual" --x 34 --y $((y0+102)) --width 250 --height 38
    pbir -q visuals position "$R/$pg.Page/kpi${k}Spark.Visual" --x 196 --y $((y0+58)) --width 90 --height 40 >/dev/null 2>&1
    s=$((s+1))
  done
  p set "$R/$pg.Page/kpi*Value.Visual.value.fontSize" --value 23 -f
  p set "$R/$pg.Page/kpi*Delta.Visual.value.fontSize" --value 9.5 -f
done
# KPI precision: no more "$5M" or "3K"
money2() { p set "$R/$1.Page/kpi$2Value.Visual.value.labelPrecision" --value 2; }
plain()  { p set "$R/$1.Page/kpi$2Value.Visual.value.labelDisplayUnits" --value 1; }
money2 "Pipeline Overview" Won; money2 "Pipeline Overview" Pipe
p set "$R/Pipeline Overview.Page/kpiDealValue.Visual.value.labelPrecision" --value 1
plain "Funnel & Conversion" Leads; plain "Rep Performance" Act
money2 "Rep Performance" Weighted; money2 "Deal Detail" Pipe

# Bars: slimmer marks with breathing room
for v in "Pipeline Overview.Page/pipeByStage" "Pipeline Overview.Page/wonByTeam" "Rep Performance.Page/attainByTeam" "Rep Performance.Page/actByType"; do
  p set "$R/$v.Visual.categoryAxis.innerPadding" --value 55; done
for v in "Funnel & Conversion.Page/winBySource" "Funnel & Conversion.Page/lostReasons"; do
  p set "$R/$v.Visual.categoryAxis.innerPadding" --value 40; done

# Lines: a dark teal wash under the line instead of a bright block, and a smaller, lighter legend
for v in "Pipeline Overview.Page/wonTrend" "Funnel & Conversion.Page/leadsTrend"; do
  p set "$R/$v.Visual.lineStyles.areaMatchStrokeColor" --value false
  p set "$R/$v.Visual.lineStyles.areaColor" --value "#115E59"
  p set "$R/$v.Visual.legend.fontSize" --value 8.5; p set "$R/$v.Visual.legend.bold" --value false
done
p set "$R/Funnel & Conversion.Page/leadsTrend.Visual.lineStyles.field($M.Qualified Leads).areaShow" --value false
p set "$R/Funnel & Conversion.Page/leadsTrend.Visual.dataPoint.field($M.Qualified Leads).fill" --value "#8B95A7"
p set "$R/Funnel & Conversion.Page/stageFunnel.Visual.percentBarLabel.color" --value "$MUTED"

# Tables: hairline rules, softer text, no heavy white borders
for v in "Pipeline Overview.Page/openDeals" "Pipeline Overview.Page/leaderboard" "Funnel & Conversion.Page/sourceTable" "Rep Performance.Page/repTable" "Deal Detail.Page/dealTable"; do
  t="$R/$v.Visual"
  for k in fontColorPrimary fontColorSecondary; do p set "$t.values.$k" --value "$TEXT"; done
  p set "$t.grid.gridHorizontalColor" --value "$GRID"; p set "$t.grid.outlineColor" --value "$GRID"
  p set "$t.columnHeaders.outlineColor" --value "$GRID"; p set "$t.values.outlineColor" --value "$GRID"
  p set "$t.columnHeaders.fontSize" --value 8
done
# Small cards show a top eight, so nothing scrolls
p add filter Reps Rep -v "$R/Pipeline Overview.Page/leaderboard.Visual" --type TopN --n 8 --by-table "$M" --by-field "Won Revenue"
p add filter Opportunities Opportunity -v "$R/Pipeline Overview.Page/openDeals.Visual" --type TopN --n 8 --by-table "$M" --by-field "Open Pipeline"
p visuals title "$R/Pipeline Overview.Page/leaderboard.Visual" --text "Top reps by won revenue"
# The scorecard fills its tall card
p set "$R/Rep Performance.Page/repTable.Visual.grid.rowPadding" --value 10
p set "$R/Rep Performance.Page/repTable.Visual.values.fontSize" --value 9.5

# Deal Detail: second KPI was a duplicate of the third; show weighted pipeline instead
p fields replace "$R/Deal Detail.Page/kpiOpenValue.Visual" --from "$M.Open Deals" --to "$M.Weighted Pipeline"
p fields replace "$R/Deal Detail.Page/kpiOpenDelta.Visual" --from "$M.Open Deals Label" --to "$M.Weighted Pipeline Label"
money2 "Deal Detail" Open

pbir -q validate "$R" --fields 2>&1 | tail -2
