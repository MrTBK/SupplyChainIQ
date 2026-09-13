# Security — SupplyChainIQ

Posture after Phase 21 hardening. Every claim below names its implementation and tests. All data SYNTHETIC unless a real source is connected.

## 1. Authentication architecture

Username + password at POST /api/auth/login (`api/routes/auth.py`). Generic failure `Invalid username or password` for unknown and wrong alike; unknown accounts still cost one PBKDF2 (no timing oracle, `api/auth.py`). Passwords PBKDF2-SHA256 200k + per-user salt, constant-time compare; never logged, never returned (tests/test_api_auth.py, test_security_sessions.py). Login rate-limited 5/300s per IP+account → 429 + Retry-After (`api/rate_limit.py`, tests/test_security_ratelimit.py).

## 2. Session architecture

Server-side sessions in app.db `sessions` table (`api/sessions.py`, ADR-009): 32-byte random IDs, fresh ID per login (fixation-safe), idle 30m + absolute 8h (env-tunable), lazy expiry cleanup, disabled/deleted users rejected on next request, password/role/disable/delete revokes sessions (`api/users.py`). Logout deletes server-side (tests/test_security_sessions.py).

## 3. Cookie security

`sci_session` (opaque ID): HttpOnly, SameSite=Lax, Path=/, Secure iff SCI_COOKIE_SECURE=1. `sci_csrf`: readable double-submit token, same flags minus HttpOnly. No tokens in localStorage/sessionStorage/URLs/state/logs (frontend verified, tests/test_ux.py).

## 4. RBAC model

See docs/rbac.md. Matrix in `api/rbac.py`, enforced per endpoint via dependencies; frontend checks are UI-only. Regression tests cover matrix, 403 splits, anonymous 401s, admin guards (tests/test_api_rbac.py, test_api_admin.py, test_api_security.py).

## 5. CSRF strategy

Double-submit tokens bound to server sessions (`api/csrf.py`, ADR-009): login issues token, mutations require X-CSRF-Token header with constant-time compare, safe methods exempt, login exempt (rate-limited). All 8 mutating routes guarded; frontend auto-sends (tests/test_security_csrf.py).

## 6. CORS policy

Same-origin by default — no CORS middleware (`api/cors.py`). Split-origin deployments opt in via SCI_CORS_ORIGINS exact origins only; `*` refused; tight methods/headers (tests/test_security_cors.py).

## 7. API security

Envelope errors (internals never leak, 500s generic), paging caps, allowlisted ORDER BY, escaped LIKE, Pydantic bodies, 1MB JSON cap with upload exemption, per-route permission table in docs/api.md (tests/test_api_foundation.py, test_security_config.py).

## 8. File-upload security

Flow: auth → perm → 10MB cap → MIME allowlist → UTF-8 CSV parse → empty/row/col/cell caps → schema check → sha256 duplicate → fixed server-side path → quarantine-style staging, never auto-load, never served (`api/services/sources.py`, `api/routes/sources.py`; attack tests in tests/test_security_upload.py).

## 9. Database security

Parameterized SQL throughout; dynamic sort/filter allowlisted; warehouse opened read-only by the API (write raises, tested); least-privilege Postgres roles in warehouse/sql/009_roles.sql; credentials via env only.

## 10. Secret management

config/.env.example holds placeholders only; config/.env, *.db, keys ignored and verified untracked by test; startup warns on dev-secret defaults (names only); operational hashes live in git-ignored app.db (H10 evidence).

## 11. Audit logging

app.db audit_log: LOGIN, LOGIN_FAILED, LOGOUT, user.create/update/delete, ETL_STARTED/COMPLETED/FAILED, UPLOAD_STAGED with actor + detail; rows verified secret-free by test (tests/test_security_audit.py, test_api_admin.py).

## 12. Rate limiting

Login 5/300s per IP+account with 429 + Retry-After (single-process memory; Redis noted for multi-worker). No blanket limits elsewhere by design.

## 13. Error handling

Central handlers; `{error:{code,message}}`; 500s generic; Starlette 404s enveloped; no stack/SQL/paths/secrets to clients (tested).

## 14. Security testing

tests/test_security_*.py (sessions, ratelimit, csrf, cors, headers, upload, audit, observability, config) + RBAC/admin/workflow coverage. Rule: every fix ships a regression test.

## 15. Production deployment requirements

HTTPS + SCI_COOKIE_SECURE=1 (then HSTS activates); real SCI_SECRET_KEY (32 random bytes) + SCI_ADMIN_PASSWORD; SCI_TRUSTED_HOSTS and SCI_CORS_ORIGINS set; run behind a proxy with login rate limits as defense in depth; backups per docs/deployment.md.

## 16. Known limitations (tested or documented, not claimed away)

* No login rate limiting beyond single-process memory (multi-worker needs Redis).
* No WAF/bot mitigation; login endpoint relies on H2 + proxy limits.
* Supplier quality score is a returns proxy; 009_roles.sql not live-tested against Postgres.
* npm audit: 4 dev-only findings accepted with rationale (H11); no blind majors.
* Vite dev server never exposed publicly (esbuild advisory scope).
