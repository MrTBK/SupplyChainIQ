# Security — SupplyChainIQ

Least privilege. Prod = Postgres roles; demo SQLite simulates via separate read-only connection + view-only access.

* Roles (warehouse/sql/009_roles.sql, Postgres prod): sci_loader (write staging/dims/facts/logs), sci_analyst (SELECT on marts/views only), sci_admin (DDL). Analyst denied INSERT/UPDATE/DELETE (tested where engine supports).
* Secrets: config/.env never committed (.gitignore). CI uses env vars. Scan: `git grep -n "BEGIN PRIVATE\|api_key\|password=" -- ':!*.md'` review + no config/.env in tree (smoke test).
* Input: parameterized SQL only (no f-string queries on user input); CSV parsing with schema checks; NL-SQL (Phase 13 deferred) would add allowlist + LIMIT + read-only user.
* Audit: etl_execution_log + dq_quarantine retained; alert ack log if API built.
* Backup: scripts/backup.sh (pg_dump) + restore.sh; tested drill in deployment.
