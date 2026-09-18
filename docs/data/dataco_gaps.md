# DataCo Gap Analysis (STOP-report format)

## Entity matrix

| SupplyChainIQ entity | DataCo support | Available fields | Missing fields | Can derive? | Action |
|---|---|---|---|---|---|
| Products | YES | Card Id, Name, Category, Price | cost breakdown | list-price label only | load dim_product |
| Categories | YES | Category Id/Name (50) | — | — | load dim_category |
| Customers | YES | Id, name, segment, city/state/country | email (masked) | — | load dim_customer, drop PII |
| Regions/Markets | YES | Market 5, Region 23, country/state/city | — | — | load dim_market/dim_region |
| Departments | YES | Dept Id/Name (11) | — | — | load dim_department |
| Dates | YES | order + shipping timestamps | — | dim_date | parse to ISO |
| Sales Orders/Lines | YES | Order Id, Item Id, qty, prices, status | — | line_no via row_number | load fact_sales |
| Shipments | PARTIAL | ship date, mode, real/sched days | carrier id, freight | delay/on_time derived | load fact_shipments + dim_shipping_mode |
| Deliveries | YES | Delivery Status 4 vals | — | on_time/delay | load fact_deliveries |
| Returns | PARTIAL | canceled status only | return lines/qty/reason | no | mark unavailable, no fake fact_returns |
| Carriers | NO | Shipping Mode only | carrier id/name | no | use mode; no fake carriers |
| Suppliers | NO | — (Type=payment, not supplier) | all | no | HIDE page; keep DDL empty + documented |
| Purchase Orders | NO | — | all | no | HIDE; keep DDL empty |
| Warehouses | NO | — | all | no | HIDE inventory-by-warehouse; region replaces it |
| Inventory/Movements | NO | — | stock, safety, reorder, coverage | no | HIDE page; demand history is NOT stock |

## Missing capability reports

- Missing capability: Supplier Intelligence. Why: no supplier entity/column.
  Legitimate solution: second public procurement dataset later.
  Decision: hide `/suppliers`, keep `dim_supplier` DDL empty.
- Missing capability: Inventory positions. Why: no stock/movement columns.
  Legitimate solution: future WMS dataset. Decision: hide `/inventory`,
  remove reorder-qty recs, keep demand-based investigations.
- Missing capability: Carrier tracking. Why: mode only, no carrier id.
  Decision: `dim_shipping_mode` + mode/region performance instead of carrier pages.
- Missing capability: Returns analytics. Why: status only, no return lines.
  Decision: cancellation rate only; no `fact_returns` from DataCo.

## Leakage note (binding)

`Late_delivery_risk`, `Delivery Status`, `Days real`, delay_days are
POST-OUTCOME. Risk/forecast features may use only: shipping mode,
market/region, department/category, qty, discount, order weekday,
scheduled days. Documented in `docs/analytics/risk_methodology.md`
(created in Wave C).
