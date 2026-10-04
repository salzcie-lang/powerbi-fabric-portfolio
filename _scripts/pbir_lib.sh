#!/usr/bin/env bash
# Shared pbir helpers for the portfolio dashboards. Source this after setting:
#   R (report path), M (measure table), INK, TEXT, MUTED, GRID, CARD, BAR (hex colours)
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1 PBIR_ALLOW_OVERLAP=1
p() { pbir -q "$@" 2>&1 | grep -i -E "error|not found|invalid|unknown|no property" ; }

# page_id <display name> -> internal page id (needed as the target of navigation buttons)
page_id() {
  python - "$R" "$1" <<'PY'
import json, pathlib, sys
for f in pathlib.Path(sys.argv[1], "definition", "pages").glob("*/page.json"):
    j = json.loads(f.read_text(encoding="utf-8"))
    if j["displayName"] == sys.argv[2]:
        print(j["name"])
PY
}

# kpi <page> <name> <x> <card width 200|279> <value> <label> <colour> <spark 1|0>
kpi() {
  local pg="$R/$1.Page" n=$2 x=$3 vw=118 dw=170 sx=126 sw=64
  [ "$4" = 279 ] && { vw=170; dw=250; sx=190; sw=76; }
  p add visual cardVisual "$pg" -n "kpi${n}Value" -d "Data:$M.$5" --x $((x+10)) --y 110 --width $vw --height 52
  p add visual cardVisual "$pg" -n "kpi${n}Delta" -d "Data:$M.$6" --x $((x+10)) --y 156 --width $dw --height 38
  p visuals cf "$pg/kpi${n}Delta.Visual" --measure "value.fontColor $M.$7"
  [ "$8" = 1 ] && p add visual lineChart "$pg" -n "kpi${n}Spark" -d "Category:Date.Month Start" -d "Y:$M.$5" --x $((x+sx)) --y 118 --width $sw --height 36
}

kpi_style() {
  local pg="$R/$1.Page"
  for v in Value Delta; do
    for o in label accentBar; do p set "$pg/kpi*$v.Visual.$o.show" --value false -f; done
    p set "$pg/kpi*$v.Visual.layout.paddingUniform" --value 0 -f
    p set "$pg/kpi*$v.Visual.cardCalloutArea.paddingUniform" --value 0 -f
    p visuals padding "$pg/kpi*$v.Visual" --top 0 --bottom 0 --left 4 --right 0
  done
  p set "$pg/kpi*Value.Visual.value.fontSize" --value 19 -f
  p set "$pg/kpi*Value.Visual.value.fontColor" --value "$INK" -f
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
  p set "$v.header.show" --value true; p set "$v.header.text" --value "$4"; p set "$v.header.textSize" --value 8; p set "$v.header.fontColor" --value "$MUTED"
  p set "$v.items.fontColor" --value "$TEXT"; p set "$v.items.background" --value "$CARD"
  for s in top:2 bottom:2 left:8 right:6; do p set "$v.padding.${s%%:*}" --value "${s##*:}"; done
}

# table_style <visual path> <data bar measure or ''> <font size>
table_style() {
  local v=$1
  [ -n "$2" ] && p visuals cf "$v" --data-bars --field "$M.$2" --positive-color "$BAR"
  p set "$v.total.totals" --value false
  p set "$v.values.fontSize" --value "$3"; p set "$v.columnHeaders.fontSize" --value 8.5
  p set "$v.columnHeaders.fontColor" --value "$MUTED"; p set "$v.columnHeaders.bold" --value false; p set "$v.columnHeaders.backColor" --value "$CARD"
  for k in fontColorPrimary fontColorSecondary; do p set "$v.values.$k" --value "$TEXT"; done
  for k in backColorPrimary backColorSecondary; do p set "$v.values.$k" --value "$CARD"; done
  p set "$v.grid.gridHorizontal" --value true; p set "$v.grid.gridHorizontalColor" --value "$GRID"
  p set "$v.grid.gridVertical" --value false; p set "$v.grid.rowPadding" --value 5
}

# colour_col <visual path> <colour measure> <column measure>: font colour of one table column by measure
colour_col() { p visuals cf "$1" --measure "values.fontColor $M.$2" --target-field "$M.$3"; }

bar_style() { p set "$1.valueAxis.show" --value false; p set "$1.valueAxis.gridlineShow" --value false; }

# line_style <visual path> <dashed comparison measure or ''>
line_style() {
  p set "$1.lineStyles.showMarker" --value false; p set "$1.lineStyles.lineChartType" --value smooth
  p set "$1.lineStyles.strokeWidth" --value 3
  if [ -n "$2" ]; then
    p set "$1.lineStyles.field($M.$2).lineStyle" --value dashed
    p set "$1.lineStyles.field($M.$2).strokeWidth" --value 2
    p set "$1.lineStyles.field($M.$2).areaShow" --value false
    p set "$1.dataPoint.field($M.$2).fill" --value "$MUTED"
  fi
}

# info <page> <name> <card x1> <card y0> <tooltip>: invisible button over the drawn (i) marker
info() {
  local v="$R/$1.Page/$2.Visual"
  p add visual actionButton "$R/$1.Page" -n "$2" --x $(($3-30)) --y $(($4+10)) --width 20 --height 20
  p visuals action "$v" --type PageNavigation --target "$(page_id "$1")" --tooltip "$5"
  for o in fill outline text icon; do p set "$v.$o.show" --value false; done
}

# nav <page 1> <page 2> <page 3> <page 4>: invisible buttons over the rail icons on every page
nav() {
  local names=("$@") i j
  for i in 0 1 2 3; do for j in 0 1 2 3; do
    [ $i = $j ] && continue
    local v="$R/${names[$i]}.Page/nav$j.Visual"
    p add visual actionButton "$R/${names[$i]}.Page" -n "nav$j" --x 27 --y $((91 + j*50)) --width 34 --height 34
    p visuals action "$v" --type PageNavigation --target "$(page_id "${names[$j]}")" --tooltip "${names[$j]}"
    for o in fill outline text icon; do p set "$v.$o.show" --value false; done
  done; done
}
