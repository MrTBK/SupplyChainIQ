# Data Quality — SupplyChainIQ

Rules in etl/dq_rules.yml. Dimensions: completeness, validity, consistency, referential, uniqueness, timeliness.

R01 id not null. R02 qty/cost >= 0 (movement delta excepted). R03 delivery >= shipment. R04 PO→supplier exists. R05 movement/snapshot/sales→product+warehouse exists. R06 promised_date present for OTIF. R07 business-key unique. R08 freshness < 26h.

Score: accepted/read per source per batch in dq_batch_score. Gate: score < 0.98 → batch partial, alert. Evidence: tests/test_etl_dq.py (R02/R05 quarantined, grain unique, idempotent).
