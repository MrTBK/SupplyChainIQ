# Security — SupplyChainIQ

Least privilege. Prod = Postgres roles; demo SQLite simulates via separate read-only connection + view-only access.

* Roles (warehouse/sql/009_roles.sql, Postgres prod): sci_loader (write staging/dims/facts/logs), sci_analyst (SELECT on marts/views only), sci_admin (DDL). Analyst denied INSERT/UPDATE/DELETE (tested where engine supports).
* Secrets: config/.env never committed (.gitignore). CI uses env vars. Scan: `git grep -n "BEGIN PRIVATE\|api_key\|password=" -- ':!*.md'` review + no config/.env in tree (smoke test).
* Input: parameterized SQL only (no f-string queries on user input); CSV parsing with schema checks; NL-SQL (Phase 13 deferred) would add allowlist + LIMIT + read-only user.
* Audit: etl_execution_log + dq_quarantine retained; alert ack log if API built.
* Backup: scripts/backup.sh (pg_dump) + restore.sh; tested drill in deployment.

## Web layer (Phase 14)

* Auth: PBKDF2-SHA256 200k iterations + per-user salt (stdlib, `api/auth.py`); sessions server-side, 8h, HttpOnly, SameSite=Lax, Secure via SCI_COOKIE_SECURE=1 (enable behind HTTPS in prod).
* RBAC: see docs/rbac.md; enforced per endpoint, tested (14.4/14.17/14.19).
* Input: allowlisted ORDER BY, escaped LIKE, 10MB upload cap, schema-validated uploads, ETL trigger restricted to data/ dirs (traversal rejected), no raw SQL from frontend (14.5/14.19 tested).
* Warehouse: API opens it read-only (`mode=ro`); write attempts raise (tested). Operational state (users/audit/alerts) lives in git-ignored `data/app.db`.
* Secrets: SCI_SECRET_KEY/SCI_ADMIN_* via env; dev defaults warn-by-documentation (override in prod); `config/.env` never committed.
* Known limits: no login rate limiting in v1; serve behind a proxy with limits or trusted network.
