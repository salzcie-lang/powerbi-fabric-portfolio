#!/usr/bin/env bash
# Builds the Products, Customers and Order Detail pages of the Sales report with pbir.
# Run from 01_Sales-Analytics after the pages and their backgrounds exist. Re-running needs the visuals removed first.
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1 PBIR_ALLOW_OVERLAP=1
R="SalesAnalytics.Report"
M="_Measures"
p() { pbir -q "$@" 2>&1 | grep -i -E "error|not found|invalid|unknown" ; }

# kpi <page> <name> <x> <value measure> <label measure> <colour measure>   (card is 279 wide at y 76)
kpi() {
  local pg="$R/$1.Page" n=$2 x=$3
  p add visual cardVisual "$pg" -n "kpi${n}Value" -d "Data:$M.$4" --x $((x+10)) --y 110 --width 170 --height 52
  p add visual cardVisual "$pg" -n "kpi${n}Delta" -d "Data:$M.$5" --x $((x+10)) --y 156 --width 250 --height 38
  p visuals cf "$pg/kpi${n}Delta.Visual" --measure "value.fontColor $M.$6"
  p add visual lineChart "$pg" -n "kpi${n}Spark" -d "Category:Date.Month Start" -d "Y:$M.$4" --x $((x+190)) --y 118 --width 76 --height 36
}

kpi_style() {
  local pg="$R/$1.Page"
  for o in label accentBar; do p set "$pg/kpi*Value.Visual.$o.show" --value false -f; p set "$pg/kpi*Delta.Visual.$o.show" --value false -f; done
  for v in Value Delta; do p set "$pg/kpi*$v.Visual.layout.paddingUniform" --value 0 -f; p set "$pg/kpi*$v.Visual.cardCalloutArea.paddingUniform" --value 0 -f; p visuals padding "$pg/kpi*$v.Visual" --top 0 --bottom 0 --left 4 --right 0; done
  p set "$pg/kpi*Value.Visual.value.fontSize" --value 19 -f
  p set "$pg/kpi*Value.Visual.value.fontColor" --value "#1D1D1F" -f
  p set "$pg/kpi*Delta.Visual.value.fontSize" --value 9 -f
  for k in title categoryAxis valueAxis legend labels; do p set "$pg/kpi*Spark.Visual.$k.show" --value false -f; done
  p set "$pg/kpi*Spark.Visual.valueAxis.gridlineShow" --value false -f
  p set "$pg/kpi*Spark.Visual.lineStyles.strokeWidth" --value 2 -f
  p set "$pg/kpi*Spark.Visual.lineStyles.showMarker" --value false -f
  p set "$pg/kpi*Spark.Visual.lineStyles.lineChartType" --value smooth -f
  p set "$pg/kpi*Spark.Visual.lineStyles.areaShow" --value false -f
  for s in top bottom left right; do p set "$pg/kpi*Spark.Visual.padding.$s" --value 0 -f; done
}

# slicer <page> <name> <Table.Field> <heading> <pill x>
slicer() {
  local v="$R/$1.Page/$2.Visual"
  p add visual slicer "$R/$1.Page" -n "$2" -d "Values:$3" --x $(($5+4)) --y 11 --width 134 --height 54
  p set "$v.data.mode" --value Dropdown
  p visuals background "$v" --no-show; p visuals border "$v" --no-show
  p set "$v.header.show" --value true; p set "$v.header.text" --value "$4"; p set "$v.header.textSize" --value 8; p set "$v.header.fontColor" --value "#8A8FA3"
  for s in top:2 bottom:2 left:8 right:6; do p set "$v.padding.${s%%:*}" --value "${s##*:}"; done
}

# table_style <visual path> <bar field or ''> <yoy field or ''> <font size>
table_style() {
  local v=$1
  [ -n "$2" ] && p visuals cf "$v" --data-bars --field "$M.$2" --positive-color "#DADDF8"
  [ -n "$3" ] && p visuals cf "$v" --measure "values.fontColor $M.Revenue YoY Color" --target-field "$M.$3"
  p set "$v.total.totals" --value false
  p set "$v.values.fontSize" --value "$4"; p set "$v.columnHeaders.fontSize" --value 8.5
  p set "$v.columnHeaders.fontColor" --value "#8A8FA3"; p set "$v.columnHeaders.bold" --value false
  for k in fontColorPrimary fontColorSecondary; do p set "$v.values.$k" --value "#2B2F3A"; done
  for k in backColorPrimary backColorSecondary; do p set "$v.values.$k" --value "#FFFFFF"; done
  p set "$v.grid.gridHorizontal" --value true; p set "$v.grid.gridHorizontalColor" --value "#EEF0F6"
  p set "$v.grid.gridVertical" --value false; p set "$v.grid.rowPadding" --value 5
}

