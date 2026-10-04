#!/usr/bin/env bash
# Rebuilds the Real Estate report in its editorial split-screen design (see make_background_re.py):
# full-height stage on the left (Azure map or photo), typeset column on the right, no cards.
# Run from 03_Real-Estate after build_re.sh.
R="RealEstate.Report"; M="_Measures"
INK="#1B221E"; TEXT="#2B332E"; MUTED="#8A8578"; GRID="#E6E0D4"; CARD="#FBFAF7"; BAR="#DCE9E0"; STAGE="#EFEAE1"
source "$(dirname "$0")/pbir_lib.sh"
pos() { p visuals position "$R/$1.Page/$2.Visual" --x "$3" --y "$4" --width "$5" --height "$6"; }
inf() { pos "$1" "$2" $(($3+$5-18)) $(($4+4)) 20 20; }   # inf <page> <button> <block x> <block y> <block w>
PAGES=("Portfolio" "Occupancy & Leasing" "Collections & NOI" "Property Detail"); KEYS=(portfolio occupancy collections property)
NAV_X=(912 996 1080 1164); KPI_X=(560 732 904 1076)
declare -A KPIS=( ["Portfolio"]="Value Occ NOI Coll" ["Occupancy & Leasing"]="Occ Vacant Rent Exp"
                  ["Collections & NOI"]="Coll Out NOI Margin" ["Property Detail"]="Occ NOI Rent Open" )

tbl() {  # tbl <visual> <bar measure or ''> <font size> <background> [image height] [image width]
  CARD="$4" table_style "$1" "$2" "$3"
  p set "$1.columnHeaders.alignment" --value Auto
  p set "$1.grid.outlineColor" --value "$GRID"; p set "$1.columnHeaders.outlineColor" --value "$GRID"; p set "$1.values.outlineColor" --value "$GRID"
  p visuals title "$1" --no-show
  if [ -n "$5" ]; then p visuals table-density "$1" --image-height "$5" --image-width "$6" --stretch-columns; else p visuals table-density "$1" --stretch-columns; fi
}

# a fourth KPI on Property Detail
PD="$R/Property Detail.Page"
p add visual cardVisual "$PD" -n kpiRentValue -d "Data:$M.Avg Rent per Unit" --x 904 --y 148 --width 164 --height 44
p add visual cardVisual "$PD" -n kpiRentDelta -d "Data:$M.Avg Rent per Unit Label" --x 904 --y 186 --width 168 --height 36
p visuals cf "$PD/kpiRentDelta.Visual" --measure "value.fontColor $M.Neutral Color"
for v in Value Delta; do
  for o in label accentBar; do p set "$PD/kpiRent$v.Visual.$o.show" --value false; done
  p set "$PD/kpiRent$v.Visual.layout.paddingUniform" --value 0; p set "$PD/kpiRent$v.Visual.cardCalloutArea.paddingUniform" --value 0
  p visuals padding "$PD/kpiRent$v.Visual" --top 0 --bottom 0 --left 4 --right 0
done
p set "$PD/kpiRentValue.Visual.value.labelDisplayUnits" --value 1; p set "$PD/kpiRentValue.Visual.value.labelPrecision" --value 0

for i in 0 1 2 3; do
  pg="${PAGES[$i]}"
  p pages background "$R/$pg.Page" --image "assets/bg_${KEYS[$i]}.png" --scaling Fit --transparency 0
  for j in 0 1 2 3; do [ $i = $j ] || pos "$pg" "nav$j" "${NAV_X[$j]}" 17 84 28; done
  s=0
  for k in ${KPIS[$pg]}; do
    pos "$pg" "kpi${k}Value" "${KPI_X[$s]}" 148 164 44
    pos "$pg" "kpi${k}Delta" "${KPI_X[$s]}" 186 168 36
    s=$((s+1))
  done
  # serif numerals for the KPI strip
  p set "$R/$pg.Page/kpi*Value.Visual.value.fontFamily" --value "Georgia" -f
  p set "$R/$pg.Page/kpi*Value.Visual.value.fontSize" --value 21 -f
  p set "$R/$pg.Page/kpi*Value.Visual.value.fontColor" --value "$INK" -f
  p set "$R/$pg.Page/kpi*Delta.Visual.value.fontSize" --value 9 -f
done

# filters: plain dropdowns on the page, no pills
for pg in "Portfolio" "Occupancy & Leasing" "Collections & NOI"; do
  pos "$pg" slType 616 232 184 54; pos "$pg" slCity 808 232 184 54
done
p set "$R/**/sl*.Visual.items.background" --value "$CARD" -f; p set "$R/**/sl*.Visual.general.outlineColor" --value "$CARD" -f
SV="$PD/propSlicer.Visual"
p set "$SV.data.mode" --value Dropdown; p set "$SV.header.show" --value false; p set "$SV.items.background" --value "$CARD"
p visuals position "$SV" --x 636 --y 238 --width 320 --height 40

