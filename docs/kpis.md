# KPI Catalog — SupplyChainIQ (DataCo real-data definitions; synthetic § retired, see git history)

> DataCo Smart Supply Chain (2015-01-01–2018-01-31). Grain: one row per Order Item.
> OTD truth EXCLUDES 'Shipping canceled'. Late_delivery_risk is post-outcome (label only).
> Inventory/supplier/purchase KPIs (#1-12, #20-22 above) are NOT available from DataCo;
> rows kept for reference, hidden in UI. Live definitions: api/services/overview.py,
> logistics.py, forecasts.py. Lineage: docs/data/lineage.md.

Grain, formula, and limits per KPI. SQL gold: analytics/kpis.py. DAX mirrors in powerbi/measures.dax.

| # | Name | Definition | Formula | Unit | Grain | Source | Dimensions | Window | Interpretation | Limits |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Inventory Value | on-hand value now | SUM(available × unit_cost) | cur | product/wh/day | snapshots | product, wh, date | latest | cash tied | costing method dependent |
| 2 | Coverage Days | days of stock left | on_hand / avg_daily_demand_30d | days | product/wh | snapshots+sales | product, wh | 30d | < lead+safe = risk | fails intermittent demand |
| 3 | Stockout Rate | share of stockout days | stockout days / active days | % | wh/month | snapshots | wh, date | month | service proxy | needs active definition |
| 4 | Turnover | cash velocity | COGS / avg inventory value | x/yr | category/wh/qtr | sales+snapshots | cat, wh | qtr | low = overstock | mix sensitive |
| 5 | Dead Stock Value | unsold 90d value | value where zero sales 90d and oh>0 | cur | product/wh | sales+snapshots | product, wh | 90d | markdown/transfer | threshold param |
| 6 | Overstock Qty | above max | oh − max where defined | units | product/wh | snapshots | product, wh | latest | move/store cost | max policy quality |
| 7 | Supplier OTIF | on-time-in-full | on-time receipts / receipts | % | supplier/month | purchases | supplier, date | month | reliability | tolerance 2d |
| 8 | Avg Lead Time | mean PO→receipt | MEAN(receipt−po) | days | supplier/product | purchases | supplier | all | planning input | variance matters more |
| 9 | Lead Time Variance | spread | STDDEV(lead time) | days | supplier | purchases | supplier | all | drives safety | needs n≥10 |
| 10 | Defect Return Rate | quality returns | quality qty / receipt qty | % | supplier | returns | supplier | month | quality | needs reason coding |
| 11 | Spend by Supplier | concentration | SUM(line cost) | cur | supplier/qtr | purchases | supplier | qtr | risk | contract vs spot |
| 12 | Price Change | inflation | (cur−prev)/prev | % | supplier/product | contracts | supplier | event | renegotiate | mix effects |
| 13 | Demand | shipped demand | SUM(qty) | units | product/month | sales | product, date | month | planning base | shipped not booked |
| 14 | Growth MoM/YoY | momentum | (cur−prev)/prev | % | product/cat | sales | product, date | month | lifecycle | seasonal confound |
| 15 | WAPE | forecast error | Σ\|a−f\|/Σa | % | product/wh/month | sales+forecast | product, wh | month | accuracy | use over MAPE low-vol |
| 16 | On-Time Delivery | logistics service | on-time / deliveries | % | carrier/lane/month | deliveries | carrier, lane | month | carrier score | tolerance 0d |
| 17 | Avg Delivery Time | lane speed | MEAN(delivery−shipment) | days | lane | deliveries | lane | month | promise setting | tail needs p90 |
| 18 | Return Rate | returns | return qty / shipped | % | product/reason | returns | product | month | quality/damage | reason split needed |
| 19 | Cost per Shipment | freight efficiency | freight / shipments | cur | carrier/month | shipments | carrier | month | cost | fuel noise |
| 20 | Stockout Risk | 0-100 | rule from coverage+forecast+variance | score | product/wh | snap+forecast | product, wh | now | act list | weights documented |
| 21 | Transfer Opportunity | fungible surplus | min(surplus, deficit) same SKU | units | product pair | snapshots | wh | now | move not buy | same-SKU only |
| 22 | Supplier Risk | composite | 0.5 late+0.3 defect+0.2 concentration | score | supplier | purch+returns | supplier | month | replace watch | weights documented |
