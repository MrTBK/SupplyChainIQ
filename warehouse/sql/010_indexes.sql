-- 010_indexes.sql — applied after load; measured in docs/performance.md
CREATE INDEX IF NOT EXISTS ix_sales_prod_wh_date ON fact_sales(product_sk, warehouse_sk, date_key);
CREATE INDEX IF NOT EXISTS ix_purch_sup_date ON fact_purchases(supplier_sk, receipt_date_key);
CREATE INDEX IF NOT EXISTS ix_snap_prod_wh_date ON fact_inventory_snapshot(product_sk, warehouse_sk, snapshot_date_key);
CREATE INDEX IF NOT EXISTS ix_mov_prod_date ON fact_inventory_movement(product_sk, event_date_key);
