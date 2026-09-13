# Machine Learning — SupplyChainIQ

Methods ship only with problem→target→features→baseline→model→eval→value→limits.

* Turnover/ABC/supplier score/lead-time: analytics/analytics.py. Supplier score = 0.5 OTIF + 0.3 quality proxy + 0.2 stability; quality proxy limit documented (returns-only until lot traceability).
* Anomaly: z-score on monthly demand residuals after MA baseline; flag |z|>=3 (tunable). IsolationForest-equivalent deferred; residual method is the auditable baseline.
* Forecast: see docs/forecasting.md.
* Prescriptions: reorder = max(0, forecast_lead_demand + safety − on_hand − on_order); safety = z·σ·√LT; supplier = min risk-adjusted cost among approved; transfer = min(surplus, deficit). Every row carries inputs + reason + risk. Code analytics/prescriptions.py. Hand-calc test green.
* Business value: cut stockouts without piling overstock; replace-or-renegotiate evidence; expedite only late lanes.
