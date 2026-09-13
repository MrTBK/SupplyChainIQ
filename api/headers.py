"""Security headers: centralized middleware. JSON API only, so CSP can be strict.

HSTS is sent only when SCI_COOKIE_SECURE=1, i.e. the operator guarantees HTTPS.
Documented omission: no CSP report-uri (no collector in this project).
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .config import COOKIE_SECURE

BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    # API returns JSON only; nothing may be framed or loaded as a document.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}

HSTS = "max-age=31536000; includeSubDomains"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for k, v in BASE_HEADERS.items():
            response.headers.setdefault(k, v)
        if COOKIE_SECURE:
            response.headers.setdefault("Strict-Transport-Security", HSTS)
        return response
