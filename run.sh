#!/usr/bin/env bash
# run.sh — one-command runner for SupplyChainIQ (SYNTHETIC demo).
# Usage: ./run.sh [--quick|--full|--tests-only]
#   --quick (default): venv + install + seed-7/90d generate + ETL load + pytest
#   --full: seed-42/730d generate + ETL load + pytest (slower, ~1 min)
#   --tests-only: pytest only (uses hermetic tmp fixtures, no data needed)
set -euo pipefail

MODE="${1:---quick}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -x .venv/bin/python ]; then
  echo "[run] creating venv..."
  python3 -m venv .venv
fi
echo "[run] installing deps..."
.venv/bin/pip install -q -r requirements.txt

run_etl() {
  local seed="$1" days="$2" batch="$3" src="$4" db="$5"
  echo "[run] generating SYNTHETIC seed=$seed days=$days -> $src"
  .venv/bin/python -m data_generator.generate --seed "$seed" --days "$days" --out "$src" | tail -1
  echo "[run] loading warehouse $db (batch $batch)..."
  .venv/bin/python -m etl.load --src "$src" --db "$db" --batch "$batch" | tail -4
  echo "[run] applying marts + indexes..."
  .venv/bin/python -c "
import sqlite3
c = sqlite3.connect('$db')
c.executescript(open('warehouse/sql/008_marts.sql').read())
c.executescript(open('warehouse/sql/010_indexes.sql').read())
print('mart_demand rows:', c.execute('select count(*) from mart_demand').fetchone()[0])
print('proc OTIF:', c.execute('select round(avg(case when late_days<=0 then 1.0 else 0 end),3) from mart_procurement').fetchone()[0])
print('logistics OTD:', c.execute('select round(avg(cast(on_time as float)),3) from mart_logistics').fetchone()[0])
"
}

case "$MODE" in
  --tests-only)
    echo "[run] running tests..."
    .venv/bin/pytest -q
    ;;
  --full)
    run_etl 42 730 DEMO42 data/generated/seed-42 data/warehouse.db
    echo "[run] running tests..."
    .venv/bin/pytest -q
    ;;
  --quick|*)
    run_etl 7 90 DEMO7 data/generated/seed-7 data/warehouse.db
    echo "[run] running tests..."
    .venv/bin/pytest -q
    ;;
esac

echo "[run] OK. Data is SYNTHETIC. See docs/demo.md for the business walkthrough."
