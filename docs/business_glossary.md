# Business Glossary — SupplyChainIQ (SYNTHETIC)

## Terms

* **On Hand:** physical units in a warehouse now. Source: snapshots.
* **Reserved:** units promised to open sales orders, not yet shipped.
* **Available:** on_hand - reserved. Never negative in clean data; negative flags DQ issue.
* **Lead Time (procurement):** receipt_date - po_date in days. Mean matters less than variance.
* **Lead Time (logistics):** delivery_date - shipment_date in days. Report mean + p90.
* **Lead Time Demand:** forecast daily demand × lead time days.
* **Safety Stock:** z × demand_stddev × sqrt(lead_time). z=1.65 for 95% service default, configurable per category.
* **Reorder Point:** lead time demand + safety stock.
* **Coverage Days:** on_hand / avg_daily_demand_30d. Undefined when demand zero → flag, do not divide by zero.
* **Dead Stock:** zero sales 90d and on_hand > 0. Threshold is business parameter.
* **Overstock:** on_hand - max_stock where max defined. Depends on max policy quality.
* **Stockout (derived):** demand > available on a product/warehouse/day. Rate = stockout days / active days.
* **OTIF (procurement):** receipts on-time-in-full / receipts. Late = receipt_date > promised_date + tolerance (default 2d).
* **OTD (logistics):** deliveries on time / deliveries. Same tolerance rule.
* **ABC:** A ~80% revenue, B ~15%, C ~5%. Computed per category annually.
* **WAPE:** sum|actual-forecast| / sum(actual). Preferred over MAPE for low-volume SKUs.
* **Quarantine:** rejected rows with rule_id + reason. Never silently dropped.

## Entities and Relationships

Product (category) —< Contract >— Supplier. Supplier —< PO >— Warehouse. Warehouse —< Snapshot/Movement >— Product. Customer —< SO >— Warehouse via Shipment (Carrier) → Delivery → Return (reason). Contract holds price + lead time + capacity. Movement reasons: RECEIPT, SALE, ADJUSTMENT, TRANSFER_IN, TRANSFER_OUT, RETURN.

## Grain Drafts (binding for warehouse)

* FactSales: one row per sales order line.
* FactPurchases: one row per PO line receipt.
* FactInventorySnapshot: one row per product/warehouse/day.
* FactInventoryMovement: one row per movement event.
* FactShipments: one row per shipment line.
* FactDeliveries: one row per delivery line.
* FactReturns: one row per return line.
