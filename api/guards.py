"""Deployment guards: request body cap + optional trusted hosts."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .config import MAX_BODY_BYTES

# Uploads carry their own 10MB rule (services/sources.py); everything else is small JSON.
EXEMPT_PREFIX = "/api/data-sources/"
EXEMPT_SUFFIX = "/upload"


class BodyLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not (request.url.path.startswith(EXEMPT_PREFIX) and request.url.path.endswith(EXEMPT_SUFFIX)
                and request.method == "POST"):
            try:
                length = int(request.headers.get("content-length", "0"))
            except ValueError:
                length = 0
            if length > MAX_BODY_BYTES:
                return JSONResponse(status_code=413, content={
                    "error": {"code": 413, "message": "Request body too large"}})
        return await call_next(request)
