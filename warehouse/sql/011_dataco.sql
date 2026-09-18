-- 011_dataco.sql — DataCo dimensions (SQLite/Postgres compatible).
-- dim_shipping_mode replaces carrier for DataCo (mode only, no carrier id).
-- dim_category / dim_region / dim_market / dim_department are first-class;
-- dim_supplier / dim_warehouse / fact_purchases / inventory / returns DDL stays
-- but remains EMPTY for DataCo (documented gap).

CREATE TABLE IF NOT EXISTS dim_shipping_mode (
  mode_sk INTEGER PRIMARY KEY,
  mode TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_category (
  category_sk INTEGER PRIMARY KEY,
  category_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_region (
  region_sk INTEGER PRIMARY KEY,
  region TEXT NOT NULL UNIQUE,
  market TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS dim_market (
  market_sk INTEGER PRIMARY KEY,
  market TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_department (
  dept_sk INTEGER PRIMARY KEY,
  dept_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL
);

-- staging preserves raw grain: one row per DataCo Order Item
CREATE TABLE IF NOT EXISTS stg_dataco (
  order_id TEXT NOT NULL,
  order_item_id TEXT NOT NULL,
  line_no INTEGER NOT NULL,
  qty INTEGER NOT NULL,
  unit_price REAL NOT NULL,
  net_amount REAL NOT NULL,
  discount REAL NOT NULL DEFAULT 0,
  discount_rate REAL NOT NULL DEFAULT 0,
  benefit REAL NOT NULL DEFAULT 0,
  order_date TEXT NOT NULL,
  ship_date TEXT NOT NULL,
  real_days INTEGER NOT NULL,
  sched_days INTEGER NOT NULL,
  delay_days INTEGER NOT NULL,
  on_time INTEGER NOT NULL,
  delivery_status TEXT NOT NULL,
  order_status TEXT NOT NULL,
  product_id TEXT NOT NULL,
  product_name TEXT NOT NULL,
  category_id TEXT NOT NULL,
  category_name TEXT NOT NULL,
  customer_id TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  customer_segment TEXT NOT NULL DEFAULT '',
  order_region TEXT NOT NULL DEFAULT '',
  market TEXT NOT NULL DEFAULT '',
  order_country TEXT NOT NULL DEFAULT '',
  order_state TEXT NOT NULL DEFAULT '',
  order_city TEXT NOT NULL DEFAULT '',
  department_id TEXT NOT NULL DEFAULT '',
  department_name TEXT NOT NULL DEFAULT '',
  shipping_mode TEXT NOT NULL DEFAULT '',
  payment_type TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (order_id, order_item_id)
);

-- source metadata for Data Sources page (real runs only)
CREATE TABLE IF NOT EXISTS dataco_source_meta (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  source_name TEXT NOT NULL DEFAULT 'DataCo Smart Supply Chain',
  source_url TEXT NOT NULL DEFAULT 'https://data.mendeley.com/datasets/8gx2fvg2k6/5',
  dataset_start TEXT NOT NULL DEFAULT '2015-01-01',
  dataset_end TEXT NOT NULL DEFAULT '2018-01-31',
  rows INTEGER NOT NULL DEFAULT 0,
  columns INTEGER NOT NULL DEFAULT 53,
  last_processed TEXT,
  last_run_id TEXT,
  last_status TEXT
);
INSERT OR IGNORE INTO dataco_source_meta
  (id, source_name, source_url, dataset_start, dataset_end, rows, columns)
VALUES
  (1, 'DataCo Smart Supply Chain', 'https://data.mendeley.com/datasets/8gx2fvg2k6/5',
   '2015-01-01', '2018-01-31', 0, 53);