bar_style() { p set "$1.valueAxis.show" --value false; p set "$1.valueAxis.gridlineShow" --value false; }

# info <page> <name> <card x1> <card y0> <page id> <tooltip>
info() {
  local v="$R/$1.Page/$2.Visual"
  p add visual actionButton "$R/$1.Page" -n "$2" --x $(($3-30)) --y $(($4+10)) --width 20 --height 20
  p visuals action "$v" --type PageNavigation --target "$5" --tooltip "$6"
  for o in fill outline text icon; do p set "$v.$o.show" --value false; done
}

# ---------------------------------------------------------------- Products & Margin
PG="Products & Margin"; ID=bbf49c3761620347; P="$R/$PG.Page"
kpi "$PG" Profit 92 "Gross Profit" "Gross Profit Label" "Gross Profit Color"
kpi "$PG" Margin 387 "Gross Margin %" "Margin Label" "Margin Color"
kpi "$PG" Discount 682 "Discount %" "Discount % Label" "Discount % Color"
kpi "$PG" Units 977 "Units" "Units Label" "Units Color"
kpi_style "$PG"
slicer "$PG" slRegion "Regions.Region" "Region" 956
slicer "$PG" slSegment "Customers.Segment" "Segment" 1114
p add visual clusteredBarChart "$P" -n marginByCategory -t "Gross margin % by category" -d "Category:Products.Category" -d "Y:$M.Gross Margin %" --x 92 --y 212 --width 340 --height 236
p visuals cf "$P/marginByCategory.Visual" --measure "dataPoint.fill $M.Margin Bar Color"
p visuals sort "$P/marginByCategory.Visual" -f "$M.Gross Margin %" -d Descending
bar_style "$P/marginByCategory.Visual"
p add visual pivotTable "$P" -n marginHeat -t "Gross margin % by category and region" -d "Rows:Products.Category" -d "Columns:Regions.Region" -d "Values:$M.Gross Margin %" --x 448 --y 212 --width 808 --height 236
p visuals cf "$P/marginHeat.Visual" --gradient --field "$M.Gross Margin %" --min-color "#F9C4CD" --mid-color "#FFFFFF" --max-color "#C5CAF4" --on values.backColor
p add visual lineChart "$P" -n marginTrend -t "Gross margin % by month, this year vs last" -d "Category:Date.Month Start" -d "Y:$M.Gross Margin %" -d "Y:$M.Gross Margin % PY" --x 92 --y 464 --width 520 --height 232
p set "$P/marginTrend.Visual.lineStyles.showMarker" --value false; p set "$P/marginTrend.Visual.lineStyles.lineChartType" --value smooth
p set "$P/marginTrend.Visual.lineStyles.strokeWidth" --value 3; p set "$P/marginTrend.Visual.lineStyles.areaShow" --value false
p set "$P/marginTrend.Visual.lineStyles.field($M.Gross Margin % PY).lineStyle" --value dashed
p set "$P/marginTrend.Visual.lineStyles.field($M.Gross Margin % PY).strokeWidth" --value 2
p set "$P/marginTrend.Visual.dataPoint.field($M.Gross Margin % PY).fill" --value "#8A8FA3"
p add visual tableEx "$P" -n productTable -t "Products by revenue" -d "Values:Products.Product" -d "Values:Products.Category" -d "Values:$M.Revenue" -d "Values:$M.Gross Margin %" -d "Values:$M.Discount %" -d "Values:$M.YoY" --x 628 --y 464 --width 628 --height 232
p visuals sort "$P/productTable.Visual" -f "$M.Revenue" -d Descending
table_style "$P/productTable.Visual" "Revenue" "YoY" 8.5
info "$PG" infoMarginCat 432 212 $ID "Gross margin by category. Rose bars are below the overall margin for the current selection."
info "$PG" infoHeat 1256 212 $ID "Margin by category and region. Rose cells are the weakest combinations and show where discounting is eroding margin."
info "$PG" infoTrend 612 464 $ID "Monthly gross margin this year against the same month last year (dashed)."
info "$PG" infoProducts 1256 464 $ID "Products ranked by revenue with margin, average discount and change against last year."

