#!/usr/bin/env bash
set -euo pipefail
# E2E demo on small seed (fast, hermetic): generate → load → KPI/forecast spot check
rm -rf /tmp/sci-demo && mkdir -p /tmp/sci-demo
.venv/bin/python -m data_generator.generate --seed 7 --days 90 --out /tmp/sci-demo/src >/dev/null
.venv/bin/python -m etl.load --src /tmp/sci-demo/src --db /tmp/sci-demo/wh.db --batch DEMO7 | tail -4
.venv/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect('/tmp/sci-demo/wh.db')
print('sales', c.execute('select count(*) from fact_sales').fetchone()[0])
print('otd', c.execute('select round(avg(on_time),3) from fact_deliveries').fetchone()[0])
print('quarantine', c.execute('select count(*) from dq_quarantine').fetchone()[0])
PY
