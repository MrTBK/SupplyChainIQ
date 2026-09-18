# Data Quality — SupplyChainIQ

Rules in etl/dq_rules.yml. Dimensions: completeness, validity, consistency, referential, uniqueness, timeliness.

R01 id not null. R02 qty/cost >= 0 (movement delta excepted). R03 delivery >= shipment. R04 PO→supplier exists. R05 movement/snapshot/sales→product+warehouse exists. R06 promised_date present for OTIF. R07 business-key unique. R08 freshness < 26h.

Score: accepted/read per source per batch in dq_batch_score. Gate: score < 0.98 → batch partial, alert. Evidence: tests/test_etl_dq.py (R02/R05 quarantined, grain unique, idempotent).

## DataCo findings (2026-09-18, real validation, zero injected errors)

Full load DATACO1: read 180,519 / accepted 180,519 / rejected 0 / score 1.0.
Rules R09–R15 all pass: 53-column contract holds, ship days in range,
timestamps parse (%m/%d/%Y %H:%M), statuses in allowlists (9 order, 4 delivery),
( Order Id, Order Item Id) unique, product/customer ids present, PII dropped,
delay_days = real − sched verified. Quarantine: 0 rows — dataset is clean;
reported as-is, no manufactured errors. Cross-check: Late delivery 98,977 =
Late_delivery_risk 1; canceled 7,754 excluded from OTD (OTD 42.7%, late 57.3%).
Coverage note: monthly volume drops ~80% from Oct 2017 (regime change, not
demand); analytics window ends Sep 2017 (`ANALYSIS_END`), raw range preserved.
