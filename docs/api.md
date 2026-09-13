# Web API — SupplyChainIQ

Base: same origin `/api` (Vite proxies to `:8000` in dev). Auth: session cookie `sci_session` (login first). Errors: `{error: {code, message}}`; 500s never leak internals. Lists: `?limit` (cap 500) `&offset`, `?ordering` allowlisted per endpoint, `?search` safe substring.

| Method + path | Perm | Request | Response |
|---|---|---|---|
| POST /api/auth/login | public | {username, password} | {id, username, role} + cookie; 401 bad creds |
| POST /api/auth/logout | login | — | {status}; clears session |
| GET /api/auth/me | login | — | {id, role}; 401 anonymous |
| GET /api/kpis/overview | ops:read | — | sales/inventory/OTIF/OTD/quarantine totals |
| GET /api/inventory | ops:read | ?search ?warehouse ?low_stock ?limit ?offset | {total, items[product, stock, coverage, value]} |
| GET /api/products/{id} | ops:read | ?warehouse | stock, 12m demand, forecast, p50 lead, safety, per-wh reorder+risk; 404 unknown |
| GET /api/suppliers | ops:read | ?search ?ordering(-score/-otif/±spend) | ranking with spend/OTIF/score/p50/p90 |
| GET /api/suppliers/{id} | ops:read | — | score, lead-time, 12m spend trend; 404 |
| GET /api/logistics/summary | ops:read | — | OTD, avg/p90 delay, by carrier/region |
| GET /api/logistics/late | ops:read | paging | late deliveries, worst delay first |
| GET /api/forecasts | ops:read | ?product ?category ?warehouse ?horizon(1-3) | history + model + WAPE + projection + note |
| GET /api/risks | ops:read | ?kind ?severity | severity/entity/time/reason/metrics/action |
| GET /api/recommendations | ops:read | ?product ?kind | reorder/transfer/supplier with full WHY |
| GET /api/data-sources | ops:read | — | 14 sources: status, runs, watermark, columns |
| POST /api/data-sources/{n}/upload | sources:upload | multipart CSV ≤10MB | schema check + staged batch; 422 bad schema; never auto-loads |
| GET /api/etl-runs | ops:read | ?source ?status + paging | run history newest first |
| POST /api/etl-runs/trigger | etl:trigger | {src in data/, batch?} | runs load_batch; 422 outside allowlist |
| GET /api/data-quality/score | ops:read | — | threshold, overall, per-source gate |
| GET /api/data-quality/quarantine | ops:read | ?source ?rule + paging | rejected rows with rule + payload |
| GET /api/data-quality/rules | ops:read | — | R01-R08 catalog |
| GET /api/alerts | ops:read | ?status ?severity ?kind + paging | persisted alerts |
| POST /api/alerts/evaluate | etl:trigger | — | {stored_new, open_total}, day-deduped |
| PATCH /api/alerts/{id} | ops:read | {status} | acknowledge/resolve; 404/422 |
| GET/POST/PATCH/DELETE /api/users… | admin:users | user shapes | guards: 409 dup, 422 weak role/pass, 400 self/last-admin |
| GET /api/roles, GET /api/audit | admin:users | ?limit | matrix, audit trail |
