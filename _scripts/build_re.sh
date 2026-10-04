#!/usr/bin/env bash
# Builds the Real Estate report (warm light theme, map-first layout, bottom dock navigation).
# Run from 03_Real-Estate once RealEstate.Report exists, is bound to the local model and pbir is connected to it.
R="RealEstate.Report"; M="_Measures"
INK="#1F2A24"; TEXT="#2B332E"; MUTED="#8C8676"; GRID="#EFE9DD"; CARD="#FFFDF8"; BAR="#DCE9E0"
source "$(dirname "$0")/pbir_lib.sh"
c() { echo "{\"solid\": {\"color\": \"$1\"}}"; }

# ---------------------------------------------------------------- theme (warm light, serif titles)
p theme set-colors "$R" --data-colors '["#2F6B4F","#C9C0AE","#8DBBA3","#D9A066","#7A93B8","#B98FA6","#9AB8C9","#8C8676"]' --good "#3E9B6E" --bad "#D9735B" --neutral "$MUTED" --foreground "$INK" --background "$CARD"
p theme set-fonts "$R" title --font-face "Georgia" --font-size 11 --color "$INK"
p theme set-fonts "$R" label --font-face "Segoe UI" --font-size 9 --color "$MUTED"
p theme set-fonts "$R" callout --font-face "Segoe UI Semibold" --font-size 24 --color "$INK"
p theme set-formatting "$R" "*.*.title.fontFamily" --value "Georgia"
p theme set-formatting "$R" "*.*.title.bold" --value true
p theme set-formatting "$R" "*.*.title.fontColor" --json "$(c $INK)"
for ax in categoryAxis valueAxis; do p theme set-formatting "$R" "*.*.$ax.labelColor" --json "$(c $MUTED)"; p theme set-formatting "$R" "*.*.$ax.gridlineColor" --json "$(c $GRID)"; done
p theme set-formatting "$R" "*.*.labels.color" --json "$(c '#5E5A4E')"
p theme set-formatting "$R" "*.*.legend.labelColor" --json "$(c $MUTED)"

# ---------------------------------------------------------------- pages
PAGES=("Portfolio" "Occupancy & Leasing" "Collections & NOI" "Property Detail"); KEYS=(portfolio occupancy collections property)
p pages rename "$R/Page 1.Page" --to "Portfolio" -f
for i in 1 2 3; do p add page "$R/p$i.Page" -n "${PAGES[$i]}"; p rm "$R/${PAGES[$i]}.Page/Title.Visual" -f; done
for i in 0 1 2 3; do p pages background "$R/${PAGES[$i]}.Page" --image "assets/bg_${KEYS[$i]}.png" --scaling Fit --transparency 0; done
p add filter Date "Fiscal Year" -r "$R" --values "FY 2026"

# dock navigation: invisible buttons over the four dock icons on every page
DOCK_X=(532 604 676 748)
for i in 0 1 2 3; do for j in 0 1 2 3; do
  [ $i = $j ] && continue
  v="$R/${PAGES[$i]}.Page/nav$j.Visual"
  p add visual actionButton "$R/${PAGES[$i]}.Page" -n "nav$j" --x $((DOCK_X[$j]-22)) --y 667 --width 44 --height 34
  p visuals action "$v" --type PageNavigation --target "$(page_id "${PAGES[$j]}")" --tooltip "${PAGES[$j]}"
  for o in fill outline text icon; do p set "$v.$o.show" --value false; done
done; done

# tile <page> <name> <x> <y> <value> <label> <colour>: KPI tile (about 292 x 96) with the delta to the right of the value
tile() {
  local pg="$R/$1.Page"
  p add visual cardVisual "$pg" -n "kpi$2Value" -d "Data:$M.$5" --x $(($3+10)) --y $(($4+40)) --width 150 --height 52
  p add visual cardVisual "$pg" -n "kpi$2Delta" -d "Data:$M.$6" --x $(($3+12)) --y $(($4+34)) --width 10 --height 10
  p visuals position "$pg/kpi$2Delta.Visual" --x $(($3+150)) --y $(($4+52)) --width 138 --height 38
  p visuals cf "$pg/kpi$2Delta.Visual" --measure "value.fontColor $M.$7"
}
tile_style() {
  local pg="$R/$1.Page"
  for v in Value Delta; do
    for o in label accentBar; do p set "$pg/kpi*$v.Visual.$o.show" --value false -f; done
    p set "$pg/kpi*$v.Visual.layout.paddingUniform" --value 0 -f
    p set "$pg/kpi*$v.Visual.cardCalloutArea.paddingUniform" --value 0 -f
    p visuals padding "$pg/kpi*$v.Visual" --top 0 --bottom 0 --left 4 --right 0
  done
  p set "$pg/kpi*Value.Visual.value.fontSize" --value 20 -f
  p set "$pg/kpi*Value.Visual.value.fontColor" --value "$INK" -f
  p set "$pg/kpi*Value.Visual.value.labelPrecision" --value 1 -f
  p set "$pg/kpi*Delta.Visual.value.fontSize" --value 8.5 -f
}
slicer_light() {  # same pill slicer as the other reports, minus the dropdown box
  slicer "$@"
  local v="$R/$1.Page/$2.Visual"
  p set "$v.general.outlineColor" --value "$CARD"; p set "$v.items.accessibilityContrastProperties" --value false; p set "$v.items.outlineStyle" --value 0
}
tbl() {  # tbl <visual> <bar measure or ''> <font size> [image height]
  table_style "$1" "$2" "$3"
  p set "$1.columnHeaders.alignment" --value Auto
  p set "$1.grid.outlineColor" --value "$GRID"; p set "$1.columnHeaders.outlineColor" --value "$GRID"; p set "$1.values.outlineColor" --value "$GRID"
  [ -n "$4" ] && p set "$1.grid.imageHeight" --value "$4"
  p visuals table-density "$1" --stretch-columns
}

