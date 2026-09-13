# Architecture — SupplyChainIQ

Status: APPROVED 2026-09-13 (ADR-001 to 005). See docs/decisions.md.

## Data Flow

```
CSV/Excel/API-stub (SYNTHETIC v1)
  → ingestion/ (validate schema, attach batch_id, ingested_at)
  → data/raw/ (immutable landing, one file per source+batch)
  → etl/staging (typed, deduped by business key, FK pre-check → quarantine)
  → warehouse/ (Postgres 16 canonical; SQLite-compatible ANSI SQL for local demo)
      dims (SCD1/SCD2, unknown 0) then facts (watermark incremental, idempotent)
  → marts (views: mart_inventory, mart_procurement, mart_logistics, mart_demand, mart_risk)
  → Power BI import + Python analytics (read-only views)
```

Future ERP/WMS/TMS: write new adapter to same staging contract. No warehouse rebuild.

## Adapter Interface (binding)

Each adapter implements: `discover() → list[source_file]`, `read(f) → rows`, `to_staging(rows, batch_id) → (accepted, rejected[])`. Rejected rows carry rule_id + reason into quarantine. Batch_id format `YYYYMMDD-HHMMSS-<seed>`.

## Watermark + Idempotency

watermark table (source, last_key). Staging upsert on business key + batch_id unique. Facts merge on business key; rerun same batch = zero delta (tested).

## Execution Log

etl_execution_log(run_id, started_at, ended_at, source, rows_read, rows_accepted, rows_rejected, errors json, status, duration_s). One row per source per run.

## Deployment

Docker Compose: postgres:16 + optional api (Phase 14). Local demo may run SQLite file `data/warehouse.db` with identical schema for zero-install CI. SQL kept ANSI + compatible types.

## Diagram source

Text diagram above is normative. ERD + star schemas in docs/datawarehouse.md (Phase 6).
