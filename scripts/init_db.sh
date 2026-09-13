#!/usr/bin/env bash
set -euo pipefail
# init DB from SQL (SQLite demo). Prod uses compose postgres with same files 001-008+010.
rm -f "${1:-data/warehouse.db}"
.venv/bin/python - <<PY
from pathlib import Path
from warehouse.db import connect, init_schema
con = connect(Path("${1:-data/warehouse.db}"))
init_schema(con)
for n in ["008_marts.sql", "010_indexes.sql"]:
    con.executescript((Path("warehouse/sql") / n).read_text())
con.close()
print("init ok")
PY
