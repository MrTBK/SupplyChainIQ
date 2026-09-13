"""CSRF: double-submit tokens bound to server-side sessions.

Strategy: login issues a random csrf token in a readable cookie (sci_csrf) and
stores the same value server-side on the session row. Mutations (POST/PUT/PATCH/
DELETE) must echo it in the X-CSRF-Token header; compared with compare_digest.
Safe methods need nothing. Login itself needs no token (rate-limited instead).
"""

from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, Request

from .config import SESSION_COOKIE
from .db import app_db

CSRF_COOKIE = "sci_csrf"
CSRF_HEADER = "x-csrf-token"


def session_csrf(sid: str) -> str:
    con = app_db()
    row = con.execute("SELECT csrf_token FROM sessions WHERE id=?", (sid,)).fetchone()
    con.close()
    return row["csrf_token"] if row else ""


def require_csrf(request: Request) -> None:
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    sid = request.cookies.get(SESSION_COOKIE, "")
    expected = session_csrf(sid) if sid else ""
    got = request.headers.get(CSRF_HEADER, "")
    if not expected or not hmac.compare_digest(got, expected):
        raise HTTPException(status_code=403, detail="Missing or invalid CSRF token")


CsrfChecked = Depends(require_csrf)
