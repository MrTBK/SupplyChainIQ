# Business Requirements — SupplyChainIQ

Status: APPROVED 2026-09-13 (Phase 1). All data in v1 is SYNTHETIC.

## 1. Personas and Per-Role Decisions

| Persona | Decisions | Grain needed | Latency |
|---|---|---|---|
| Executive | Continue/pause/intervene by region/category; approve safety-stock budget | Category, region, month | Weekly |
| Supply Chain Mgr | What to reorder, how much, from which supplier; what to transfer | Product/warehouse, day | Daily |
| Procurement Mgr | Which supplier to keep/renegotiate/replace; contract price action | Supplier/product, month | Weekly |
| Inventory Mgr | Where is overstock, dead stock, stockout risk; count priorities | Product/warehouse, day | Daily |
| Warehouse Mgr | What to receive, put away, count, move | Product/warehouse, day | Daily |
| Logistics Mgr | Which carrier/lane fails; expedite which shipment | Carrier/lane, shipment | Daily |
| BI Analyst | Why did KPI move; drill by dimensions | All dims, ad hoc | Ad hoc |
| Data Engineer | Did batch succeed; what quarantined; rerun what | Batch/table/run | Per run |
| SysAdmin | Who accesses what; backup/restore status | User/system | Per change |

No single UI serves all. Engineers get run logs. Managers get recommendations with reasons. Executives get trends + exceptions.

## 2. Business Processes

* Procure-to-pay: requisition → PO → receipt → return (quality).
* Plan-to-stock: forecast → safety stock → reorder point → transfer.
* Order-to-cash: sales order → shipment → delivery → return.
* Record-to-report: raw → staging → warehouse → mart → KPI.

## 3. Business Questions (must all trace to KPIs in docs/kpis.md)

Inventory: current value? low-stock? overstocked? dead stock? highest turnover? excess by warehouse? stockout rate?
Procurement: best/worst suppliers? consistently late? avg lead time? defect rate? spend by supplier? price rising?
Demand: increasing/declining? next month? seasonal?
Logistics: late deliveries? best carrier? longest lanes? delay drivers?
Decision: what/when to reorder? which supplier? stockout risk? where to move excess?

## 4. Functional Requirements

* FR-01 ingest CSV/Excel/API-stub into immutable Raw with batch_id.
* FR-02 validate + quarantine with rule_id; DQ score per batch; threshold 0.98 blocks promotion.
* FR-03 incremental SCD1/SCD2 dim load + fact load with watermark; idempotent rerun; execution log per run.
* FR-04 star schema queryable from Power BI import; 22 core KPIs defined; 7 pages.
* FR-05 forecast monthly qty per product/warehouse 1-3 months with baseline comparison + WAPE.
* FR-06 explainable prescriptions (reorder, safety, supplier, transfer, risk) with inputs shown.
* FR-07 alert feed with severity + explanation + action, deduped per entity/condition/day.

## 5. Non-Functional Requirements

* Reproducibility: same seed → identical dataset hashes.
* Idempotency: rerun same batch_id → zero fact delta.
* Performance demo targets: BI p95 < 3s, ETL demo < 10 min, model < 500MB.
* Maintainability: stdlib-first Python, ANSI SQL, Docker Compose, pytest suite.
* Auditability: every rejected row has reason; every recommendation has inputs.

## 6. Data Requirements

2 years daily history; 200-2000 products, 20-100 suppliers, 3-8 warehouses, 500-5000 customers. Entities listed in docs/business_glossary.md. Source keys preserved in staging only.

## 7. Analytics Requirements

Turnover, ABC (A 80/B 15/C 5 revenue), stockout analysis, supplier score (OTIF 50 + quality 30 + price stability 20), lead-time p50/p90, z-score + IsolationForest-equivalent residual check after baseline, forecasting per docs/forecasting.md.

## 8. Security Requirements

Roles loader/analyst-read-only/admin; secrets via env only; parameterized SQL; read-only analytics user; audit log; nightly dump procedure. Details docs/security.md.

## 9. Deployment Requirements

Docker Compose Postgres 16 + optional API; env example; cron schedule + Airflow path; backup/restore + rollback drill. Details docs/deployment.md.

## 10. Scalability Requirements

Partition facts by month when >10M rows; indexes on FK+date; Power BI incremental refresh ready; no streaming in v1.

## 11. Traceability (question → KPI → mart → source)

| Question | KPI | Mart | Source |
|---|---|---|---|
| Current inventory value? | Inventory Value | mart_inventory | snapshots |
| Low-stock? | Coverage Days, Stockout Risk | mart_inventory, mart_risk | snapshots + forecast |
| Overstocked/dead? | Overstock Qty, Dead Stock Value | mart_inventory | snapshots + sales |
| Turnover? | Turnover | mart_inventory | sales + snapshots |
| Stockout rate? | Stockout Rate | mart_inventory | snapshots |
| Supplier best/worst? | Supplier OTIF, Risk Score | mart_procurement | purchases + returns |
| Late suppliers? | Avg Lead Time, Variance | mart_procurement | purchases |
| Defect rate? | Defect Return Rate | mart_procurement | returns |
| Spend? | Spend by Supplier | mart_procurement | purchases |
| Prices rising? | Price Change | mart_procurement | contracts/purchases |
| Demand trend/seasonal/next? | Demand, Growth, Forecast, WAPE | mart_demand | sales + forecast |
| Late deliveries/best carrier/longest lane? | On-Time Delivery, Avg Delivery Time, p90 | mart_logistics | shipments + deliveries |
| What/when reorder, which supplier, risk, transfer? | Reorder Qty, Safety Stock, Supplier pick, Transfer, Risk Score | mart_risk | snapshots + forecast + contracts |

Zero orphan questions. Out-of-scope explicitly: real-time tracking, order entry, IoT streaming.
