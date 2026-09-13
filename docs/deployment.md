# Deployment — SupplyChainIQ

Envs dev→test→prod. `cp config/.env.example config/.env`. Prod: `docker compose up -d postgres`, `python -m etl.load --src data/generated/seed-42 --db ...` or Postgres DSN path, schedule daily cron (Airflow path documented: DAG = generate? no—ingest→etl→dq→forecast→prescribe). Backup scripts/backup.sh nightly. Logs: etl_execution_log. Monitoring: DQ score < 0.98 alert + log scan. Rollback: restore prior dump + `git checkout <tag>` + rerun pytest. Reproduce from README alone (tested fresh-clone in CI).

## Web layer (Phase 14)

Backend: `.venv/bin/uvicorn api.main:app --port 8000` (systemd/unit of choice in prod; set SCI_SECRET_KEY, SCI_COOKIE_SECURE=1, SCI_ADMIN_USER/SCI_ADMIN_PASSWORD, SCI_WAREHOUSE_DB/SCI_APP_DB). Frontend: `cd frontend && npm install && npm run build`, serve `dist/` from the same origin as the API (required for session cookies) or keep Vite's /api proxy in dev (`npm run dev`). Health: GET /api/health. Smoke: login → /api/kpis/overview → logout (see tests/test_api_workflow.py). Data: point SCI_WAREHOUSE_DB at the loaded warehouse; operational state stays in git-ignored app.db.
