# Data Lineage — DataCo → API → Frontend

Raw `DataCo/DataCoSupplyChainDataset.csv` (untouched, 53 cols)
→ `ingestion/dataco_adapter.py` (file/schema validation + profiling JSON, PII dropped)
→ `stg_dataco` (typed staging, one row per Order Item + parsed ISO dates)
→ `etl/load_dataco.py`:
  - dims: dim_date / dim_product / dim_customer / dim_category /
    dim_region / dim_market / dim_department / dim_shipping_mode
  - facts: fact_sales (so_id, line_no, qty, unit_price, net_amount, date_key, order_status)
    / fact_shipments (shipment per line: ship date, mode, real/sched days)
    / fact_deliveries (delay_days = real − sched, on_time, delivery status)
→ DQ: `dq_rules.yml` R01–R08 (kept) + R09–R15 (dataco); rejects → `dq_quarantine`
→ Warehouse `data/warehouse.db` + `etl_execution_log` + `dq_batch_score`
→ Analytics:
  - `analytics/kpis.py` revenue/orders/units/AOV/late-rate/delay/mode/region/category
  - `api/services/logistics.py` mode + region cuts (no fake carriers)
  - `api/services/risks.py` pre-outcome features only
  - `forecasting/forecast.py` monthly demand from fact_sales
→ API `/api/kpis/overview`, `/api/logistics/*`, `/api/risks`, `/api/forecasts`,
  `/api/sources`, `/api/etl-runs`, `/api/quality`
→ Frontend Overview/Logistics/Forecasts/Risks/Recommendations/Alerts/Sources/ETL/Quality
  + header `Dataset 2015-01-01–2018-01-31 · DataCo Smart Supply Chain · Last processed <ETL ts>`

Unsupported (empty DDL, hidden UI): dim_supplier / dim_warehouse positions /
fact_purchases / fact_inventory_snapshot+ movement / fact_returns.
