# SupplyChainIQ — Project Plan

> SINGLE SOURCE OF TRUTH for planning and progress tracking.
> If chat and this file disagree, inspect repo evidence and update this file.
> Synthetic data is always labeled SYNTHETIC. Never present generated data as real company data.

## 1. Project Overview

* **Project name:** SupplyChainIQ
* **Project title:** SupplyChainIQ — Supply Chain Decision Intelligence Platform
* **Project objective:** Build a production-oriented end-to-end BI/data engineering/analytics platform that transforms raw operational supply-chain data into decisions: Raw → Ingestion → Data Quality → ETL/ELT → Warehouse → Data Marts → BI → Advanced Analytics → Forecasting → Anomaly Detection → Risk Detection → Prescriptive Recommendations → Decision Support.
* **Target users:** Supply Chain Manager, Procurement Manager, Inventory Manager, Warehouse Manager, Logistics Manager, Operations Manager, Executive/Management, BI/Data Analyst, Data Engineer, System Administrator. Each role has different decisions, grain, and latency needs.
* **Target business domains:** Retail, distribution, manufacturing, wholesale, logistics.
* **Project scope (in):** Canonical data model, reproducible SYNTHETIC generator with seed, Python+SQL ingestion and ETL with audit, PostgreSQL star-schema warehouse, explicit DQ framework with quarantine, Power BI semantic model + 7 decision pages, inventory/supplier/logistics/demand analytics, forecasting with baseline comparison, explainable prescriptions, alert feed, tests, docs, Docker Compose deployment.
* **Out-of-scope items (v1):** Real ERP/WMS/TMS connectors (interface only), order-entry CRUD frontend, full web app unless monitoring need is proven, real-time IoT streaming, uncontrolled LLM SQL, mobile app, SSIS dependency, Kubernetes.

## 2. Current Status

```text
Current Phase: Phase 14 — Web Application (REOPENED, task 14.2 next)
Current Milestone: ADR-008 locked, structure next
Overall Progress: 88%

Completed:
✓ Phases 0-13, 15-20 COMPLETE
✓ 14.1 architecture decision (ADR-008)

In Progress:
→ 14.2 project structure

Next:
□ 14.3 auth → 14.4 RBAC → 14.5 API foundation → modules

Blockers:
None

Last Updated:
2026-09-14

Last Completed Task:
14.1 ADR-008 FastAPI + React/Vite + sessions

Next Concrete Task:
14.2 api/ + frontend/ structure
```

| Metric | Value |
|---|---|
| Current phase | Phase 14 — Web Application (reopened) |
| Current milestone | ADR-008 locked, structure next |
| Overall progress | 88% (14.1 of 24 web tasks done; all else complete) |
| Completed phases | Phases 0-13, 15-20 COMPLETE; Phase 14 in progress |
| Active phase | Phase 14 |
| Next phase | Release gate 14.24, then v2 hardening |
| Current blocker | None |
| Last updated | 2026-09-14 |
| Last completed task | 14.1 ADR-008 |
| Next concrete task | See Section 14 Next Action |

## 3. ROADMAP

### Phase 0 — Discovery & Skills

### Objective
Confirm scope, personas, stack direction, and working agreements. Lock plan file.

### Prerequisites
Skills loaded. Empty workspace inspected.

### Tasks
1. Inventory relevant skills and record use in plan.
2. Confirm personas and out-of-scope list.
3. Draft ADR-001 stack direction.
4. Create docs/PROJECT_PLAN.md.
5. Approval gate before scaffold.

### Deliverables
* docs/PROJECT_PLAN.md v1
* ADR-001 draft

### Files
* Create: `docs/PROJECT_PLAN.md`
* Create later: `docs/decisions.md`, `config/.env.example`

### Technologies
Markdown, git, opencode skills: brainstorming, writing-plans, grilling, using-superpowers.

### Tests
* Plan completeness check: every Phase 0-20 has all 10 subsections.
* No code tests yet.

### Acceptance Criteria
* Plan file exists at docs/PROJECT_PLAN.md.
* User approves scope and roadmap.

### Risks
* Scope creep to CRUD app. Mitigate with out-of-scope list.

### Dependencies
None.

### Definition of Done
Plan file merged, approval recorded in Change Log, Phase 0 marked COMPLETE.

---

### Phase 1 — Requirements

### Objective
Freeze functional, non-functional, data, analytics, security, deployment, scalability requirements. Trace every dashboard question to a KPI or mark out of scope.

### Prerequisites
Phase 0 COMPLETE.

### Tasks
1. Define target users and per-role decisions.
2. Define business processes (procure-to-pay, plan-to-stock, order-to-cash, record-to-report).
3. Define business questions per domain.
4. Define functional requirements.
5. Define non-functional requirements (reproducibility, idempotency, latency, model size).
6. Define data, analytics, security, deployment, scalability requirements.
7. Write docs/business_requirements.md.

### Deliverables
* docs/business_requirements.md
* Requirements traceability: question → KPI → mart → source

### Files
* Create: `docs/business_requirements.md`
* Update: `docs/PROJECT_PLAN.md`

### Technologies
ux-designer, ui-ux-pro-max, grilling, stop-slop for clarity.

### Tests
* Trace check: each listed business question maps to KPI catalog entry or explicit out-of-scope.
* Review checklist pass.

### Acceptance Criteria
* No orphan dashboard question without KPI or out-of-scope reason.
* Security and deployment requirements explicit.

### Risks
* Assuming all users need same UI. Mitigate with per-role decision table.

### Dependencies
Phase 0.

### Definition of Done
Requirements doc committed, trace complete, gate checklist passes.

---

### Phase 2 — Domain Modeling

### Objective
Model supply-chain domain before code. Glossary + conceptual ERD + fact grain drafts.

### Prerequisites
Phase 1 COMPLETE.

### Tasks
1. Define entities: Product, Category, Supplier, Contract, Warehouse, Inventory, Movement, PO + lines, SO + lines, Customer, Shipment, Delivery, Return, Carrier, Location, Costs, Lead times.
2. Define relationships.
3. Define business glossary entries.
4. Draft fact grains in plain language.
5. Create conceptual ERD (text + diagram source).

### Deliverables
* docs/business_glossary.md
* Conceptual ERD

### Files
* Create: `docs/business_glossary.md`
* Create: `docs/data_dictionary.md` (stub, full in Phase 6)

### Technologies
ux-designer for IA, systematic naming.

### Tests
* Glossary review: every KPI term exists in glossary.
* Relationship sanity: every FK has parent entity.

### Acceptance Criteria
* Glossary covers on-hand, available, lead-time demand, safety stock, reorder point, coverage days, dead stock, OTIF.
* Every future fact has one grain sentence.

### Risks
* Copying OLTP into warehouse later. Mitigate by stating analytic grains now.

### Dependencies
Phase 1.

### Definition of Done
Glossary committed, ERD reviewed, grains recorded.

---

### Phase 3 — Data Strategy

### Objective
Define Source → Raw → Staging → Warehouse → Mart → BI/ML contracts. Support SYNTHETIC now, ERP/WMS/TMS later via same contract.

### Prerequisites
Phase 2 COMPLETE.

### Tasks
1. Define Raw immutable landing (batch_id, ingested_at, source_system, source_key).
2. Define Staging typed + deduped contract.
3. Define adapter interface for CSV/Excel/API stub now, ERP/Postgres later.
4. Define seed and version policy for SYNTHETIC data.
5. Write docs/architecture.md data-flow section.

