# Testing — SupplyChainIQ

Layers: data (schema/constraints/dups/FK/business rules), ETL (transform fixture, watermark, idempotency, recovery), warehouse (grain unique, SCD single-current, measures reconcile), ML (leakage prefix-only, time split, baseline compare), BI (DAX vs SQL gold on sample), E2E (seed 7: generate→load→kpi→forecast→prescription).

Run: `.venv/bin/pytest -q` (hermetic tmp fixtures; demo DB not required). E2E: `scripts/run_tests.sh`. CI: .github/workflows/ci.yml.
