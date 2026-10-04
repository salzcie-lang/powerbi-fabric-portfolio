#!/usr/bin/env bash
# Builds the CRM & Pipeline report (dark theme). Run from 02_CRM-Pipeline once CRMPipeline.Report exists,
# is bound to the local model and pbir is connected to it.
R="CRMPipeline.Report"; M="_Measures"
INK="#F2F4F7"; TEXT="#D7DCE5"; MUTED="#8B95A7"; GRID="#262C36"; CARD="#161B22"; BAR="#1F4A47"
source "$(dirname "$0")/pbir_lib.sh"
c() { echo "{\"solid\": {\"color\": \"$1\"}}"; }

# ---------------------------------------------------------------- theme (dark)
p theme set-colors "$R" --data-colors '["#2DD4BF","#3B4654","#99F6E4","#FBBF77","#C4B5FD","#F9A8D4","#7DD3FC","#64748B"]' --good "#6EE7B7" --bad "#FB8FA4" --neutral "#8B95A7" --foreground "$INK" --background "$CARD"
p theme set-fonts "$R" title --font-face "Segoe UI Semibold" --font-size 11 --color "$INK"
p theme set-fonts "$R" label --font-face "Segoe UI" --font-size 9 --color "$MUTED"
p theme set-fonts "$R" callout --font-face "Segoe UI Semibold" --font-size 24 --color "$INK"
for ax in categoryAxis valueAxis; do p theme set-formatting "$R" "*.*.$ax.labelColor" --json "$(c $MUTED)"; p theme set-formatting "$R" "*.*.$ax.gridlineColor" --json "$(c $GRID)"; done
p theme set-formatting "$R" "*.*.labels.color" --json "$(c '#C5CBD6')"
p theme set-formatting "$R" "*.*.legend.labelColor" --json "$(c $MUTED)"
p theme set-formatting "$R" "*.*.title.fontColor" --json "$(c $INK)"

# ---------------------------------------------------------------- pages
PAGES=("Pipeline Overview" "Funnel & Conversion" "Rep Performance" "Deal Detail"); KEYS=(overview funnel reps deals)
p pages rename "$R/Page 1.Page" --to "Pipeline Overview" -f
for i in 1 2 3; do p add page "$R/p$i.Page" -n "${PAGES[$i]}"; p rm "$R/${PAGES[$i]}.Page/Title.Visual" -f; done
for i in 0 1 2 3; do p pages background "$R/${PAGES[$i]}.Page" --image "assets/bg_${KEYS[$i]}.png" --scaling Fit --transparency 0; done
p add filter Date "Fiscal Year" -r "$R" --values "FY 2026"
nav "${PAGES[@]}"

# ---------------------------------------------------------------- Pipeline Overview
PG="Pipeline Overview"; P="$R/$PG.Page"
kpi "$PG" Won 92 200 "Won Revenue" "Won Revenue Label" "Won Revenue Color" 1
kpi "$PG" Pipe 308 200 "Open Pipeline" "Open Pipeline Label" "Neutral Color" 0
kpi "$PG" Win 524 200 "Win Rate" "Win Rate Label" "Win Rate Color" 1
kpi "$PG" Deal 740 200 "Avg Deal Size" "Avg Deal Size Label" "Avg Deal Size Color" 1
kpi_style "$PG"
slicer "$PG" slTeam "Reps.Team" "Team" 956
slicer "$PG" slSegment "Accounts.Segment" "Segment" 1114
p add visual lineChart "$P" -n wonTrend -t "Won revenue by month, this year vs last" -d "Category:Date.Month Start" -d "Y:$M.Won Revenue" -d "Y:$M.Won Revenue PY" --x 92 --y 212 --width 520 --height 236
line_style "$P/wonTrend.Visual" "Won Revenue PY"
p add visual clusteredBarChart "$P" -n pipeByStage -t "Open pipeline by stage" -d "Category:Stages.Stage" -d "Y:$M.Open Pipeline" --x 628 --y 212 --width 312 --height 236
p visuals sort "$P/pipeByStage.Visual" -f "Stages.Stage" -d Ascending
bar_style "$P/pipeByStage.Visual"
p add visual clusteredBarChart "$P" -n wonByTeam -t "Won revenue by team" -d "Category:Reps.Team" -d "Y:$M.Won Revenue" --x 92 --y 464 --width 300 --height 232
p visuals sort "$P/wonByTeam.Visual" -f "$M.Won Revenue" -d Descending
bar_style "$P/wonByTeam.Visual"
p add visual tableEx "$P" -n openDeals -t "Largest open deals" -d "Values:Opportunities.Opportunity" -d "Values:Stages.Stage" -d "Values:$M.Open Pipeline" -d "Values:$M.Days Since Activity" --x 408 --y 464 --width 532 --height 232
p visuals sort "$P/openDeals.Visual" -f "$M.Open Pipeline" -d Descending
table_style "$P/openDeals.Visual" "Open Pipeline" 8.5
colour_col "$P/openDeals.Visual" "Stale Color" "Days Since Activity"
p add visual tableEx "$P" -n leaderboard -t "Rep leaderboard" -d "Values:Reps.Rep" -d "Values:$M.Won Revenue" -d "Values:$M.Quota Attainment" --x 956 --y 76 --width 300 --height 620
p visuals sort "$P/leaderboard.Visual" -f "$M.Won Revenue" -d Descending
table_style "$P/leaderboard.Visual" "Won Revenue" 9
colour_col "$P/leaderboard.Visual" "Attainment Color" "Quota Attainment"
info "$PG" infoTrend 612 212 "Revenue from deals closed won each month, against the same month last year (dashed)."
info "$PG" infoStage 940 212 "Value of open deals at each stage. Open pipeline ignores the date filter because these deals close in the future."
info "$PG" infoTeam 392 464 "Closed won revenue by sales team for the selected period."
info "$PG" infoOpen 940 464 "Open deals by value. Idle days in rose mean no activity for more than 21 days."
info "$PG" infoBoard 1256 76 "Reps ranked by won revenue. Attainment is won revenue against quota for the quarters started so far."