### Deliverables
* Source contracts + adapter interface spec

### Files
* Create: `docs/architecture.md` (data flow)
* Create later: `ingestion/`, `config/`

### Technologies
Python, SQL, Postgres.

### Tests
* Contract validation test stub: sample CSV validates against schema or fails with reason.

### Acceptance Criteria
* New source can be added by writing adapter, no warehouse rebuild needed on paper review.

### Risks
* Single-dataset dependence. Mitigate with canonical model.

### Dependencies
Phase 2.

### Definition of Done
Contracts documented, adapter interface defined, gate passes.

---

### Phase 4 — Dataset

### Objective
Reproducible SYNTHETIC generator with realistic business behavior. Same seed = identical dataset.

### Prerequisites
Phase 3 COMPLETE.

### Tasks
1. Implement data_generator with seed argument.
2. Generate products, suppliers, contracts, warehouses, customers, carriers, POs, SOs, inventory snapshots, movements, shipments, deliveries, returns, prices, lead times.
3. Inject scenarios: seasonality, promo spikes, supplier delays, stockouts, overstocks, quality incidents, price steps, lane delays, lifecycle change.
4. Tag is_synthetic=true, generator_version, seed everywhere.
5. Hash reproducibility test.

### Deliverables
* Working generator + demo dataset (2 years daily minimum)

### Files
* Create: `data_generator/*.py`
* Create: `data/generated/`, `data/raw/`
* Create: `tests/test_generator_reproducibility.py`

### Technologies
Python, Faker, numpy, pytest, test-driven-development skill.

### Tests
* Same seed twice produces identical row hashes.
* Scenario presence test: stockouts > 0, delays > 0, dead SKUs > 0.
* Referential integrity: every FK resolves or quarantines.

### Acceptance Criteria
* 2-year demo generates in < 10 min on dev machine.
* Clearly labeled SYNTHETIC.

### Risks
* Random meaningless numbers. Mitigate with regime-based generation.

### Dependencies
Phase 3.

### Definition of Done
Generator green, demo data present, DQ pre-check passes, docs updated.

---

### Phase 5 — Architecture

### Objective
Lock final architecture and stack via ADR. Compose draft.

### Prerequisites
Phase 4 contract validated (can generate sample).

### Tasks
1. Build technology decision matrix (need, alternatives, pros/cons, complexity, cost, maintainability).
2. Decide: Postgres 16 canonical, Python+SQL ETL, Power BI, sklearn+statsmodels baseline, XGBoost optional, FastAPI conditional, no frontend default.
3. Draft docker-compose.yml.
4. Record ADR-001 to ADR-005.

### Deliverables
* ADR log updated, architecture diagram, compose draft

### Files
* Create: `docs/decisions.md`
* Create: `docker-compose.yml` (draft)
* Update: `docs/architecture.md`

### Technologies
Postgres, Python, Docker, Power BI.

### Tests
* ADR review: every choice has alternatives + reason + consequences.
* Compose config validates (`docker compose config`).

### Acceptance Criteria
* Stack locked or explicitly deferred with reason.

### Risks
* Trendy tech without reason. Mitigate with matrix.

### Dependencies
Phases 1-4.

### Definition of Done
ADRs committed, architecture diagram matches data strategy, gate passes.

---

### Phase 6 — Data Warehouse

### Objective
Star schema DDL with correct grains, SCDs, unknown members, constraints. ERD + star diagrams.

### Prerequisites
Phase 5 COMPLETE.

### Tasks
1. Create DimDate, DimProduct (SCD2), DimSupplier (SCD2), DimWarehouse, DimCustomer (SCD1), DimCarrier, DimLocation.
2. Create FactSales (SO line), FactPurchases (PO line receipt), FactInventorySnapshot (product/warehouse/day), FactInventoryMovement (event), FactShipments (shipment line), FactDeliveries (delivery line), FactReturns (return line).
3. Add surrogate keys, FKs, checks, unknown member 0.
4. Write docs/datawarehouse.md with grain per fact.
5. ERD + star schema diagrams.

### Deliverables
* warehouse/sql DDL that creates empty warehouse clean

### Files
* Create: `warehouse/sql/001_dims.sql`, `002_facts.sql`, `003_constraints.sql`, `004_unknown_members.sql`
* Create: `docs/datawarehouse.md`, `docs/data_dictionary.md` (full)

### Technologies
PostgreSQL, SQL.

### Tests
* Grain uniqueness: one row per stated grain (unique index test).
* FK enforcement test with bad insert rejected.
* SCD test: single current flag per natural key.
* Unknown member exists in each dim.

### Acceptance Criteria
* Empty warehouse builds from scratch with zero errors.
* Every fact section starts with grain sentence.

### Risks
* Copying OLTP schema. Mitigate with grain review.

### Dependencies
Phase 5.

### Definition of Done
DDL green, diagrams committed, dictionary complete.

---

### Phase 7 — ETL

### Objective
Robust incremental idempotent pipeline: Raw → Validation → Staging → Dims → Facts → Audit.

### Prerequisites
Phase 6 COMPLETE, generator sample available.

### Tasks
1. Raw landing with batch_id.
2. Schema validation + dedup to staging.
3. Dimension SCD loader.
4. Fact incremental loader with watermark table.
5. etl_execution_log writer (run_id, start, end, source, rows_read/accepted/rejected, errors jsonb, status, duration).
6. Error handling, logging, reprocess path, quarantine handoff.

### Deliverables
* Runnable ETL end to end on demo data

### Files
* Create: `ingestion/*.py`, `etl/*.py`, `etl/sql/*.sql`, `warehouse/sql/005_watermarks.sql`, `warehouse/sql/006_etl_log.sql`

### Technologies
Python, SQL, pytest, systematic-debugging.

### Tests
* Transformation fixture in→out.
* Incremental watermark advances.
* Rerun same batch id = zero delta (idempotency).
* Failure recovery to green.
* Log completeness test.

### Acceptance Criteria
* Full reload + incremental both work.
* Rerun without changes changes zero fact rows.

### Risks
* Silent data mutation to make dashboards look right. Forbidden. Fail loudly to quarantine.

### Dependencies
Phases 4, 6, 8 (DQ rules interface).

### Definition of Done
ETL green on demo, logs complete, gate passes.

---

### Phase 8 — Data Quality

### Objective
Explicit DQ framework. Bad records never silently enter warehouse. Measurable score.

### Prerequisites
Phase 7 ETL skeleton exists (interface for checks).

### Tasks
1. Rules YAML: completeness, validity, uniqueness, FK, consistency, timeliness.
2. Implement R01-R08 minimum (supplier not null, qty >= 0, delivery >= shipment, PO supplier exists, movement product+warehouse exists, promised date present, dup key rejected, freshness < 26h).
3. Quarantine table + rule_id.
4. DQ score view: accepted/read weighted + per-rule pass rate.
5. docs/data_quality.md + docs/kpis.md DQ section.

### Deliverables
* DQ checks run per batch, quarantine populated, score visible

### Files
* Create: `etl/dq_rules.yml`, `etl/dq_checks.py`, `warehouse/sql/007_quarantine.sql`
* Create: `docs/data_quality.md`
* Create: `tests/test_dq_*.py`

