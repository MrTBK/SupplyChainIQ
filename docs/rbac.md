# RBAC — SupplyChainIQ web app

Source of truth in code: `api/rbac.py` (PERMISSIONS). This doc mirrors it; tests enforce it.

| Role | ops:read | etl:trigger | sources:upload | admin:users |
|---|---|---|---|---|
| executive | x | | | |
| supply_manager | x | x | x | |
| procurement_manager | x | x | x | |
| inventory_manager | x | x | x | |
| logistics_manager | x | x | x | |
| analyst | x | | | |
| administrator | x | x | x | x |

Rules: no role except administrator holds everything; anonymous holds nothing (401); violations are 403 with the missing permission named. Users live in `app.db` (never committed); passwords PBKDF2-SHA256 200k + salt, min 8 chars; last administrator and self-deletion blocked. Sessions: server-side signed cookie, 8h, HttpOnly, SameSite Lax, Secure flag via SCI_COOKIE_SECURE=1 in production. No login rate limiting in v1 — expose only behind trusted network or add a proxy limit (known limit, 14.19).