# ---------------------------------------------------------------- Portfolio (map first)
PG="Portfolio"; P="$R/$PG.Page"
tile "$PG" Value 656 76 "Portfolio Value" "Portfolio Value Label" "Good Color"
tile "$PG" Occ 964 76 "Occupancy %" "Occupancy % Label" "Occupancy % Color"
tile "$PG" NOI 656 188 "NOI" "NOI Label" "NOI Color"
tile "$PG" Coll 964 188 "Collection Rate" "Collection Rate Label" "Collection Rate Color"
tile_style "$PG"
slicer_light "$PG" slType "Property Types.Property Type" "Property type" 956
slicer_light "$PG" slCity "Properties.City" "City" 1114
# clickable city bubbles on top of the dotted map drawn in the background (same 0-100 coordinate space)
p add visual scatterChart "$P" -n cityMap -d "Category:Properties.City" -d "X:$M.Map X" -d "Y:$M.Map Y" -d "Size:$M.Units" --x 44 --y 124 --width 576 --height 320
MAP="$P/cityMap.Visual"
for k in title legend categoryLabels; do p set "$MAP.$k.show" --value false; done
for ax in categoryAxis valueAxis; do p set "$MAP.$ax.show" --value false; p set "$MAP.$ax.gridlineShow" --value false; p set "$MAP.$ax.start" --value 0; p set "$MAP.$ax.end" --value 100; done
for s in top bottom left right; do p set "$MAP.padding.$s" --value 0; done
p set "$MAP.bubbles.bubbleSize" --value 25
p visuals cf "$MAP" --measure "dataPoint.fill $M.Occupancy Color"
p add visual tableEx "$P" -n cityTable -d "Values:Properties.City" -d "Values:$M.Units" -d "Values:$M.Occupancy Bar" -d "Values:$M.Occupancy %" -d "Values:$M.Portfolio Value" -d "Values:$M.NOI" --x 40 --y 452 --width 584 --height 186
p visuals title "$P/cityTable.Visual" --no-show
p visuals sort "$P/cityTable.Visual" -f "$M.Portfolio Value" -d Descending
tbl "$P/cityTable.Visual" "Portfolio Value" 9 16
colour_col "$P/cityTable.Visual" "Occupancy Text Color" "Occupancy %"
p add visual tableEx "$P" -n propTable -t "Properties" -d "Values:Property Types.Picture" -d "Values:Properties.Property" -d "Values:Properties.City" -d "Values:$M.Units" -d "Values:$M.Occupancy Bar" -d "Values:$M.Occupancy %" -d "Values:$M.NOI" -d "Values:$M.Collection Rate" --x 656 --y 300 --width 600 --height 348
p visuals sort "$P/propTable.Visual" -f "$M.NOI" -d Descending
tbl "$P/propTable.Visual" "NOI" 9 30
colour_col "$P/propTable.Visual" "Occupancy Text Color" "Occupancy %"
colour_col "$P/propTable.Visual" "Collection Text Color" "Collection Rate"
info "$PG" infoMap 640 76 "Each bubble is a city: size is the number of units, colour turns terracotta when occupancy is under 90%. Click a bubble to filter the page."
info "$PG" infoProps 1256 300 "Every property with its type, occupancy on the snapshot date, net operating income and collection rate."
info "$PG" infoValue 948 76 "Current appraised value of the portfolio against its purchase price."
info "$PG" infoOcc 1256 76 "Share of units with an active lease on the last day of the selected period."
info "$PG" infoNOI 948 188 "Rent collected less operating expenses."
info "$PG" infoColl 1256 188 "Rent collected as a share of rent due."