# ---------------------------------------------------------------- Funnel & Conversion
PG="Funnel & Conversion"; P="$R/$PG.Page"
kpi "$PG" Leads 92 279 "Leads" "Leads Label" "Leads Color" 1
kpi "$PG" Qual 387 279 "Qualification Rate" "Qualification Rate Label" "Qualification Rate Color" 1
kpi "$PG" L2W 682 279 "Lead to Win Rate" "Lead to Win Rate Label" "Lead to Win Rate Color" 1
kpi "$PG" Cycle 977 279 "Avg Sales Cycle" "Avg Sales Cycle Label" "Avg Sales Cycle Color" 1
kpi_style "$PG"
slicer "$PG" slTeam "Reps.Team" "Team" 956
slicer "$PG" slSegment "Accounts.Segment" "Segment" 1114
p add visual funnel "$P" -n stageFunnel -t "Deals reaching each stage" -d "Category:Stage History.Stage Reached" -d "Y:$M.Deals Reaching Stage" --x 92 --y 212 --width 380 --height 236
p add filter "Stage History" "Stage Reached" -v "$P/stageFunnel.Visual" --type Advanced --operator IsNot --values "Closed Lost"
p add visual clusteredBarChart "$P" -n winBySource -t "Win rate by lead source" -d "Category:Opportunities.Lead Source" -d "Y:$M.Win Rate" --x 488 --y 212 --width 380 --height 236
p visuals cf "$P/winBySource.Visual" --measure "dataPoint.fill $M.Win Rate Bar Color"
p visuals sort "$P/winBySource.Visual" -f "$M.Win Rate" -d Descending
bar_style "$P/winBySource.Visual"
p add visual clusteredBarChart "$P" -n lostReasons -t "Why deals are lost" -d "Category:Opportunities.Lost Reason" -d "Y:$M.Lost Deals" --x 884 --y 212 --width 372 --height 236
p visuals sort "$P/lostReasons.Visual" -f "$M.Lost Deals" -d Descending
bar_style "$P/lostReasons.Visual"
p add visual lineChart "$P" -n leadsTrend -t "Leads and qualified leads by month" -d "Category:Date.Month Start" -d "Y:$M.Leads" -d "Y:$M.Qualified Leads" --x 92 --y 464 --width 616 --height 232
line_style "$P/leadsTrend.Visual" ""
p add visual tableEx "$P" -n sourceTable -t "Lead source performance" -d "Values:Opportunities.Lead Source" -d "Values:$M.Won Revenue" -d "Values:$M.Won Deals" -d "Values:$M.Win Rate" -d "Values:$M.Avg Deal Size" -d "Values:$M.Avg Sales Cycle" --x 724 --y 464 --width 532 --height 232
p visuals sort "$P/sourceTable.Visual" -f "$M.Won Revenue" -d Descending
table_style "$P/sourceTable.Visual" "Won Revenue" 8.5
info "$PG" infoFunnel 472 212 "How many deals closed in the period reached each stage, ending with those won."
info "$PG" infoWin 868 212 "Won deals as a share of closed deals by lead source. Rose bars are below the overall win rate."
info "$PG" infoLost 1256 212 "Reasons recorded on closed lost deals."
info "$PG" infoLeads 708 464 "New leads created each month and how many of them were qualified."
info "$PG" infoSource 1256 464 "Closed won results by the lead source of the deal."

