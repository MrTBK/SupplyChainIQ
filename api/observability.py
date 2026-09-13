"""Observability: request IDs, secret-free access log. No bodies, headers, or cookies logged."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .config import SESSION_COOKIE
from .db import app_db

logger = logging.getLogger("supplychainiq.access")
REQUEST_ID_HEADER = "X-Request-ID"


def _uid_for(sid: str) -> str:
    if not sid:
        return "-"
    try:
        con = app_db()
        row = con.execute("SELECT user_id FROM sessions WHERE id=?", (sid,)).fetchone()
        con.close()
        return str(row["user_id"]) if row else "-"
    except Exception:
        return "-"


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex[:16]
        request.state.request_id = rid
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            status = 500
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            uid = _uid_for(request.cookies.get(SESSION_COOKIE, ""))
            logger.info("%s %s %s %s %sms uid=%s",
                        rid, request.method, request.url.path, status, duration_ms, uid)
        response.headers[REQUEST_ID_HEADER] = rid
        return response