# ---------------------------------------------------------------- Occupancy & Leasing
PG="Occupancy & Leasing"; P="$R/$PG.Page"
tile "$PG" Occ 24 76 "Occupancy %" "Occupancy % Label" "Occupancy % Color"
tile "$PG" Vacant 336 76 "Vacant Units" "Vacant Units Label" "Neutral Color"
tile "$PG" Rent 648 76 "Avg Rent per Unit" "Avg Rent per Unit Label" "Neutral Color"
tile "$PG" Exp 960 76 "Expiring Leases" "Expiring Leases Label" "Warning Color"
tile_style "$PG"
slicer_light "$PG" slType "Property Types.Property Type" "Property type" 956
slicer_light "$PG" slCity "Properties.City" "City" 1114
p visuals position "$P/slType.Visual" --y 10; p visuals position "$P/slCity.Visual" --y 10
p add visual tableEx "$P" -n typeTiles -t "Property types" -d "Values:Property Types.Picture" -d "Values:Property Types.Property Type" -d "Values:$M.Occupancy %" -d "Values:$M.Units" --x 24 --y 188 --width 296 --height 460
tbl "$P/typeTiles.Visual" "" 9.5 72
colour_col "$P/typeTiles.Visual" "Occupancy Text Color" "Occupancy %"
p add visual lineChart "$P" -n occTrend -t "Occupancy by month, this year vs last" -d "Category:Date.Month Start" -d "Y:$M.Occupancy %" -d "Y:$M.Occupancy % PY" --x 336 --y 188 --width 608 --height 224
line_style "$P/occTrend.Visual" "Occupancy % PY"
p set "$P/occTrend.Visual.lineStyles.areaShow" --value false
p add visual clusteredBarChart "$P" -n vacantByCity -t "Vacant units by city" -d "Category:Properties.City" -d "Y:$M.Vacant Units" --x 960 --y 188 --width 296 --height 224
p visuals sort "$P/vacantByCity.Visual" -f "$M.Vacant Units" -d Descending
bar_style "$P/vacantByCity.Visual"; p set "$P/vacantByCity.Visual.categoryAxis.innerPadding" --value 45
p add visual tableEx "$P" -n expiring -t "Leases ending in the next 90 days" -d "Values:Leases.Tenant" -d "Values:Properties.Property" -d "Values:Units.Unit Type" -d "Values:Leases.End Date" -d "Values:$M.Expiring Rent" --x 336 --y 428 --width 920 --height 220
p visuals sort "$P/expiring.Visual" -f "Leases.End Date" -d Ascending
tbl "$P/expiring.Visual" "Expiring Rent" 9
info "$PG" infoTypes 320 188 "Click a picture to filter the page to one property type."
info "$PG" infoTrend 944 188 "Share of units with an active lease at each month end, against the same month last year (dashed)."
info "$PG" infoVacant 1256 188 "Units without an active lease on the snapshot date."
info "$PG" infoExp 1256 428 "Active leases that end within 90 days, soonest first, with the monthly rent at risk."

# ---------------------------------------------------------------- Collections & NOI
PG="Collections & NOI"; P="$R/$PG.Page"
tile "$PG" Coll 24 76 "Rent Collected" "Rent Collected Label" "Rent Collected Color"
tile "$PG" Out 336 76 "Outstanding Rent" "Outstanding Rent Label" "Warning Color"
tile "$PG" NOI 648 76 "NOI" "NOI Label" "NOI Color"
tile "$PG" Margin 960 76 "NOI Margin" "NOI Margin Label" "NOI Margin Color"
tile_style "$PG"
slicer_light "$PG" slType "Property Types.Property Type" "Property type" 956
slicer_light "$PG" slCity "Properties.City" "City" 1114
p add visual lineChart "$P" -n dueTrend -t "Rent collected against rent due, monthly" -d "Category:Date.Month Start" -d "Y:$M.Rent Collected" -d "Y:$M.Rent Due" --x 24 --y 188 --width 616 --height 242
line_style "$P/dueTrend.Visual" "Rent Due"
p set "$P/dueTrend.Visual.lineStyles.areaShow" --value false
p add visual clusteredBarChart "$P" -n statusBar -t "Payments by status" -d "Category:Rent Payments.Payment Status" -d "Y:$M.Payments" --x 656 --y 188 --width 292 --height 242
p visuals sort "$P/statusBar.Visual" -f "$M.Payments" -d Descending
bar_style "$P/statusBar.Visual"; p set "$P/statusBar.Visual.categoryAxis.innerPadding" --value 45
p add visual clusteredBarChart "$P" -n expBar -t "Operating expenses by category" -d "Category:Operating Expenses.Expense Category" -d "Y:$M.Operating Expenses Total" --x 964 --y 188 --width 292 --height 242
p visuals sort "$P/expBar.Visual" -f "$M.Operating Expenses Total" -d Descending
bar_style "$P/expBar.Visual"; p set "$P/expBar.Visual.categoryAxis.innerPadding" --value 40
p add visual tableEx "$P" -n noiTable -t "Net operating income by property" -d "Values:Property Types.Picture" -d "Values:Properties.Property" -d "Values:Properties.City" -d "Values:$M.Rent Collected" -d "Values:$M.Collection Bar" -d "Values:$M.Collection Rate" -d "Values:$M.Operating Expenses Total" -d "Values:$M.NOI" -d "Values:$M.NOI Margin" --x 24 --y 446 --width 1232 --height 202
p visuals sort "$P/noiTable.Visual" -f "$M.NOI" -d Descending
tbl "$P/noiTable.Visual" "Rent Collected" 9 24
colour_col "$P/noiTable.Visual" "Collection Text Color" "Collection Rate"
info "$PG" infoDue 640 188 "Rent received each month against the rent that fell due (dashed)."
info "$PG" infoStatus 948 188 "Number of monthly rent payments by how they were paid."
info "$PG" infoExp 1256 188 "Operating expenses for the selected period by category."
info "$PG" infoNoi 1256 446 "Rent collected, collection rate, operating expenses and NOI for each property."

