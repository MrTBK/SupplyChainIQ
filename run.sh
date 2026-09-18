#!/usr/bin/env bash
# run.sh — one-command runner for SupplyChainIQ (DataCo real data).
# Usage: ./run.sh [--quick|--full|--tests-only|--web|--dataco]
#   --quick (default): pytest only (hermetic tmp fixtures, no data needed)
#   --full: pytest full suite incl. DataCo pipeline test (~2 min, reads 92MB CSV)
#   --tests-only: pytest only
#   --web: ensure DataCo warehouse loaded, build frontend if needed,
#          then serve API + SPA at http://localhost:8766
#   --dataco: (re)load DataCo CSV into data/warehouse.db (idempotent rerun = zero delta)
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

load_dataco() {
  local batch="$1" db="$2"
  echo "[run] loading DataCo into $db (batch $batch)..."
  .venv/bin/python -m etl.load_dataco --db "$db" --batch "$batch" | tail -10
}

case "$MODE" in
  --tests-only)
    echo "[run] running tests..."
    .venv/bin/pytest -q
    ;;
  --web)
    if [ ! -d frontend/node_modules ]; then
      echo "[run] installing frontend deps..."
      (cd frontend && npm install --no-audit --no-fund)
    fi
    if [ ! -f frontend/dist/index.html ]; then
      echo "[run] building frontend..."
      (cd frontend && npm run build)
    fi
    if [ ! -f data/warehouse.db ]; then
      echo "[run] no warehouse found — loading DataCo first..."
      load_dataco DATACO1 data/warehouse.db
    fi
    echo "[run] starting web servers (foreground)..."
    exec .venv/bin/python scripts/serve_web.py
    ;;
  --dataco)
    load_dataco DATACO1 data/warehouse.db
    ;;
  --full)
    echo "[run] running tests (full, incl. DataCo pipeline)..."
    .venv/bin/pytest -q
    ;;
  --quick|*)
    echo "[run] running tests..."
    .venv/bin/pytest -q --ignore=tests/test_dataco_pipeline.py
    ;;
esac

echo "[run] OK. Data: DataCo Smart Supply Chain (historical public dataset 2015-2018)."
