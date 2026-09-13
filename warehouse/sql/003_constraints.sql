-- 003_constraints.sql — FKs where engine enforces; SQLite needs PRAGMA foreign_keys=ON (set by ETL).
-- Kept as indexes for portability; logical FKs documented in docs/datawarehouse.md.

CREATE INDEX IF NOT EXISTS ix_fact_sales_product ON fact_sales(product_sk);
CREATE INDEX IF NOT EXISTS ix_fact_sales_wh ON fact_sales(warehouse_sk);
CREATE INDEX IF NOT EXISTS ix_fact_sales_date ON fact_sales(date_key);
CREATE INDEX IF NOT EXISTS ix_fact_purchases_supplier ON fact_purchases(supplier_sk);
CREATE INDEX IF NOT EXISTS ix_fact_purchases_date ON fact_purchases(receipt_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_snap_date ON fact_inventory_snapshot(snapshot_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_snap_prod_wh ON fact_inventory_snapshot(product_sk, warehouse_sk);
CREATE INDEX IF NOT EXISTS ix_fact_mov_date ON fact_inventory_movement(event_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_ship_date ON fact_shipments(shipment_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_del_date ON fact_deliveries(delivery_date_key);