# ---------------------------------------------------------------- Property Detail
PG="Property Detail"; P="$R/$PG.Page"
tile "$PG" Occ 336 76 "Occupancy %" "Occupancy % Label" "Occupancy % Color"
tile "$PG" NOI 648 76 "NOI" "NOI Label" "NOI Color"
tile "$PG" Open 960 76 "Open Requests" "Open Requests Label" "Neutral Color"
tile_style "$PG"
p add visual tableEx "$P" -n heroPicture -d "Values:Property Types.Picture" -d "Values:Property Types.Property Type" -d "Values:$M.Properties" --x 36 --y 84 --width 272 --height 150
p visuals title "$P/heroPicture.Visual" --no-show
tbl "$P/heroPicture.Visual" "" 9 30
p add visual slicer "$P" -n propSlicer -d "Values:Properties.Property" --x 36 --y 240 --width 272 --height 398
SV="$P/propSlicer.Visual"
p visuals background "$SV" --no-show; p visuals border "$SV" --no-show
p set "$SV.header.show" --value true; p set "$SV.header.text" --value "Choose a property"; p set "$SV.header.fontColor" --value "$MUTED"; p set "$SV.header.textSize" --value 8.5
p set "$SV.items.fontColor" --value "$TEXT"; p set "$SV.items.background" --value "$CARD"; p set "$SV.items.textSize" --value 9
p set "$SV.selection.singleSelect" --value true
p add visual tableEx "$P" -n unitTable -t "Units by type" -d "Values:Units.Unit Type" -d "Values:$M.Units" -d "Values:$M.Occupied Units" -d "Values:$M.Occupancy Bar" -d "Values:$M.Occupancy %" -d "Values:$M.Rent Roll" -d "Values:$M.Avg Rent per Unit" --x 336 --y 188 --width 608 --height 220
tbl "$P/unitTable.Visual" "Rent Roll" 9.5 16
p add visual lineChart "$P" -n propTrend -t "Rent collected and NOI by month" -d "Category:Date.Month Start" -d "Y:$M.Rent Collected" -d "Y:$M.NOI" --x 336 --y 416 --width 608 --height 232
line_style "$P/propTrend.Visual" ""
p set "$P/propTrend.Visual.lineStyles.areaShow" --value false
p add visual clusteredBarChart "$P" -n maintBar -t "Maintenance requests by category" -d "Category:Maintenance Requests.Category" -d "Y:$M.Requests" --x 960 --y 188 --width 296 --height 460
p visuals sort "$P/maintBar.Visual" -f "$M.Requests" -d Descending
bar_style "$P/maintBar.Visual"; p set "$P/maintBar.Visual.categoryAxis.innerPadding" --value 45
info "$PG" infoPick 320 76 "Pick one property to see its occupancy, income and maintenance."
info "$PG" infoUnits 944 188 "Units, occupancy and contracted rent by unit type, with monthly rent collected and NOI below."
info "$PG" infoMaint 1256 188 "Maintenance requests opened in the selected period by category."

p fields rename "$R" "Property Types.Picture" " "
p fields rename "$R" "$M.Occupancy Bar" "Occupancy"
p fields rename "$R" "$M.Occupancy %" "Occ. %"
p fields rename "$R" "$M.Collection Bar" "Collection"
p fields rename "$R" "$M.Collection Rate" "Coll. %"
p fields rename "$R" "$M.Operating Expenses Total" "Operating expenses"
p fields rename "$R" "$M.Expiring Rent" "Monthly rent"
p pages active-page "$R" "Portfolio"
pbir -q validate "$R" --fields 2>&1 | tail -3