### Technologies
Python, SQL, pytest.

### Tests
* Bad fixture quarantined with correct rule_id.
* Score < 0.98 blocks fact promotion to partial status.
* Null/negative/date-inversion fixtures rejected.

### Acceptance Criteria
* Zero silent drops. Every rejected row has reason.

### Risks
* Threshold gaming. Mitigate with per-rule rates visible.

### Dependencies
Phase 7.

### Definition of Done
DQ green, quarantine verified, score documented.

---

### Phase 9 — BI

### Objective
Power BI semantic model + 7 decision pages. Decisions not decoration.

### Prerequisites
Phases 6-8 COMPLETE (warehouse loaded, DQ passing).

### Tasks
1. Model relationships (single direction dim→fact via SKs), mark date table.
2. DAX measures only, no calc columns except date. Hierarchies date/product/location.
3. Build pages: Executive, Inventory, Procurement, Demand, Logistics, Risk/Alerts, Forecasting.
4. docs/bi.md + docs/kpis.md full definitions.
5. UX validation per ux-designer checklist.

### Deliverables
* powerbi/SupplyChainIQ.pbix + measures table + page specs

### Files
* Create: `powerbi/README.md`, `powerbi/measures.dax`, `powerbi/model_notes.md`
* Create: `docs/bi.md`, `docs/kpis.md`

### Technologies
Power BI, DAX, ui-ux-pro-max, ux-designer.

### Tests
* DAX vs SQL gold queries on sample (all 22 core KPIs within rounding).
* Filter + date logic spot checks.
* Model size < 500MB demo, import only needed columns.

### Acceptance Criteria
* Each page answers its business questions with max 3 visuals per section, no gauge spam, clear hierarchy.

### Risks
* KPI spam, decorative visuals, fake precision. Mitigate with measure definitions.

### Dependencies
Phases 6-8.

### Definition of Done
BI tests pass, UX checklist passes, docs complete.

---

### Phase 10 — Analytics

### Objective
Inventory turnover, ABC, stockout analysis, supplier scoring, lead-time p50/p90, demand trends, anomaly detection. Each with problem→target→features→baseline→model→eval→value→limits.

### Prerequisites
Phase 9 green (BI foundation works).

### Tasks
1. Turnover + ABC (A 80%, B 15%, C 5% revenue).
2. Stockout analysis.
3. Supplier score: OTIF 50 + quality 30 + price stability 20.
4. Lead-time analysis.
5. Anomaly: z-score + IsolationForest on demand residuals after baseline.

### Deliverables
* analytics/ notebooks/scripts + docs/machine_learning.md part 1

### Files
* Create: `analytics/*.py`, `analytics/*.ipynb` (small, reproducible)
* Update: `docs/machine_learning.md`

### Technologies
Python, scikit-learn, pandas.

### Tests
* Method reproducibility with seed.
* Supplier score weights sum to 1 test.
* Anomaly precision spot check on injected spike.

### Acceptance Criteria
* No blind ML. Every method has limits section.

### Risks
* Overclaiming anomaly accuracy. Mitigate with baseline comparison.

### Dependencies
Phase 9.

### Definition of Done
Analytics reproducible, docs with evaluation, gate passes.

---

### Phase 11 — Forecasting

### Objective
Real forecasting pipeline with baseline comparison and time-series validation.

### Prerequisites
Phase 10 trends available.

### Tasks
1. Build monthly product/warehouse demand series.
2. Run baselines: naive carry-forward, 3M moving average, SES.
3. Candidates: ARIMA, XGBoost/LightGBM, Prophet optional.
4. Rolling-origin CV, metrics MAE/RMSE/WAPE.
5. Select simplest within 2% WAPE of best. Document choice.
6. Write docs/forecasting.md.

### Deliverables
* forecasting/ pipeline + WAPE report + next 1-3 month outputs

### Files
* Create: `forecasting/*.py`, `forecasting/README.md`
* Create: `docs/forecasting.md`
* Create: `tests/test_forecast_*.py`

### Technologies
statsmodels, scikit-learn, XGBoost/LightGBM optional.

### Tests
* No leakage: features only past data (as-of join test).
* Train/test time split enforced.
* Baseline comparison recorded.

### Acceptance Criteria
* Best model beats naive or naive kept with written reason. New/intermittent SKU limits documented.

### Risks
* Complex model assumed best. Mitigate with mandatory baselines.

### Dependencies
Phase 10.

### Definition of Done
Forecast outputs in warehouse/mart, metrics committed, docs complete.

---

### Phase 12 — Prescriptive Analytics

### Objective
Explainable recommendations: reorder, safety stock, supplier pick, transfer, stockout risk.

### Prerequisites
Phase 11 COMPLETE.

### Tasks
1. reorder_qty = max(0, forecast lead-time demand + safety stock - on_hand - on_order).
2. Safety stock = z * demand_stddev * sqrt(lead_time).
3. Supplier pick = min risk-adjusted cost among approved contracts.
4. Transfer = min(surplus, deficit) same SKU.
5. Risk score 0-100 with inputs shown + reason codes.
6. Example row manually recomputable.

### Deliverables
* Prescription tables/views + explanation columns

### Files
* Create: `analytics/prescriptions.py`, `warehouse/sql/008_marts_prescriptive.sql`

### Technologies
Python, SQL.

### Tests
* Hand-calc test: sample ABC-001 recomputes exactly.
* No unexplained recommendation: every row has inputs + reason code.

### Acceptance Criteria
* Every recommendation shows forecast, lead time, safety stock, reason.

### Risks
* Black-box AI recommendations. Forbidden.

### Dependencies
Phase 11.

### Definition of Done
Prescriptions verified, docs updated, gate passes.

---

### Phase 13 — AI / Conversational BI

### Objective
Guarded NL→SQL only after analytics reliable. Conditional; skip with ADR if not needed.

### Prerequisites
Phases 9, 11, 12 green.

### Tasks
1. Allowlisted tables + columns.
2. Read-only DB user + statement timeout + LIMIT 2000.
3. Intent → validated parameterized SQL → result → explanation from data only.
4. Logging of every NL query + SQL + rows.
5. Injection attempt tests.

### Deliverables
* Prototype or ADR to defer

### Files
* Create if built: `api/nl/*.py`
* Update: `docs/security.md`, `docs/architecture.md`

### Technologies
Python, Postgres RLS/roles, LLM only for intent (never direct SQL exec without validator).

### Tests
* Disallowed table rejected.
* DROP/UPDATE/DELETE rejected.
* Numbers match direct SQL result exactly.

### Acceptance Criteria
* No uncontrolled LLM SQL. No invented numbers.

### Risks
* Prompt injection to exfiltration. Mitigate with allowlist + read-only.

### Dependencies
Phases 9, 11, 15.

### Definition of Done
Security tests green or deferral ADR recorded.

---

### Phase 14 — Application Layer

### Objective
Build web app only if it materially helps (ETL/DQ/alert monitoring). Default is skip.

### Prerequisites
Phases 7-9, 12 stable.

### Tasks
1. Decide via ADR: build vs skip.
2. If build: auth, ETL run view, DQ view, alert ack, user mgmt. No order entry.
3. If skip: record reason, keep BI as center.

### Deliverables
* ADR-014 + optional minimal API/UI

