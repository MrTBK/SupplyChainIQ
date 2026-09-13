# Data Dictionary — SupplyChainIQ (stub v0.1, full in Phase 6)

Conventions: surrogate keys *_sk integer PK in warehouse; natural source keys kept in staging only; unknown member 0 per dim; dates ISO YYYY-MM-DD; currency in base currency units; qty >= 0 except movement delta.

## Staging contracts (binding, see docs/architecture.md)

products: product_id, sku, name, category, standard_cost, is_synthetic, seed, generator_version
suppliers: supplier_id, name, rating_tier, is_synthetic
contracts: contract_id, supplier_id, product_id, unit_cost, lead_time_days, capacity
warehouses: warehouse_id, name, region
customers: customer_id, name, region
carriers: carrier_id, name
purchase_orders: po_id, supplier_id, warehouse_id, order_date, promised_date
po_lines: po_id, line_no, product_id, ordered_qty, received_qty, unit_cost, receipt_date
sales_orders: so_id, customer_id, order_date
so_lines: so_id, line_no, product_id, warehouse_id, qty, unit_price
inventory_snapshots: snapshot_date, product_id, warehouse_id, on_hand, reserved
movements: movement_id, event_date, product_id, warehouse_id, qty_delta, reason
shipments: shipment_id, so_id, line_no, carrier_id, shipment_date, shipped_qty, freight_cost
deliveries: shipment_id, promised_date, delivery_date, delivered_qty
returns: return_id, so_id, line_no, product_id, qty, reason (QUALITY/DAMAGE/OTHER)

Full column types + constraints in warehouse/sql DDL (Phase 6). This stub locks names so generator, ETL, and warehouse agree.
