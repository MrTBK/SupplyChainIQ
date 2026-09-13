-- 002_facts.sql — grain is normative (see docs/datawarehouse.md)
-- FactSales: one row per sales order line.
-- FactPurchases: one row per PO line receipt.
-- FactInventorySnapshot: one row per product/warehouse/day.
-- FactInventoryMovement: one row per movement event.
-- FactShipments: one row per shipment line.
-- FactDeliveries: one row per delivery line.
-- FactReturns: one row per return line.

CREATE TABLE IF NOT EXISTS fact_sales (
  sales_sk INTEGER PRIMARY KEY,
  so_id TEXT NOT NULL,
  line_no INTEGER NOT NULL,
  product_sk INTEGER NOT NULL DEFAULT 0,
  warehouse_sk INTEGER NOT NULL DEFAULT 0,
  customer_sk INTEGER NOT NULL DEFAULT 0,
  date_key TEXT NOT NULL DEFAULT '1900-01-01',
  qty INTEGER NOT NULL CHECK (qty >= 0),
  unit_price REAL NOT NULL CHECK (unit_price >= 0),
  net_amount REAL NOT NULL,
  UNIQUE (so_id, line_no)
);

CREATE TABLE IF NOT EXISTS fact_purchases (
  purchase_sk INTEGER PRIMARY KEY,
  po_id TEXT NOT NULL,
  line_no INTEGER NOT NULL,
  supplier_sk INTEGER NOT NULL DEFAULT 0,
  warehouse_sk INTEGER NOT NULL DEFAULT 0,
  product_sk INTEGER NOT NULL DEFAULT 0,
  order_date_key TEXT NOT NULL,
  receipt_date_key TEXT NOT NULL,
  ordered_qty INTEGER NOT NULL CHECK (ordered_qty >= 0),
  received_qty INTEGER NOT NULL CHECK (received_qty >= 0),
  unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
  late_days INTEGER NOT NULL,
  UNIQUE (po_id, line_no)
);

CREATE TABLE IF NOT EXISTS fact_inventory_snapshot (
  snap_sk INTEGER PRIMARY KEY,
  snapshot_date_key TEXT NOT NULL,
  product_sk INTEGER NOT NULL DEFAULT 0,
  warehouse_sk INTEGER NOT NULL DEFAULT 0,
  on_hand INTEGER NOT NULL,
  reserved INTEGER NOT NULL DEFAULT 0,
  available INTEGER NOT NULL,
  unit_cost REAL NOT NULL,
  UNIQUE (snapshot_date_key, product_sk, warehouse_sk)
);

CREATE TABLE IF NOT EXISTS fact_inventory_movement (
  movement_sk INTEGER PRIMARY KEY,
  movement_id TEXT NOT NULL UNIQUE,
  event_date_key TEXT NOT NULL,
  product_sk INTEGER NOT NULL DEFAULT 0,
  warehouse_sk INTEGER NOT NULL DEFAULT 0,
  qty_delta INTEGER NOT NULL,
  reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_shipments (
  shipment_sk INTEGER PRIMARY KEY,
  shipment_id TEXT NOT NULL UNIQUE,
  so_id TEXT NOT NULL,
  carrier_sk INTEGER NOT NULL DEFAULT 0,
  shipment_date_key TEXT NOT NULL,
  shipped_qty INTEGER NOT NULL CHECK (shipped_qty >= 0),
  freight_cost REAL NOT NULL CHECK (freight_cost >= 0)
);

CREATE TABLE IF NOT EXISTS fact_deliveries (
  delivery_sk INTEGER PRIMARY KEY,
  shipment_id TEXT NOT NULL UNIQUE,
  promised_date_key TEXT NOT NULL,
  delivery_date_key TEXT NOT NULL,
  delivered_qty INTEGER NOT NULL CHECK (delivered_qty >= 0),
  on_time INTEGER NOT NULL,
  delay_days INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_returns (
  return_sk INTEGER PRIMARY KEY,
  return_id TEXT NOT NULL UNIQUE,
  so_id TEXT NOT NULL,
  product_sk INTEGER NOT NULL DEFAULT 0,
  qty INTEGER NOT NULL CHECK (qty >= 0),
  reason TEXT NOT NULL
);