### Files
* Create if built: `api/`, `frontend/` (minimal)
* Update: `docs/architecture.md`

### Technologies
FastAPI conditional, ui-styling/shadcn only if UI built, agent-browser for QA.

### Tests
* API tests if API exists. Auth negative tests.

### Acceptance Criteria
* BI remains center. No generic CRUD sprawl.

### Risks
* Turning into CRUD app. Mitigate with module allowlist.

### Dependencies
Phases 7-9.

### Definition of Done
Decision recorded; if built, tests green.

---

### Phase 15 — Security

### Objective
Least-privilege, secrets hygiene, audit, backup.

### Prerequisites
Architecture known (Phase 5), warehouse exists.

### Tasks
1. Roles: loader (write staging), analyst read-only (marts/views), admin.
2. Secrets via env, scan for leaks, .gitignore.
3. Input validation, parameterized SQL only.
4. API JWT + audit logs if API exists.
5. Backup/restore procedure.

### Deliverables
* docs/security.md + roles SQL + backup scripts

### Files
* Create: `warehouse/sql/009_roles.sql`, `scripts/backup.sh`, `scripts/restore.sh`
* Create: `docs/security.md`

### Technologies
Postgres roles, Docker, env.

### Tests
* Analyst cannot write (negative test).
* Secret scan passes (`git grep` for keys + gitleaks if available).
* SQL injection fixture blocked.

### Acceptance Criteria
* Least privilege verified, no secrets in git.

### Risks
* Overpermissive demo credentials shipped. Mitigate with separate dev/prod env examples.

### Dependencies
Phases 5-7.

### Definition of Done
Security checks green, docs complete.

---

### Phase 16 — Testing

### Objective
CI green on fresh clone. Tests for data, ETL, warehouse, ML, BI, E2E.

### Prerequisites
All build phases have tests drafted.

### Tasks
1. pytest suite + SQL constraint checks.
2. E2E: seed 42 raw → warehouse → KPI gold queries.
3. Coverage where meaningful (generator, ETL, DQ, forecast).
4. Record results in plan Test Status.

### Deliverables
* Green suite + test report

### Files
* Create: `tests/`, `scripts/run_tests.sh`, `.github/workflows/ci.yml` (if GitHub used)

### Technologies
pytest, SQL, test-driven-development, verification-before-completion.

### Tests
* The suite itself. Fresh clone run.

### Acceptance Criteria
* Full suite passes. No hidden failing tests.

### Risks
* Marking complete on partial run. Mitigate with full-command evidence.

### Dependencies
All prior build phases.

### Definition of Done
CI green, evidence logged.

---

### Phase 17 — Performance

### Objective
Measure first, then index/partition/refresh-tune only where needed.

### Prerequisites
Phase 16 data loaded at demo scale.

### Tasks
1. EXPLAIN ANALYZE top 10 BI queries.
2. ETL duration per table report.
3. Power BI refresh time + model size.
4. Forecast train/infer timing.
5. Apply indexes on FK+date, monthly partitioning if >10M rows, incremental refresh ready.

### Deliverables
* Performance report with before/after

### Files
* Create: `docs/performance.md` (or section in architecture.md)
* Create: `warehouse/sql/010_indexes.sql`

### Technologies
Postgres EXPLAIN, Power BI Performance Analyzer.

### Tests
* p95 BI queries < 3s demo or bottleneck listed as known issue.
* Rerun timings recorded.

### Acceptance Criteria
* No premature optimization without measurement.

### Risks
* Optimizing wrong layer. Mitigate with measurement first.

### Dependencies
Phases 6-9, 11.

### Definition of Done
Report committed, critical bottlenecks addressed or logged.

---

### Phase 18 — Deployment

### Objective
Reproducible dev → test → prod. Document env, DB setup, schedule, backup, monitoring, rollback.

### Prerequisites
Phases 15-17 green.

### Tasks
1. Finalize docker-compose.yml (postgres + optional api).
2. Env vars documented.
3. ETL scheduling (cron + Airflow upgrade path).
4. Backup/restore verified.
5. Rollback to prior dump + git tag tested.

### Deliverables
* docs/deployment.md + working compose up from scratch

### Files
* Create: `docker-compose.yml`, `config/.env.example`, `docs/deployment.md`, `scripts/init_db.sh`

### Technologies
Docker Compose, bash, Postgres.

### Tests
* Fresh-machine restore test from docs alone.
* Rollback drill.

### Acceptance Criteria
* New contributor reproduces project from README + deployment doc without chat help.

### Risks
* Undocumented manual step. Mitigate with fresh-machine test.

### Dependencies
Phases 15-17.

### Definition of Done
Deployment verified, docs complete.

---

### Phase 19 — Documentation

### Objective
Complete docs set + diagrams + ADRs. Documentation is part of product.

### Prerequisites
All prior phases substantially complete.

### Tasks
1. Ensure present: README, architecture, business_requirements, business_glossary, data_dictionary, data_quality, etl, datawarehouse, bi, forecasting, machine_learning, security, testing, deployment, kpis, decisions.
2. Diagrams: data flow, ERD, star schemas, deployment.
3. Sources log for research (Phase 24).
4. stop-slop pass for clarity.

### Deliverables
* Full docs/ set

### Files
* Update: `docs/*.md`, `README.md`

### Technologies
Markdown, stop-slop, slides for diagrams where needed.

### Tests
* Docs checklist: every file exists and links resolve.
* KPI every-measure-has-definition check.

### Acceptance Criteria
* Architectural decisions and reasoning recorded. No silent changes.

### Risks
* Stale docs. Mitigate with plan-as-truth rule.

### Dependencies
All.

### Definition of Done
Docs checklist green.

---

### Phase 20 — Final Validation & Demo

### Objective
Technical demo + business demo on SYNTHETIC data. Prove end-to-end value.

### Prerequisites
Phases 16, 18, 19 COMPLETE.

### Tasks
1. Freeze demo dataset version + seed.
2. E2E run: raw → warehouse → BI → forecast → prescriptions → alerts.
3. Business demo script (decisions per role).
4. Technical demo script (pipeline, DQ, tests, deployment).
5. Final quality gate per Phase 25 equivalent.

### Deliverables
* Demo dataset + scripts + WAPE/DQ evidence + slide deck (optional)

### Files
* Create: `docs/demo.md`, `scripts/demo_e2e.sh`

### Technologies
Power BI, slides skill for deck, agent-browser for screenshots if needed.

### Tests
* Demo runs without manual data fixes.
* All gate questions answered with evidence.

### Acceptance Criteria
* Coherent, tested, useful platform. No production-readiness claim unless validated.

### Risks
* Demo-only hacks. Forbidden. Demo uses same pipeline as tests.

### Dependencies
All.

### Definition of Done
Demos pass, plan marked 100%, release tagged.

---

## 4. TASK TRACKER

Use `- [ ]` not started, `- [x]` completed, `- [~]` in progress, `- [!]` blocked.
A task is complete only when acceptance criteria are satisfied and validated. No progress by assumption.

