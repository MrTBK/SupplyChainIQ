# Data Warehouse — SupplyChainIQ

Grain is normative. Do not copy OLTP into warehouse.

## Star Schemas

dim_date — dim_product(SCD2) — dim_supplier(SCD2) — dim_warehouse — dim_customer — dim_carrier.

* FactSales (one row per sales order line): qty, unit_price, net_amount. Dims: product, warehouse, customer, date.
* FactPurchases (one row per PO line receipt): ordered_qty, received_qty, unit_cost, late_days. Dims: supplier, warehouse, product, order/receipt dates.
* FactInventorySnapshot (one row per product/warehouse/day): on_hand, reserved, available, unit_cost.
* FactInventoryMovement (one row per movement event): qty_delta, reason.
* FactShipments (one row per shipment line): shipped_qty, freight_cost. Dim carrier.
* FactDeliveries (one row per delivery line): on_time flag, delay_days.
* FactReturns (one row per return line): qty, reason.

## Keys

Surrogate integer PKs (*_sk). Natural source keys in staging only. Unknown member 0 per dim. FKs indexed (003_constraints.sql). SCD2 product/supplier keep single is_current=1 per natural key (tested). Checks: qty/cost >= 0 except movement delta.

## Marts (views, warehouse/sql/008_marts.sql)

mart_inventory, mart_procurement, mart_logistics, mart_demand, mart_risk. BI reads marts/views only.
