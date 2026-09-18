# DataCo → SupplyChainIQ Mapping (binding for ETL)

Legend: DIRECT = copy; DERIVED = justified formula; AGGREGATED = group-by;
NOT USED = present but excluded; NOT AVAILABLE = absent in source.

## Fact sales (grain: one row per DataCo Order Item)

| DataCo field | SupplyChainIQ field | Transform | Class | Confidence |
|---|---|---|---|---|
| Order Id | fact_sales.so_id | str strip | DIRECT | high |
| Order Item Id | fact_sales.line_no | row_number per Order Id ordered by Item Id | DERIVED | high |
| Order Item Quantity | fact_sales.qty | int, must be >0 else quarantine R02 | DIRECT | high |
| Order Item Product Price | fact_sales.unit_price | float ≥0 | DIRECT | high |
| Order Item Total | fact_sales.net_amount | float ≥0 | DIRECT | high |
| order date (DateOrders) | fact_sales.date_key + dim_date | parse `%m/%d/%Y %H:%M` → ISO date | DIRECT | high |
| Order Status | fact_sales.order_status | allowlist 9 values | DIRECT | high |
| Order Item Discount / Rate | fact_sales discount measures | float | DIRECT | high |
| Sales / Benefit / Profit | revenue/profit measures | Sales=unit price; Total=net; Benefit==Profit (use one) | DIRECT | high |
| Product Card Id | dim_product.product_id | str | DIRECT | high |
| Product Name | dim_product.name | strip | DIRECT | high |
| Category Name + Category Id | dim_product.category / dim_category | strip | DIRECT | high |
| Product Price | dim_product.standard_cost | list price label (NOT cost) | DERIVED | medium |
| Customer Id/Fname/Lname | dim_customer | concat name; drop Email/Password (PII) | DIRECT | high |
| Customer Segment/City/State/Country | dim_customer attrs | strip | DIRECT | high |
| Market / Order Region / Country/State/City | dim_market / dim_region | strip | DIRECT | high |
| Department Id/Name | dim_department | strip | DIRECT | high |
| Type | dim_payment_type (optional) | DEBIT/TRANSFER/PAYMENT/CASH | DIRECT | low |

## Logistics (grain: one row per Order Item shipment/delivery)

| DataCo field | SupplyChainIQ field | Transform | Class | Confidence |
|---|---|---|---|---|
| shipping date (DateOrders) | fact_shipments.shipment_date_key = actual delivery date | parse → ISO date; verified == order_date + real_days on raw rows | DIRECT | high |
| Shipping Mode | dim_shipping_mode | 4 values | DIRECT | high |
| Days for shipping (real) | staging real_days 0–6 | int | DIRECT | high |
| Days for shipment (scheduled) | staging sched_days → promised_date_key | scheduled delivery = order_date + sched_days (verified on raw late rows) | DERIVED | high |
| delay_days | fact_deliveries.delay_days | real − sched | DERIVED | high |
| on_time | fact_deliveries.on_time | 1 if delay ≤0 else 0 | DERIVED | high |
| Delivery Status | fact_deliveries.status | 4 values | DIRECT | high |
| Late_delivery_risk | label only | NEVER a prediction feature (leakage) | NOT USED (features) | high |

## Explicitly NOT USED / NOT AVAILABLE

- NOT USED: Order Zipcode (86% empty), Product Description (100% empty),
  Customer Email/Password (masked PII), Product Image, Latitude/Longitude.
- NOT AVAILABLE: supplier, purchase order/lines, warehouse, inventory
  snapshot/movement, carrier id, safety stock, reorder point, return lines
  (only canceled status → returns marked partial/unavailable).