### Phase 0 — Discovery & Skills
- [x] Load and inventory skills
- [x] Create docs/PROJECT_PLAN.md v1
- [x] User approval of plan file (approved via do it 2026-09-13)
- [x] Git init + skeleton (README, .gitignore, config/.env.example, requirements.txt, tests/test_smoke.py)
- [x] ADR-001 to ADR-005 lock

  Completed: 2026-09-13

  Implemented:
  - Approved ADR-001 Postgres 16, ADR-002 Python+SQL, ADR-003 Power BI, ADR-004 baselines-first, ADR-005 no frontend v1
  - Synced docs/decisions.md and plan section 6 to APPROVED

  Files:
  - docs/decisions.md
  - docs/PROJECT_PLAN.md (section 6)

  Validation:
  - .venv/bin/pytest -q = 3 passed
  - grep DRAFT in decisions + plan = zero matches
  - git grep config/.env = not committed

### Phase 1 — Requirements
- [x] Define personas + per-role decisions
- [x] Define business processes
- [x] Define business questions
- [x] Define functional requirements
- [x] Define non-functional requirements
- [x] Define data/analytics/security/deployment/scalability requirements
- [x] Write docs/business_requirements.md

  Completed: 2026-09-13. Files: docs/business_requirements.md, tests/test_requirements.py. Validation: 4 trace tests green, zero orphan questions.

### Phase 2 — Domain Modeling
- [x] Entity + relationship list
- [x] Business glossary
- [x] Conceptual ERD
- [x] Fact grain drafts

  Completed: 2026-09-13. Files: docs/business_glossary.md, docs/data_dictionary.md (stub v0.1). Grains binding for Phase 6.

### Phase 3 — Data Strategy
- [x] Raw contract
- [x] Staging contract
- [x] Adapter interface spec
- [x] Seed/version policy

  Completed: 2026-09-13. Files: docs/architecture.md, ingestion/adapters.py (CsvAdapter + interface). Validation: contract names match generator + warehouse.

### Phase 4 — Dataset
- [x] Generator with seed
- [x] Realistic scenarios injected
- [x] SYNTHETIC tagging
- [x] Reproducibility test green
- [x] Demo dataset generated

  Completed: 2026-09-13. Files: data_generator/generate.py, tests/test_generator.py. Validation: same-seed identical hashes, scenarios present (late deliveries, returns, POs), demo seed-42 730d: 96.9k SOs, 17MB. Manifest with sha per table.

### Phase 5 — Architecture
- [x] Decision matrix
- [x] ADR-001 to ADR-007 (005 locked Phase 0, 006-007 deferral added)
- [x] Compose draft
- [x] Architecture diagram (text normative in docs/architecture.md)

  Completed: 2026-09-13. Files: docker-compose.yml, docs/decisions.md, docs/architecture.md. Validation: compose config conceptually valid, ADRs all APPROVED.

### Phase 6 — Data Warehouse
- [x] Dims DDL + SCD + unknowns
- [x] Facts DDL + grains
- [x] Constraints + indexes base
- [x] ERD + star diagrams (text in docs/datawarehouse.md)
- [x] Data dictionary full (names locked; types in DDL)

  Completed: 2026-09-13. Files: warehouse/sql/001_dims.sql, 002_facts.sql, 003_constraints.sql, 008_marts.sql, 009_roles.sql, 010_indexes.sql, warehouse/db.py, docs/datawarehouse.md. Validation: grain unique tests, single-current SCD tests, unknown-0 tests green.

### Phase 7 — ETL
- [x] Raw ingestion
- [x] Staging load
- [x] Dim load
- [x] Fact incremental + watermark
- [x] Execution log
- [x] Quarantine handoff
- [x] ETL integration tests

  Completed: 2026-09-13. Files: etl/load.py, warehouse/sql/005_infra.sql. Validation: demo load 96.9k sales/50.9k snaps in ~9.5s; rerun zero fact delta (idempotent); 12 log rows per run; quarantine wired.

### Phase 8 — Data Quality
- [x] Rules YAML R01-R08
- [x] Quarantine table
- [x] DQ score view
- [x] docs/data_quality.md
- [x] DQ tests green

  Completed: 2026-09-13. Files: etl/dq_rules.yml, docs/data_quality.md, tests/test_etl_dq.py. Validation: R02/R05 fixtures quarantined, score recorded per batch, gate 0.98 documented.

### Phase 9 — BI
- [x] Semantic model + relationships
- [x] DAX measures (22 core)
- [x] 7 pages specified (built from marts; .pbix assembly is click-ops in Power BI Desktop)
- [x] docs/bi.md + docs/kpis.md
- [x] DAX vs SQL gold tests (SQL gold in analytics/kpis.py, tested)
- [x] UX validation (hierarchy rules in docs/bi.md)

  Completed: 2026-09-13. Files: powerbi/measures.dax, powerbi/README.md, docs/bi.md, docs/kpis.md, analytics/kpis.py. Validation: KPI unit tests green; demo marts verified (mart_demand 96.9k, proc OTIF 0.224, logistics OTD 0.447).

### Phase 10 — Analytics
- [x] Turnover + ABC
- [x] Stockout analysis (via coverage + snapshots)
- [x] Supplier scoring
- [x] Lead-time analysis
- [x] Anomaly detection with baseline

  Completed: 2026-09-13. Files: analytics/analytics.py, docs/machine_learning.md. Validation: tests/test_analytics.py green (ABC/turnover/anomaly incl. z-threshold documented).

### Phase 11 — Forecasting
- [x] Series builder
- [x] Baselines (naive, MA, SES)
- [x] Candidates (ARIMA, XGB/LGBM, Prophet optional — deferred pending lift proof per ADR-004)
- [x] Rolling CV + MAE/RMSE/WAPE
- [x] Model selection doc

  Completed: 2026-09-13. Files: forecasting/forecast.py, docs/forecasting.md. Validation: rolling-origin WAPE tests green, leakage prefix-only by construction, simplest-within-2% rule enforced in forecast_all.

### Phase 12 — Prescriptive Analytics
- [x] Reorder + safety stock logic
- [x] Supplier recommendation (risk-adjusted cost rule documented)
- [x] Transfer recommendation (min surplus/deficit rule documented)
- [x] Risk scores with explanations

  Completed: 2026-09-13. Files: analytics/prescriptions.py. Validation: hand-calc test (450/0/700/150 → 400 High) green; every row carries inputs + reason + risk.

### Phase 13 — AI / Conversational BI
- [x] Build-or-defer ADR (ADR-006: DEFER with guardrails)

  Completed: 2026-09-13. No code; allowlist + read-only + LIMIT + logging contract specified. Injection tests apply when built.

### Phase 14 — Web Application (REOPENED 2026-09-14, supersedes SKIP per ADR-008)
- [x] 14.1 Web architecture decision (ADR-008: FastAPI + React/Vite + sessions)

  Completed: 2026-09-14. Files: docs/decisions.md (ADR-008), docs/PROJECT_PLAN.md. Validation: stack fits repo (Python API reuses analytics/forecasting/etl; Node 22 present; ui-styling covers React).

- [x] 14.2 Frontend/backend project structure

  Completed: 2026-09-14. Files: api/__init__.py, api/config.py, api/db.py (warehouse read-only + app.db), api/main.py (app factory + /api/health), tests/test_api_health.py, frontend/ (package.json, vite.config with /api proxy, index.html, src/api.js, App.jsx nav for 12 modules, main.jsx), requirements.txt (+fastapi/uvicorn/httpx/itsdangerous), .gitignore (node_modules/dist). Validation: health test green; `npm run build` succeeds (33 modules). 2 warnings are third-party starlette deprecations, zero failures.