# ---------------------------------------------------------------- Rep Performance
PG="Rep Performance"; P="$R/$PG.Page"
kpi "$PG" Quota 92 279 "Quota Attainment" "Quota Label" "Attainment Color" 0
kpi "$PG" AtQuota 387 279 "Reps at Quota" "Reps at Quota Label" "Neutral Color" 0
kpi "$PG" Act 682 279 "Activities" "Activities Label" "Activities Color" 1
kpi "$PG" Weighted 977 279 "Weighted Pipeline" "Weighted Pipeline Label" "Neutral Color" 0
kpi_style "$PG"
slicer "$PG" slTeam "Reps.Team" "Team" 956
slicer "$PG" slSegment "Accounts.Segment" "Segment" 1114
p add visual tableEx "$P" -n repTable -t "Rep scorecard" -d "Values:Reps.Rep" -d "Values:Reps.Team" -d "Values:$M.Won Revenue" -d "Values:$M.Quota Attainment" -d "Values:$M.Won YoY" -d "Values:$M.Win Rate" -d "Values:$M.Open Pipeline" -d "Values:$M.Activities" --x 92 --y 212 --width 720 --height 484
p visuals sort "$P/repTable.Visual" -f "$M.Won Revenue" -d Descending
table_style "$P/repTable.Visual" "Won Revenue" 9
colour_col "$P/repTable.Visual" "Attainment Color" "Quota Attainment"
colour_col "$P/repTable.Visual" "Won Revenue Color" "Won YoY"
p add visual clusteredBarChart "$P" -n attainByTeam -t "Quota attainment by team" -d "Category:Reps.Team" -d "Y:$M.Quota Attainment" --x 828 --y 212 --width 428 --height 236
p visuals sort "$P/attainByTeam.Visual" -f "$M.Quota Attainment" -d Descending
bar_style "$P/attainByTeam.Visual"
p add visual clusteredBarChart "$P" -n actByType -t "Activities by type" -d "Category:Activities.Activity Type" -d "Y:$M.Activities" --x 828 --y 464 --width 428 --height 232
p visuals sort "$P/actByType.Visual" -f "$M.Activities" -d Descending
bar_style "$P/actByType.Visual"
info "$PG" infoReps 812 212 "One row per rep. Attainment is green at or above quota and rose below 80%."
info "$PG" infoAttain 1256 212 "Won revenue against quota for each team, for the quarters started so far."
info "$PG" infoAct 1256 464 "Logged calls, emails, meetings and demos in the selected period."

# ---------------------------------------------------------------- Deal Detail
PG="Deal Detail"; P="$R/$PG.Page"
kpi "$PG" Won 92 279 "Won Deals" "Won Deals Label" "Won Deals Color" 1
kpi "$PG" Open 387 279 "Open Deals" "Open Deals Label" "Neutral Color" 0
kpi "$PG" Pipe 682 279 "Open Pipeline" "Open Pipeline Label" "Neutral Color" 0
kpi "$PG" Stalled 977 279 "Stalled Deals" "Stalled Deals Label" "Warning Color" 0
kpi_style "$PG"
slicer "$PG" slStage "Stages.Stage" "Stage" 640
slicer "$PG" slSource "Opportunities.Lead Source" "Lead source" 798
slicer "$PG" slTeam "Reps.Team" "Team" 956
slicer "$PG" slSegment "Accounts.Segment" "Segment" 1114
p add visual tableEx "$P" -n dealTable -t "Deals" -d "Values:Opportunities.Opportunity" -d "Values:Accounts.Segment" -d "Values:Reps.Rep" -d "Values:Stages.Stage" -d "Values:Opportunities.Lead Source" -d "Values:Opportunities.Created Date" -d "Values:Opportunities.Close Date" -d "Values:$M.Deal Amount" --x 92 --y 212 --width 1164 --height 484
p visuals sort "$P/dealTable.Visual" -f "Opportunities.Close Date" -d Descending
table_style "$P/dealTable.Visual" "Deal Amount" 9
info "$PG" infoDeals 1256 212 "Every deal with a close date in the selected period, newest first. Use the slicers to narrow it down."

p fields rename "$R" "$M.Days Since Activity" "Idle days"
p fields rename "$R" "$M.Quota Attainment" "Attainment"
p fields rename "$R" "$M.Deal Amount" "Amount"
p pages active-page "$R" "Pipeline Overview"
pbir -q validate "$R" --fields 2>&1 | tail -3
