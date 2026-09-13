# SupplyChainIQ — Supply Chain Decision Intelligence Platform

Production-oriented BI/data engineering/analytics platform.

Raw Data → Ingestion → Data Quality → ETL/ELT → Warehouse → Data Marts → BI → Forecasting → Anomaly Detection → Risk → Prescriptive Recommendations → Decision Support.

> ALL DATA IN V1 IS SYNTHETIC. Never present generated data as real company data.
> Single source of truth: `docs/PROJECT_PLAN.md`.

## Status

Phase 0 — Discovery & Skills. See `docs/PROJECT_PLAN.md` section 2 for live status.

## Quickstart (dev)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp config/.env.example config/.env
.venv/bin/pytest -q
```

## Structure

Created only as phases need them. No placeholder dirs.

```
supplychainiq/
  docs/PROJECT_PLAN.md
  docs/decisions.md
  config/.env.example
  tests/
```

Full target structure is defined in `docs/PROJECT_PLAN.md` Phase 18/22.

## Rules

* Plan before code. See `docs/PROJECT_PLAN.md`.
* Every KPI has definition + formula in `docs/kpis.md` (Phase 9).
* Every ML model has evaluation vs baseline.
* Every recommendation is explainable.
* No secrets in git. Use `config/.env`, never commit it.
* Bad records go to quarantine, never silently dropped.