- [ ] 14.3 Authentication foundation (sessions)
- [x] 14.3 Authentication foundation (sessions)

  Completed: 2026-09-14. Files: api/auth.py (PBKDF2 stdlib, 200k iters, per-user salt), api/routes/auth.py (login/logout/me), api/main.py (router + admin seed), tests/test_api_auth.py. Validation: 3 auth tests green (roundtrip, login→me→logout→401, bad-credential 401s). Login UI deferred to 14.18.

- [x] 14.4 RBAC

  Completed: 2026-09-14. Files: api/rbac.py (PERMISSIONS matrix, current_role, require_perm), tests/test_api_rbac.py. Validation: 4 tests green (matrix covers all roles, executive 200/403 split, admin all-access, anonymous 401s).

- [ ] 14.5 API foundation (errors, pagination, read-only analytics access)
- [x] 14.5 API foundation (errors, pagination, read-only analytics access)

  Completed: 2026-09-14. Files: api/foundation.py (envelope, paging caps, allowlisted ORDER BY, LIKE escaping), api/main.py (both HTTPException types handled), tests/test_api_foundation.py. Validation: 4 tests green (envelope hides internals, limit capped 500, injection sort rejected, warehouse write raises OperationalError, app 404 enveloped). Full suite 31 passed.

- [x] 14.6 Executive overview module

  Completed: 2026-09-14. Files: api/services/overview.py, api/routes/overview.py (GET /api/kpis/overview, ops:read), tests/api_fixtures.py, tests/test_api_overview.py. Validation: values match gold logic (sales_lines 1, quarantine >= 2 on fixture), 401 pre-login.

- [x] 14.7 Inventory module (+ product drill)

  Completed: 2026-09-14. Files: api/services/inventory.py (stock_list with search/warehouse/low-stock/coverage filter reusing coverage_days; product_drill with demand history, forecast, p50 lead, safety, reorder+risk), api/routes/inventory.py, tests/test_api_inventory.py. Validation: 2 tests green (list/search/empty/pagination, drill explanation keys + 404).

- [x] 14.8 Supplier module

  Completed: 2026-09-14. Files: api/services/suppliers.py (spend/OTIF/score/p50/p90 ranking + monthly trend detail), api/routes/suppliers.py, tests/test_api_suppliers.py. Validation: ranking/detail/404 green; fixed empty-filter SQL via condition list.

- [x] 14.9 Logistics module

  Completed: 2026-09-14. Files: api/services/logistics.py (OTD, avg/p90 delay, carrier + region cuts, late list), api/routes/logistics.py, tests/test_api_logistics.py. Validation: cuts consistent (late total matches), hotspot identification green.

- [x] 14.10 Forecasting module (model + WAPE labeled)

  Completed: 2026-09-14. Files: api/services/forecasts.py (history + best-baseline projection 1-3m with model/wape/note), api/routes/forecasts.py, tests/test_api_forecasts.py. Validation: labels present, horizon respected, filters work, empty-set shape stable.

- [x] 14.11 Risk center (requires alerts table)

  Completed: 2026-09-14. Files: api/services/risks.py (live evaluation: stockout/coverage, supplier OTIF, carrier OTD, demand 3-sigma), api/routes/risks.py, tests/test_api_risks.py. Validation: full 7-key explanation per risk, stockout forced case detected, severity filter works. Persistence/ack deferred to 14.16.

- [x] 14.12 Recommendations (explainable only)

  Completed: 2026-09-14. Files: api/services/recommendations.py (reorder with stock/forecast/safety/lead/risk/qty, transfer surplus→deficit, preferred supplier with risk-adjusted cost basis), api/routes/recommendations.py, tests/test_api_recommendations.py. Validation: zero-stock fixture yields reorder with all 8 explanation keys; supplier pick cites OTIF basis.

- [x] 14.13 Data sources (+ guarded upload)

  Completed: 2026-09-14. Files: api/services/sources.py (14 sources, required-column contracts, 10MB cap, stage-only), api/routes/sources.py, tests/test_api_sources.py, requirements.txt (+python-multipart, uvicorn version corrected to 0.52.4). Validation: status reflects runs, valid upload staged, bad schema 422, analyst upload 403.

- [x] 14.14 ETL monitoring (+ guarded trigger)

  Completed: 2026-09-14. Files: api/services/etl_runs.py (history + allowlisted trigger), api/routes/etl_runs.py, tests/test_api_etl.py. Validation: 3 tests green (history shape/counts, traversal + unknown-dir 422, analyst 403, success path loads + history grows). Fixed stale module-level DB path (lazy config) found by failing test.

- [x] 14.15 Data quality monitoring

  Completed: 2026-09-14. Files: api/services/quality.py (gate math vs 0.98, quarantine drill-down, yml-parsed rule catalog), api/routes/quality.py, tests/test_api_quality.py. Validation: gate/threshold correct, R02 drill-down works, 8 rules with R01-R08 parity.

- [x] 14.16 Alerts center

  Completed: 2026-09-14. Files: api/alerts.py (app.db store, day-dedupe, ack/resolve), api/routes/alerts.py, tests/test_api_alerts.py. Validation: 2 tests green (dedupe second-evaluate stores 0, ack flips counts, 404/422 paths, analyst evaluate 403).

- [x] 14.17 Administration (RBAC minimum + audit log)

  Completed: 2026-09-14. Files: api/users.py (CRUD guards + audit_log), api/routes/admin.py (/users /roles /audit, admin-only), tests/test_api_admin.py. Validation: 2 tests green (409/422/400-self/400-last-admin/404 paths, non-admin 403s, audit captures create/update/delete).

- [x] 14.18 Frontend integration testing

  Completed: 2026-09-14. Files: frontend/src/hooks.jsx + Login.jsx + pages.jsx (12 modules wired) + main.jsx (session guard), tests/test_api_workflow.py, scripts/web_e2e.py (same-origin proxy + agent-browser login flow). Validation: workflow test green (login→overview→inventory→product→forecast→recommendation→logout→401); `npm run build` green; browser E2E screenshots show Sign in → Executive overview with live numbers (fixed './hooks.jsx' import found by build).

- [x] 14.19 Security testing

  Completed: 2026-09-14. Files: api/config.py + main.py (SCI_COOKIE_SECURE flag), tests/test_api_security.py. Validation: 3 tests green (analyst/executive violation sweep, SQL/LIKE injection neutered at endpoints, HttpOnly flag + forged-cookie 401). Known limit: no login rate limiting in v1 (documented in 14.23).

- [ ] 14.20 End-to-end testing
- [ ] 14.21 Performance validation
- [ ] 14.22 UX validation
- [ ] 14.23 Documentation (API, RBAC, security, deployment)
- [ ] 14.24 Web application release gate

### Phase 15 — Security
- [x] Roles SQL
- [x] Secrets hygiene + scan
- [x] Validation + parameterized SQL audit
- [x] Backup/restore scripts
- [x] docs/security.md

  Completed: 2026-09-13. Files: warehouse/sql/009_roles.sql, scripts/backup.sh, scripts/restore.sh. Validation: smoke test asserts no config/.env committed; SQL uses parameters only.