# ---------------------------------------------------------------- Portfolio: the map is the stage
PG="Portfolio"; P="$R/$PG.Page"
for v in cityTable infoValue infoOcc infoNOI infoColl infoMap propTable; do p rm "$P/$v.Visual" -f; done
p visuals border "$P/propertyMap.Visual" --no-show
pos "$PG" propertyMap 0 0 520 720
p add visual tableEx "$P" -n propTable -d "Values:Properties.Photo" -d "Values:Properties.Property" -d "Values:Properties.City" -d "Values:$M.Units" -d "Values:$M.Occupancy Bar" -d "Values:$M.Occupancy %" -d "Values:$M.NOI" --x 560 --y 326 --width 688 --height 378
p visuals sort "$P/propTable.Visual" -f "$M.NOI" -d Descending
tbl "$P/propTable.Visual" "NOI" 9.5 "$CARD" 38 56
colour_col "$P/propTable.Visual" "Occupancy Text Color" "Occupancy %"
inf "$PG" infoProps 560 300 688

# ---------------------------------------------------------------- Occupancy & Leasing
PG="Occupancy & Leasing"; P="$R/$PG.Page"
p add visual image "$P" -n hero --image "https://images.unsplash.com/photo-1516501312919-d0cb0b7b60b8?w=1040&h=580&fit=crop&q=75" --x 0 --y 0 --width 520 --height 290
for v in occTrend vacantByCity occByType; do p visuals title "$P/$v.Visual" --no-show; done
pos "$PG" occTrend 24 336 472 368;       inf "$PG" infoTrend 24 310 472
pos "$PG" vacantByCity 560 326 332 164;  inf "$PG" infoVacant 560 300 332
pos "$PG" occByType 916 326 332 164;     inf "$PG" infoTypes 916 300 332
pos "$PG" expiring 560 528 688 176;      inf "$PG" infoExp 560 502 688
tbl "$P/expiring.Visual" "Expiring Rent" 9.5 "$CARD"
p visuals action "$P/infoTypes.Visual" --type PageNavigation --target "$(page_id "$PG")" --tooltip "Occupancy on the snapshot date for each property type. Terracotta means under 90%."

# ---------------------------------------------------------------- Collections & NOI
PG="Collections & NOI"; P="$R/$PG.Page"
p add visual image "$P" -n hero --image "https://images.unsplash.com/photo-1549757521-4160565ff3de?w=1040&h=580&fit=crop&q=75" --x 0 --y 0 --width 520 --height 290
p rm "$P/noiTable.Visual" -f
for v in dueTrend statusBar expBar; do p visuals title "$P/$v.Visual" --no-show; done
pos "$PG" dueTrend 24 336 472 368;       inf "$PG" infoDue 24 310 472
pos "$PG" statusBar 560 326 332 164;     inf "$PG" infoStatus 560 300 332
pos "$PG" expBar 916 326 332 164;        inf "$PG" infoExp 916 300 332
p add visual tableEx "$P" -n noiTable -d "Values:Properties.Photo" -d "Values:Properties.Property" -d "Values:$M.Rent Collected" -d "Values:$M.Collection Bar" -d "Values:$M.Collection Rate" -d "Values:$M.Operating Expenses Total" -d "Values:$M.NOI" --x 560 --y 528 --width 688 --height 176
p visuals sort "$P/noiTable.Visual" -f "$M.NOI" -d Descending
tbl "$P/noiTable.Visual" "Rent Collected" 9.5 "$CARD" 32 48
colour_col "$P/noiTable.Visual" "Collection Text Color" "Collection Rate"
inf "$PG" infoNoi 560 502 688

# ---------------------------------------------------------------- Property Detail: the building's own photo is the stage
PG="Property Detail"; P="$R/$PG.Page"
p rm "$P/infoPick.Visual" -f
p add visual image "$P" -n hero --image "$M.Hero Photo" --x 0 --y 0 --width 520 --height 360
p add visual tableEx "$P" -n aboutTable -d "Values:Properties.City" -d "Values:Property Types.Property Type" -d "Values:Properties.Year Built" -d "Values:Properties.Property Manager" -d "Values:$M.Units" -d "Values:$M.Portfolio Value" --x 24 --y 404 --width 472 --height 86
tbl "$P/aboutTable.Visual" "" 9.5 "$STAGE"
for v in maintBar unitTable propTrend; do p visuals title "$P/$v.Visual" --no-show; done
pos "$PG" maintBar 24 526 472 182;       inf "$PG" infoMaint 24 500 472
pos "$PG" unitTable 560 326 688 164;     inf "$PG" infoUnits 560 300 688
tbl "$P/unitTable.Visual" "Rent Roll" 9.5 "$CARD" 16 104
pos "$PG" propTrend 560 528 688 176

# heroes fill their frame
for pg in "Occupancy & Leasing" "Collections & NOI" "Property Detail"; do
  p set "$R/$pg.Page/hero.Visual.imageScaling.imageScalingType" --value Fill
  for s in top bottom left right; do p set "$R/$pg.Page/hero.Visual.padding.$s" --value 0; done
done
p fields rename "$R" "Properties.Photo" " "
p fields rename "$R" "Property Types.Property Type" "Type"
pbir -q validate "$R" --fields 2>&1 | tail -2
