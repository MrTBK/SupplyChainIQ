# Deployment — SupplyChainIQ

Envs dev→test→prod. `cp config/.env.example config/.env`. Prod: `docker compose up -d postgres`, `python -m etl.load --src data/generated/seed-42 --db ...` or Postgres DSN path, schedule daily cron (Airflow path documented: DAG = generate? no—ingest→etl→dq→forecast→prescribe). Backup scripts/backup.sh nightly. Logs: etl_execution_log. Monitoring: DQ score < 0.98 alert + log scan. Rollback: restore prior dump + `git checkout <tag>` + rerun pytest. Reproduce from README alone (tested fresh-clone in CI).
