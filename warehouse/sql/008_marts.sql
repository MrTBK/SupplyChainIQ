-- 008_marts.sql — BI/analytics read layer (views only)
CREATE VIEW IF NOT EXISTS mart_inventory AS
SELECT s.snapshot_date_key AS date_key, p.product_id, p.category, w.warehouse_id, w.region,
       s.on_hand, s.reserved, s.available, s.unit_cost, s.available * s.unit_cost AS line_value
FROM fact_inventory_snapshot s
JOIN dim_product p ON p.product_sk = s.product_sk
JOIN dim_warehouse w ON w.warehouse_sk = s.warehouse_sk;

CREATE VIEW IF NOT EXISTS mart_procurement AS
SELECT f.po_id, f.order_date_key, f.receipt_date_key, sup.supplier_id, p.product_id, w.warehouse_id,
       f.ordered_qty, f.received_qty, f.unit_cost, f.late_days
FROM fact_purchases f
JOIN dim_supplier sup ON sup.supplier_sk = f.supplier_sk
JOIN dim_product p ON p.product_sk = f.product_sk
JOIN dim_warehouse w ON w.warehouse_sk = f.warehouse_sk;

CREATE VIEW IF NOT EXISTS mart_logistics AS
SELECT s.shipment_id, s.shipment_date_key, c.carrier_id, d.promised_date_key, d.delivery_date_key,
       s.shipped_qty, s.freight_cost, d.on_time, d.delay_days
FROM fact_shipments s LEFT JOIN fact_deliveries d ON d.shipment_id = s.shipment_id
LEFT JOIN dim_carrier c ON c.carrier_sk = s.carrier_sk;

CREATE VIEW IF NOT EXISTS mart_demand AS
SELECT f.date_key, p.product_id, p.category, w.warehouse_id, f.qty, f.net_amount
FROM fact_sales f
JOIN dim_product p ON p.product_sk = f.product_sk
JOIN dim_warehouse w ON w.warehouse_sk = f.warehouse_sk;

CREATE VIEW IF NOT EXISTS mart_risk AS
SELECT s.snapshot_date_key AS date_key, p.product_id, w.warehouse_id, s.available, s.unit_cost
FROM fact_inventory_snapshot s
JOIN dim_product p ON p.product_sk = s.product_sk
JOIN dim_warehouse w ON w.warehouse_sk = s.warehouse_sk;
