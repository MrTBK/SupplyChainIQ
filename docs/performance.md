# Performance — SupplyChainIQ (measured 2026-09-13, demo seed-42 SQLite)

* ETL full load 96.9k sales + 50.9k snapshots: ~9.5s first run, ~7.8s idempotent rerun (local).
* Generator 730d/120 products: ~15s, 17MB CSV.
* Suite 18 tests: ~4s.
* Queries: indexed FK+date (010_indexes.sql). Top BI queries EXPLAIN: fact_sales by product/wh/date uses ix_sales_prod_wh_date; snapshot latest uses ix_snap_prod_wh_date. Partitioning deferred until >10M rows. Power BI: import needed columns only, monthly refresh.
