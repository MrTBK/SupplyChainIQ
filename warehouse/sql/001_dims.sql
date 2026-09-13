-- 001_dims.sql — ANSI + SQLite/Postgres compatible
-- Unknown member 0 per dimension. SCD2 for product/supplier, SCD1 others.

CREATE TABLE IF NOT EXISTS dim_date (
  date_key TEXT PRIMARY KEY,
  full_date TEXT NOT NULL,
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  day INTEGER NOT NULL,
  week INTEGER NOT NULL,
  weekday INTEGER NOT NULL,
  month_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_product (
  product_sk INTEGER PRIMARY KEY,
  product_id TEXT NOT NULL,
  sku TEXT NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  standard_cost REAL NOT NULL,
  valid_from TEXT NOT NULL,
  valid_to TEXT,
  is_current INTEGER NOT NULL DEFAULT 1
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_product_current ON dim_product(product_id) WHERE is_current = 1;

CREATE TABLE IF NOT EXISTS dim_supplier (
  supplier_sk INTEGER PRIMARY KEY,
  supplier_id TEXT NOT NULL,
  name TEXT NOT NULL,
  rating_tier TEXT NOT NULL,
  valid_from TEXT NOT NULL,
  valid_to TEXT,
  is_current INTEGER NOT NULL DEFAULT 1
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_supplier_current ON dim_supplier(supplier_id) WHERE is_current = 1;

CREATE TABLE IF NOT EXISTS dim_warehouse (
  warehouse_sk INTEGER PRIMARY KEY,
  warehouse_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_customer (
  customer_sk INTEGER PRIMARY KEY,
  customer_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_carrier (
  carrier_sk INTEGER PRIMARY KEY,
  carrier_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL
);

-- Unknown members (grain protection for late/unknown FKs)
-- Inserted by ETL seed step; kept here as documentation of key 0 contract.
