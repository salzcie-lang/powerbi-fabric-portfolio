#!/usr/bin/env bash
# Moves the CRM visuals into the CRM-specific layout: top pill tabs, KPI column on the left, content on the right.
# Run from 02_CRM-Pipeline after build_crm.sh. Geometry matches make_background_crm.py.
R="CRMPipeline.Report"; M="_Measures"
source "$(dirname "$0")/pbir_lib.sh"
pos() { p visuals position "$R/$1.Page/$2.Visual" --x "$3" --y "$4" --width "$5" --height "$6"; }

PAGES=("Pipeline Overview" "Funnel & Conversion" "Rep Performance" "Deal Detail"); KEYS=(overview funnel reps deals)
declare -A KPIS=( ["Pipeline Overview"]="Won Pipe Win Deal" ["Funnel & Conversion"]="Leads Qual L2W Cycle"
                  ["Rep Performance"]="Quota AtQuota Act Weighted" ["Deal Detail"]="Won Open Pipe Stalled" )

for i in 0 1 2 3; do
  pg="${PAGES[$i]}"
  p pages background "$R/$pg.Page" --image "assets/bg_${KEYS[$i]}.png" --scaling Fit --transparency 0
  # KPI column: four slots of 154px starting at y 78
  s=0
  for k in ${KPIS[$pg]}; do
    y0=$((78 + s*154))
    pos "$pg" "kpi${k}Value" 34 $((y0+54)) 160 52
    pos "$pg" "kpi${k}Delta" 34 $((y0+104)) 250 38
    [ -d "$R/definition/pages" ] && pbir -q visuals position "$R/$pg.Page/kpi${k}Spark.Visual" --x 196 --y $((y0+60)) --width 90 --height 42 >/dev/null 2>&1
    s=$((s+1))
  done
  # tabs
  for j in 0 1 2 3; do [ $i = $j ] || pos "$pg" "nav$j" $((304 + j*80)) 22 76 30; done
  # slicers sit inside the pills (same x as before, pills are 10..64)
  for sl in slTeam slSegment slStage slSource; do pbir -q visuals position "$R/$pg.Page/$sl.Visual" --y 10 --height 54 >/dev/null 2>&1; done
done

inf() { pos "$1" "$2" $(($3-30)) $(($4+10)) 20 20; }

PG="Pipeline Overview"
pos "$PG" wonTrend 316 78 560 302;   inf "$PG" infoTrend 876 78
pos "$PG" pipeByStage 892 78 364 302; inf "$PG" infoStage 1256 78
pos "$PG" wonByTeam 316 396 250 300;  inf "$PG" infoTeam 566 396
pos "$PG" openDeals 582 396 380 300;  inf "$PG" infoOpen 962 396
pos "$PG" leaderboard 978 396 278 300; inf "$PG" infoBoard 1256 396

PG="Funnel & Conversion"
pos "$PG" stageFunnel 316 78 320 302; inf "$PG" infoFunnel 636 78
pos "$PG" winBySource 652 78 294 302; inf "$PG" infoWin 946 78
pos "$PG" lostReasons 962 78 294 302; inf "$PG" infoLost 1256 78
pos "$PG" leadsTrend 316 396 460 300; inf "$PG" infoLeads 776 396
pos "$PG" sourceTable 792 396 464 300; inf "$PG" infoSource 1256 396

PG="Rep Performance"
pos "$PG" repTable 316 78 580 618;    inf "$PG" infoReps 896 78
pos "$PG" attainByTeam 912 78 344 302; inf "$PG" infoAttain 1256 78
pos "$PG" actByType 912 396 344 300;  inf "$PG" infoAct 1256 396

PG="Deal Detail"
pos "$PG" dealTable 316 78 940 618;   inf "$PG" infoDeals 1256 78

pbir -q validate "$R" --fields 2>&1 | tail -2
