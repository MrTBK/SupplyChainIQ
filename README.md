# SupplyChainIQ — Supply Chain Decision Intelligence Platform

Production-oriented BI/data engineering/analytics platform.

Raw Data → Ingestion → Data Quality → ETL/ELT → Warehouse → Data Marts → BI → Forecasting → Anomaly Detection → Risk → Prescriptive Recommendations → Decision Support.

> ALL DATA IN V1 IS SYNTHETIC. Never present generated data as real company data.
> Single source of truth: `docs/PROJECT_PLAN.md`.

## Status

Phase 0 — Discovery & Skills. See `docs/PROJECT_PLAN.md` section 2 for live status.

## Quickstart (dev)

One command (venv + install + SYNTHETIC demo + ETL + tests):

```bash
./run.sh            # quick demo (seed 7, 90 days)
./run.sh --full     # full demo (seed 42, 2 years, slower)
./run.sh --tests-only
```

Web app (Phase 14, operational layer around the BI platform):

```bash
./run.sh --web     # API + SPA at http://localhost:8766 (admin/change-me, SYNTHETIC demo)
```

Manual equivalent:

```bash
.venv/bin/uvicorn api.main:app --port 8000
cd frontend && npm install && npm run dev   # http://localhost:5173, /api proxied
```

API reference: `docs/api.md`. RBAC: `docs/rbac.md`. Full plan: `docs/PROJECT_PLAN.md`.

Manual equivalent:

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
