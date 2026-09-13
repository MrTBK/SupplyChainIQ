# BI — SupplyChainIQ

Model: star import, single-direction dim→fact via *_sk, DimDate marked date table. Measures in powerbi/measures.dax only. Hierarchies: date Y-Q-M-D, product category→product, location region→warehouse.

Pages (each answers listed questions, max 3 visuals per section, no gauges):
1 Executive: value, service, risk trends.
2 Inventory: coverage histogram, dead/overstock tables, turnover by category.
3 Procurement: OTIF leaderboard, lead-time variance, spend concentration, price change.
4 Demand: trend, seasonality, growers/decliners.
5 Logistics: OTIF by carrier/lane, p50+p90 time, delay causes.
6 Risk & Alerts: stockout-risk list, supplier degradation, spike flags.
7 Forecasting: actual vs forecast, WAPE, next-3-month table.

Build .pbix from warehouse views (008_marts.sql) via Postgres connector (prod) or SQLite export (demo). Gold checks: analytics/kpis.py vs DAX on sample.
