#!/usr/bin/env bash
set -euo pipefail
# Postgres backup (prod). Demo SQLite: copy data/warehouse.db.
if [ -n "${WAREHOUSE_HOST:-}" ]; then
  pg_dump -h "$WAREHOUSE_HOST" -U "${WAREHOUSE_USER:-sci_loader}" "${WAREHOUSE_DB:-supplychainiq}" > "backup-$(date +%F).sql"
else
  cp data/warehouse.db "backup-$(date +%F).db"
fi
echo OK
