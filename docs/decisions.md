# Architecture Decisions

Log for every significant decision. Never silently change architecture.

## ADR-001 — PostgreSQL as Warehouse (APPROVED 2026-09-13)

Context: Need free, Docker-ready dimensional warehouse with window functions and Power BI connector.

Alternatives: SQL Server, DuckDB (local dev only).

Decision: PostgreSQL 16 canonical. Keep SQL ANSI for future SQL Server port.

Reason: Zero license, mature, testable, compose-ready.

Consequences: Team runs Postgres locally. Small dialect check needed if enterprise mandates SQL Server.

## ADR-002 — Python + SQL for ETL, no SSIS in v1 (APPROVED 2026-09-13)

Context: Cross-platform reproducibility, git diff, pytest.

Alternatives: SSIS, dbt.

Decision: Python + SQL with watermark idempotency. dbt deferred.

Reason: No Windows lock, no license, explicit quarantine + logging.

Consequences: Implement watermark/idempotency manually with tests.

## ADR-003 — Power BI for BI layer (APPROVED 2026-09-13)

Context: Project requirement.

Decision: Power BI Desktop, star import, DAX measures only, DimDate marked as date table.

Reason: Requirement + modeling maturity + incremental refresh path.

Consequences: Model size discipline required.

## ADR-004 — Baselines before complex ML (APPROVED 2026-09-13)

Decision: Naive + MA + SES must run before ARIMA/XGB/Prophet. Simplest within 2% WAPE wins.

Reason: Best practice, leakage control, explainability.

## ADR-005 — No full frontend in v1 (APPROVED 2026-09-13)

Decision: No CRUD app. FastAPI/monitoring UI only if proven useful (Phase 14 gate).

Reason: Core value is BI/data platform. Prevent scope creep.

## ADR-006 — Conversational BI deferred with guardrails specified (APPROVED 2026-09-13)

Decision: Defer NL-to-SQL build. Contract locked if built later: allowlisted tables, read-only analyst role, LIMIT 2000, parameterized SQL only, full logging, numbers only from query results.

Reason: Warehouse + BI must prove stable first. Security design done, code deferred to avoid uncontrolled LLM SQL.

## ADR-007 — No application layer in v1 beyond pipeline + BI (APPROVED 2026-09-13)

Decision: No web app in v1. Monitoring via logs + DQ views + Power BI. FastAPI reconsidered only on proven ops need.

Reason: Protect data-platform focus per ADR-005.

## ADR-008 — Build operational web layer: FastAPI + React/Vite, session auth (APPROVED 2026-09-14)

Decision: Build the web application as operational/control layer around the BI platform. Backend FastAPI (typed, TestClient-tested), frontend React + Vite SPA, server-side session cookies, SQLite demo / Postgres canonical. Frontend talks only to the API; API talks to services reusing analytics/, forecasting/, etl/, warehouse marts. Supersedes ADR-005/007 (kept for history).

Alternatives: Flask (rejected — weaker typing/auth ecosystem for 13-module scope); Jinja SSR (rejected by stakeholder frontend choice); JWT bearer (rejected by stakeholder auth choice — sessions fit operational user counts and are revocable).

API route table (business capabilities only): /auth (login/logout/me), /users /roles (admin), /kpis/overview, /inventory /products/:id, /suppliers, /shipments /deliveries, /forecasts, /risks /recommendations /alerts, /data-sources (+upload), /etl-runs (+guarded trigger), /data-quality, /audit.

RBAC matrix: executive (read all ops, no trigger/upload/admin), supply/procurement/inventory/logistics managers (read all ops + trigger ETL + upload sources in own domain), analyst (read all ops, no trigger/upload/admin), administrator (all + users/roles/audit). ETL trigger allowlist: generate-seed + load-batch jobs only; no arbitrary commands. Uploads land as batches and pass the same R01-R08 quarantine.

Reason: User directive 2026-09-14 requires usable operational interface; stack fits existing Python codebase, installed ui-styling skill, and Node 22 availability. Power BI keeps deep analytics; web app owns monitoring/workflows.

Consequences: requirements.txt gains fastapi/uvicorn + hashing lib; new api/, frontend/, alerts table; E2E/security test suites; .pbix remains separate.

## ADR-009 — Server-side sessions + CSRF double-submit, no JWT (APPROVED 2026-09-14)

Decision: Replace Starlette signed-cookie session content with random session IDs in app.db (idle 30m, absolute 8h, revocable, disabled-aware); CSRF via session-bound double-submit tokens. No JWT: single web client, server-side revocation required.

Alternatives: keep signed cookies (rejected — no revocation); JWT bearer (rejected — stateless conflicts with revocation + disabled-user requirements, no multi-client need).

Reason: Directive §§2-5 require revocable server-side sessions and CSRF for cookie auth with minimal new dependencies (stdlib + existing stack).

Consequences: sessions + csrf_token columns (migrated), login/logout shapes unchanged, 8 mutating routes carry CsrfChecked, frontend sends header automatically.