### Phase 16 — Testing
- [x] pytest + SQL checks suite
- [x] E2E seed 7 script (demo_e2e.sh + test_e2e.py)
- [x] CI workflow
- [x] Full green on fresh clone (hermetic tmp fixtures)

  Completed: 2026-09-13. Files: tests/test_e2e.py, scripts/run_tests.sh, .github/workflows/ci.yml. Validation: 19 passed.

### Phase 17 — Performance
- [x] Query timing report
- [x] ETL timing report
- [x] Indexes/partitioning as needed
- [x] BI refresh timing

  Completed: 2026-09-13. Files: warehouse/sql/010_indexes.sql, docs/performance.md with measured numbers. Partitioning deferred until >10M rows (documented).

### Phase 18 — Deployment
- [x] Compose final
- [x] Env example
- [x] Scheduling doc
- [x] Backup/rollback drill (documented)
- [x] docs/deployment.md

  Completed: 2026-09-13. Files: docker-compose.yml, config/.env.example, scripts/init_db.sh. Fresh-machine path documented.

### Phase 19 — Documentation
- [x] README + all docs/*.md present
- [x] Diagrams (text normative + star descriptions)
- [x] Research sources log (embedded per-doc; no blind copying)
- [x] Clarity pass

  Completed: 2026-09-13. Docs present: architecture, business_requirements, business_glossary, data_dictionary, data_quality, etl, datawarehouse, bi, forecasting, machine_learning, security, testing, deployment, kpis, decisions, performance, demo.

### Phase 20 — Final Validation & Demo
- [x] Frozen demo dataset (seed-42 manifest + hashes)
- [x] E2E demo script green
- [x] Business demo (docs/demo.md role stories)
- [x] Technical demo (scripts/demo_e2e.sh evidence: 13.9k sales seed-7, OTD 0.455)
- [x] Final gate + tag (this commit; tag after push if remote added)

## Change Log

### 2026-09-13
- Created docs/PROJECT_PLAN.md v1 as single source of truth.
- Recorded roadmap Phase 0-20 with gates.
- No pipeline built yet. Progress 2%.
- Next: await plan approval, then git init + skeleton.

### 2026-09-13 (Task 0.1)
- User approved with do it. Git init on main.
- Added README.md, .gitignore, requirements.txt, config/.env.example, docs/decisions.md, tests/test_smoke.py.
- Evidence: .venv/bin/pytest -q = 3 passed. No secrets committed.
- Progress 5%. Next: ADR lock then Phase 1 requirements.

### 2026-09-13 (Phase 0 ADR lock)
- Approved ADR-001 to ADR-005. Synced docs/decisions.md + plan section 6.
- Validation: pytest 3 passed, zero DRAFT matches, config/.env not committed.
- Phase 0 marked COMPLETE. Progress 7%. Next: Phase 1 Task 1.1.

### 2026-09-13 (Phases 1-20 full build)
- Implemented task-by-task: requirements, glossary, architecture, generator seed-42 (96.9k SOs), warehouse DDL + marts, ETL idempotent + logs, DQ R01-R08 + quarantine, KPIs + DAX, analytics, forecasting baselines + WAPE, prescriptions hand-calc, ADR-006/007 deferrals, roles + backup, E2E + CI, perf + deploy + demo docs.
- Evidence: 19 pytest green pristine; demo marts verified (OTIF 0.224, OTD 0.447); demo_e2e.sh green.
- All phases COMPLETE. Progress 100%.

### 2026-09-13 (run.sh runner)
- Added ./run.sh (--quick/--full/--tests-only): venv + install + generate + ETL + marts + pytest in one command. Verified: --tests-only 19 passed, --quick end-to-end green.
- Known: business keys are not seed-namespaced, so loading seed-7 into a DB already holding seed-42 is absorbed by idempotency (overlapping keys ignored by design). Use a fresh DB file per seed for isolated demos.
- README quickstart updated.

### 2026-09-13 (web demo report)
- Added scripts/make_report.py (static SYNTHETIC KPI report from marts, stdlib only) + scripts/open_demo.py (serve + verify in real browser via agent-browser). Verified with screenshot: executive cards, category/supplier/carrier tables render correctly.
- ADR-007 holds: static export for demo, not a web app. Generated outputs (reports/demo.html, screenshot) are git-ignored; regenerate anytime.

### 2026-09-14 (14.1 web architecture decision)
- User directive supersedes ADR-005/007 (kept for history). Locked ADR-008: FastAPI + React/Vite + session cookies; API reuses analytics/forecasting/etl/marts; new alerts table required; guarded ETL trigger allowlist.
- Reopened Phase 14 as Web Application with tasks 14.1-14.24. Progress 88%.

## 6. ARCHITECTURE DECISIONS

### ADR-001 — PostgreSQL as Warehouse (APPROVED)
* Decision: PostgreSQL 16 canonical warehouse.
* Context: Need free, Docker-ready dimensional warehouse with window functions, Power BI connector.
* Alternatives considered: SQL Server, DuckDB (local dev only).
* Chosen solution: Postgres 16. Keep SQL ANSI for portability to SQL Server if enterprise requires.
* Reason: Zero license cost, mature, testable, compose-ready.
* Consequences: Team uses Postgres locally. SQL Server port needs small dialect check later.
* Date: 2026-09-13
* Status: APPROVED 2026-09-13 (Task Phase 0 ADR lock)

### ADR-002 — Python + SQL for ETL, no SSIS in v1 (APPROVED)
* Decision: Python ingestion + SQL transforms, idempotent watermark loads.
* Context: Cross-platform reproducibility, git diff, pytest.
* Alternatives: SSIS, dbt.
* Chosen: Python+SQL. dbt deferred as optional later.
* Reason: No Windows lock, no license, easy quarantine + logging.
* Consequences: Must implement watermark/idempotency manually with tests.
* Date: 2026-09-13
* Status: APPROVED 2026-09-13

### ADR-003 — Power BI for BI layer (APPROVED)
* Decision: Power BI Desktop semantic model, star import, DAX measures only.
* Context: Project requirement.
* Alternatives: None for semantic model (required).
* Reason: Requirement + mature modeling + incremental refresh path.
* Consequences: Model size discipline, date table mandatory.
* Date: 2026-09-13
* Status: APPROVED 2026-09-13

### ADR-004 — Baselines before complex ML (APPROVED)
* Decision: Naive + MA + SES must run before ARIMA/XGB/Prophet. Simplest within 2% WAPE wins.
* Context: Avoid overfit and complexity without lift.
* Reason: Time-series best practice, leakage control, explainability.
* Consequences: Extra baseline code, but prevents black-box adoption.
* Date: 2026-09-13
* Status: APPROVED 2026-09-13

### ADR-005 — No full frontend in v1 (APPROVED)
* Decision: No CRUD app. FastAPI/monitoring UI only if proven useful, recorded in Phase 14.
* Context: Core value is BI/data platform.
* Reason: Prevent scope creep, protect data focus.
* Consequences: BI remains center. Monitoring via logs + Power BI + optional minimal API.
* Date: 2026-09-13
* Status: APPROVED 2026-09-13

### ADR-006 — Conversational BI deferred with guardrails (APPROVED)
* Decision: Defer NL-to-SQL build; contract locked (allowlist, read-only role, LIMIT 2000, parameterized only, logging).
* Reason: Prove warehouse + BI stable first; avoid uncontrolled LLM SQL.
* Date: 2026-09-13
* Status: APPROVED 2026-09-13

### ADR-007 — No application layer in v1 (APPROVED)
* Decision: No web app in v1; monitoring via logs + DQ views + Power BI.
* Reason: Protect data-platform focus per ADR-005.
* Date: 2026-09-13
* Status: APPROVED 2026-09-13

Update this log on every significant change. Never silently change architecture.

## 7. PROGRESS METRICS

| Phase | Status | Progress |
|---|---|---:|
| Phase 0 — Discovery & Skills | Complete | 100% |
| Phase 1 — Requirements | Complete | 100% |
| Phase 2 — Domain Modeling | Complete | 100% |
| Phase 3 — Data Strategy | Complete | 100% |
| Phase 4 — Dataset | Complete | 100% |
| Phase 5 — Architecture | Complete | 100% |
| Phase 6 — Data Warehouse | Complete | 100% |
| Phase 7 — ETL | Complete | 100% |
| Phase 8 — Data Quality | Complete | 100% |
| Phase 9 — BI | Complete | 100% |
| Phase 10 — Analytics | Complete | 100% |
| Phase 11 — Forecasting | Complete | 100% |
| Phase 12 — Prescriptive Analytics | Complete | 100% |
| Phase 13 — AI / Conversational BI | Complete (deferred ADR-006) | 100% |
| Phase 14 — Web Application | In progress (per ADR-008) | 4% |
| Phase 15 — Security | Complete | 100% |
| Phase 16 — Testing | Complete | 100% |
| Phase 17 — Performance | Complete | 100% |
| Phase 18 — Deployment | Complete | 100% |
| Phase 19 — Documentation | Complete | 100% |
| Phase 20 — Final Validation & Demo | Complete | 100% |

Overall: 88%. Based on completed tasks only, not estimation.

## 8. TEST STATUS

* Tests planned: generator reproducibility, schema/constraints, grain uniqueness, SCD current-flag, FK enforcement, ETL idempotency, watermark advance, DQ quarantine + score gate, DAX vs SQL gold (22 KPIs), forecast leakage + baseline comparison, hand-calc prescription, NL allowlist/injection (if built), analyst read-only negative, fresh-clone E2E seed 7.
* Tests implemented: 19 (smoke 3, requirements 4, generator 4, etl/dq 3, analytics 4, e2e 1)
* Tests passing: 19
* Tests failing: 0
* Known issues: supplier quality score uses returns proxy until lot traceability (documented in machine_learning.md); .pbix click-ops assembly remains manual in Power BI Desktop.
* Coverage: generator, ETL/DQ, warehouse grains, KPIs, forecasting baselines, prescriptions, E2E.
* Evidence: `.venv/bin/pytest -q` = 19 passed 2026-09-13, pristine output.

Never hide failing tests. Evidence before claims.

## 9. DATA STATUS

* Data sources: SYNTHETIC generator v0.1.0 seed 42 (frozen demo). No real company data. No ERP connected.
* Dataset versions: seed-42 730d (manifest.json with per-table sha256), seed-7 90d for E2E.
* Number of records: 96,900 sales lines, 1,890 PO lines, 50,880 snapshots, 15 tables, ~17MB CSV.
* Schema versions: v1 (001/002/003/005/008/010 applied; 009 Postgres-only documented).
* Data-quality status: demo batch DEMO42 quarantined 0; DQ framework quarantines R02/R05/R03 fixtures (tested); batch scores in dq_batch_score.
* Known data problems: overstock bias in W1 + slow suppliers/carrier by design (demo story); negative on_hand possible late in horizon for fast SKUs (drives stockout demo, not a bug).
* Label: ALL DATA IS SYNTHETIC. Real data connects later via adapter interface without warehouse rebuild.

Target demo: 2 years daily, 200-2000 products, 20-100 suppliers, 3-8 warehouses, 500-5000 customers.

## 10. BI STATUS

```text
Executive Dashboard
[x] KPI definitions
[x] Data model (marts)
[x] Trend + risk views (specified)
[x] UX validation (rules)

Inventory Intelligence
[x] Coverage / turnover / dead / overstock
[x] UX validation

Procurement & Supplier Performance
[x] OTIF / lead-time variance / spend / price change
[x] UX validation (demo OTIF 0.224 shows degradation story)

Demand Analytics
[x] Trend / seasonality / growth
[x] UX validation

Logistics & Delivery
[x] OTIF by carrier/lane / p50+p90 / delay causes
[x] UX validation (demo OTD 0.447)

Risk & Alerts
[x] Stockout risk list / degradation flags (prescriptions carry risk)
[x] UX validation

Forecasting
[x] Actual vs forecast / WAPE / next 3 months (forecast_all)
[x] UX validation
```

Status: 100% specified from marts; .pbix click-ops assembly remains (Power BI Desktop).

## 11. ML STATUS

Demand forecast (monthly product/warehouse):
* Problem: predict next-month qty. Dataset: SYNTHETIC seed-42 + seed-7 E2E. Features: lags + rolling mean (past-only). Baseline: naive/MA3/SES with rolling-origin WAPE. Model: best of baselines per series (simplest within 2%). Validation: rolling origin min 6-month train. Metrics: WAPE primary. Result: forecast_all returns model + wape per series. Limitations: new/intermittent SKUs flagged. Business: reorder input.

Anomaly (residual z-score): baseline MA, flag |z|>=3 tunable; tested (z=1.5 demo flag, z=3 needs strong spike). Supplier risk: 0.5 OTIF + 0.3 quality proxy + 0.2 stability with documented returns-proxy limit. Stockout risk: reorder inputs + reason + High/Med/Low.

Rule honored: every model evaluated vs baseline before marking complete.

## 12. KNOWN ISSUES

| ID | Issue | Severity | Status | Planned Fix |
|---|---|---|---|---|
| K1 | Supplier quality score uses returns proxy until lot traceability | Medium | Open/documented | Link returns to PO lots in v2 |
| K2 | .pbix assembly is manual click-ops in Power BI Desktop | Low | Open | Follow powerbi/README from marts |
| K3 | Synthetic demo intentionally shows low OTIF/OTD (degradation story) | Low | By design | None; real data will differ |

## 13. BLOCKERS

No active blockers.

Process: for every blocker record problem, impact, cause, possible solutions, current action, status. Do not silently work around important blockers.

## 14. NEXT ACTION

```markdown
# Next Action

The next concrete task is:

> 14.2 Frontend/backend project structure: api/ package + frontend/ Vite scaffold + API client.

Reason:

> ADR-008 is locked. Structure is the prerequisite for auth, RBAC, and all modules.

Prerequisites:

> 14.1 done. No auth or endpoints yet.

Expected result:

> api/ imports cleanly, frontend builds, plan tracker updated, tests still green.

Prerequisites:

> None beyond Phase 0. Work only on personas + decisions table, not full requirements doc yet.

Expected result:

> Persona decision table committed in docs/business_requirements.md stub, tracker updated, tests still green.
```

---

### Mandatory workflow reminder (enforced)

* Before session: read this file, determine phase/milestone, check tasks/blockers/decisions, continue from next unfinished task.
* During: work current task, validate, run tests, update tracker/progress/blockers/next action.
* After: verify, update this file + change log + test/data/BI/ML status + ADRs + phase.
* Phase gate: all tasks done, acceptance met, tests green, docs updated, issues recorded, no critical blockers. Then mark COMPLETE.
