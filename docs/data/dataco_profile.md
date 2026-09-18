# DataCo Smart Supply Chain — Dataset Profile (measured from local file)

Source: https://data.mendeley.com/datasets/8gx2fvg2k6/5 (DataCo Smart Supply Chain)
Local file: `DataCo/DataCoSupplyChainDataset.csv` (raw, never modified)
Description file: `DataCo/DescriptionDataCoSupplyChain.csv`
Out-of-scope file: `DataCo/tokenized_access_logs.csv` (92 MB, access logs, not used in v1)

## Measured facts (python csv scan, 2026-09-18)

- File size: 92 MB; lines: 180,520 → **180,519 data rows**
- Columns: **53** (see mapping doc for full header list)
- Grain: **one row per Order Item** — 180,519 unique `Order Item Id`,
  0 duplicates on `(Order Id, Order Item Id)`
- Keys: 65,752 `Order Id`; 20,652 `Customer Id`; 118 `Product Card Id` / `Product Name`;
  50 `Category Name`; 11 `Department Name`
- Dates (`%m/%d/%Y %H:%M`, 0 parse failures):
  `order date` 2015-01-01 → 2018-01-31;
  `shipping date` 2015-01-03 → 2018-02-06. **Historical dataset.**
- `Delivery Status`: Late delivery 98,977 / Advance shipping 41,592 /
  Shipping on time 32,196 / Shipping canceled 7,754
- `Late_delivery_risk`: 1 = 98,977 = Late delivery exactly → **post-outcome label**
- `Order Status` (9): COMPLETE 59,491 / PENDING_PAYMENT 39,832 / PROCESSING 21,902 /
  PENDING 20,227 / CLOSED 19,616 / ON_HOLD 9,804 / SUSPECTED_FRAUD 4,062 /
  CANCELED 3,692 / PAYMENT_REVIEW 1,893
- Consistency: CANCELED ↔ Shipping canceled; SUSPECTED_FRAUD ↔ Shipping canceled
- Logistics: `Days for shipping (real)` 0–6 mean 3.5;
  `Days for shipment (scheduled)` 0–4 mean 2.93
- `Shipping Mode` (4, no carrier id): Standard 107,752 / Second 35,216 /
  First 27,814 / Same Day 9,737
- Commercial: `Order Item Quantity` ∈ {1..5} (1=99,134, 2–5 ≈20k each), 0 bad;
  `Product Price` 0 bad; `Sales` = unit price; `Order Item Total` = net after discount;
  `Benefit per order` == `Order Profit Per Order` (duplicate columns, use one)
- Geo/commercial dims: `Market` 5 / `Order Region` 23 / `Customer Segment` 3 /
  `Type` 4 (DEBIT/TRANSFER/PAYMENT/CASH = payment type, NOT supplier)
- Missing: `Order Zipcode` 155,679/180,519 empty (86%) → NOT USED;
  `Product Description` 180,519/180,519 empty → NOT USED;
  `Customer Email/Password` masked `XXXXXXXXX` → dropped (PII)
- Quality scan: 0 bad qty, 0 bad price, 0 bad dates, 0 dup (Order,Item)

## Coverage break (reported, not smoothed over)

Monthly line volume runs ~10–11k through Sep 2017, then drops ~80% from
Oct 2017 (every line qty=1; Oct 2,490 / Nov 2,055 / Dec 2,124 / Jan 2,123
units vs ~11k before), while order timestamps continue to 2018-01-31 23:38.
This reads as a collection-regime change, not a demand collapse.
Decision: warehouse keeps the full range; analytics (demand trend,
forecasts, demand anomalies) use complete-coverage months through
2017-09-30 (`ANALYSIS_END` in `forecasting/forecast.py`). Snapshot label:
Jan 2015 – Jan 2018 dataset, Sep 2017 analysis snapshot.
18 products (IDs 1346–1363) launched Oct–Dec 2017 with 200–800 units each:
too short for baselines, shown explicitly as no-baseline items.

## What DataCo does NOT contain

No supplier, purchase order, warehouse, inventory position/movement,
carrier id, safety stock, reorder point. See `dataco_gaps.md`.
