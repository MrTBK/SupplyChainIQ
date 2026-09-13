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
