# ETL — SupplyChainIQ

Raw (immutable CSV landing + batch_id) → Validation (schema, R01-R08) → Staging (typed, dedup) → Dims (SCD1/SCD2) → Facts (watermark incremental, INSERT OR IGNORE idempotent) → DQ score → Audit log.

Run: `python -m etl.load --src data/generated/seed-42 --db data/warehouse.db --batch DEMO42`

Log: etl_execution_log(run_id, started_at, ended_at, source, rows_read, rows_accepted, rows_rejected, errors, status, duration_s). Watermark: etl_watermark(source, last_key). Reprocess: rerun same batch → zero fact delta (tested). Failures: quarantine row with rule_id, never silent drop.