# ---------------------------------------------------------------- Customers & Reps
PG="Customers & Reps"; ID=5bc49ee982c18b89; P="$R/$PG.Page"
kpi "$PG" Active 92 "Active Customers" "Active Customers Label" "Active Customers Color"
kpi "$PG" New 387 "New Customers" "New Customers Label" "Neutral Color"
kpi "$PG" PerCust 682 "Revenue per Customer" "Revenue per Customer Label" "Revenue per Customer Color"
kpi "$PG" Orders 977 "Orders" "Orders Label" "Orders YoY Color"
kpi_style "$PG"
slicer "$PG" slRegion "Regions.Region" "Region" 956
slicer "$PG" slSegment "Customers.Segment" "Segment" 1114
p add visual barChart "$P" -n bySegment -t "Revenue by segment and channel" -d "Category:Customers.Segment" -d "Y:$M.Revenue" -d "Series:Orders.Channel" --x 92 --y 212 --width 380 --height 236
bar_style "$P/bySegment.Visual"
p add visual clusteredBarChart "$P" -n byIndustry -t "Revenue by industry" -d "Category:Customers.Industry" -d "Y:$M.Revenue" --x 488 --y 212 --width 380 --height 236
p visuals sort "$P/byIndustry.Visual" -f "$M.Revenue" -d Descending
bar_style "$P/byIndustry.Visual"
p add visual clusteredBarChart "$P" -n byCountry -t "Top countries by revenue" -d "Category:Customers.Country" -d "Y:$M.Revenue" --x 884 --y 212 --width 372 --height 236
p visuals sort "$P/byCountry.Visual" -f "$M.Revenue" -d Descending
p add filter Customers Country -v "$P/byCountry.Visual" --type TopN --n 7 --by-table "$M" --by-field Revenue
bar_style "$P/byCountry.Visual"
p add visual tableEx "$P" -n repTable -t "Sales rep leaderboard" -d "Values:Sales Reps.Sales Rep" -d "Values:$M.Revenue" -d "Values:$M.YoY" -d "Values:$M.Orders" -d "Values:$M.Avg Order Value" -d "Values:$M.Gross Margin %" --x 92 --y 464 --width 616 --height 232
p visuals sort "$P/repTable.Visual" -f "$M.Revenue" -d Descending
table_style "$P/repTable.Visual" "Revenue" "YoY" 8.5
p add visual tableEx "$P" -n declineTable -t "Accounts in decline" -d "Values:Customers.Customer" -d "Values:Customers.Segment" -d "Values:$M.Revenue" -d "Values:$M.Revenue PY" -d "Values:$M.Revenue YoY Sort" --x 724 --y 464 --width 532 --height 232
p visuals sort "$P/declineTable.Visual" -f "$M.Revenue YoY Sort" -d Ascending
table_style "$P/declineTable.Visual" "" "Revenue YoY Sort" 8.5
p add filter Customers Customer -v "$P/declineTable.Visual" --type TopN --n 30 --by-table "$M" --by-field "Revenue PY"
info "$PG" infoSegment 472 212 $ID "Revenue by customer segment, split by sales channel."
info "$PG" infoIndustry 868 212 $ID "Revenue by customer industry for the current selection."
info "$PG" infoCountry 1256 212 $ID "The seven countries with the highest revenue."
info "$PG" infoReps 708 464 $ID "Sales reps ranked by revenue, with change against the same period last year."
info "$PG" infoDecline 1256 464 $ID "Among the 30 largest accounts last year, those with the steepest revenue decline come first."

# ---------------------------------------------------------------- Order Detail
PG="Order Detail"; ID=b08f34609bad5bb7; P="$R/$PG.Page"
kpi "$PG" Orders 92 "Orders" "Orders Label" "Orders YoY Color"
kpi "$PG" Units 387 "Units" "Units Label" "Units Color"
kpi "$PG" Revenue 682 "Revenue" "Revenue YoY Label" "Revenue YoY Color"
kpi "$PG" Discount 977 "Discount %" "Discount % Label" "Discount % Color"
kpi_style "$PG"
slicer "$PG" slCategory "Products.Category" "Category" 640
slicer "$PG" slChannel "Orders.Channel" "Channel" 798
slicer "$PG" slRegion "Regions.Region" "Region" 956
slicer "$PG" slSegment "Customers.Segment" "Segment" 1114
p add visual tableEx "$P" -n orderTable -t "Order lines" -d "Values:Orders.Order ID" -d "Values:Orders.Order Date" -d "Values:Customers.Customer" -d "Values:Products.Product" -d "Values:Products.Category" -d "Values:Orders.Channel" -d "Values:Sales Reps.Sales Rep" -d "Values:$M.Units" -d "Values:$M.Revenue" -d "Values:$M.Discount %" -d "Values:$M.Gross Margin %" --x 92 --y 212 --width 1164 --height 484
p visuals sort "$P/orderTable.Visual" -f "Orders.Order Date" -d Descending
table_style "$P/orderTable.Visual" "Revenue" "" 9
info "$PG" infoOrders 1256 212 $ID "Every order line for the current selection, newest first. Use the slicers above to narrow it down."

pbir -q validate "$R" --fields 2>&1 | tail -3
