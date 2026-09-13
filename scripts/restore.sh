#!/usr/bin/env bash
set -euo pipefail
# Restore: psql < backup.sql (prod) or cp backup db (demo). Verify with pytest after.
echo "restore: psql \$WAREHOUSE_DB < backup-YYYY-MM-DD.sql  (prod)"
echo "demo: cp backup-YYYY-MM-DD.db data/warehouse.db && pytest -q"
