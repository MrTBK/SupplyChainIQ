"""Auth routes: login/logout/me over server-side sessions (cookie holds only a random ID)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from ..auth import authenticate
from ..config import COOKIE_SECURE, SESSION_COOKIE
from ..csrf import CSRF_COOKIE, CsrfChecked
from ..db import app_db
from ..rate_limit import clear_login, login_allowed, record_login_failure
from ..rbac import current_user
from ..sessions import ABSOLUTE_HOURS, create_session, destroy_session, get_session
from ..users import audit

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


def _set_session_cookie(response: Response, sid: str) -> None:
    response.set_cookie(SESSION_COOKIE, sid, httponly=True, samesite="lax",
                        secure=COOKIE_SECURE, path="/",
                        max_age=ABSOLUTE_HOURS * 3600)


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response) -> dict:
    key = f"{request.client.host if request.client else 'unknown'}:{body.username.strip().lower()}"
    allowed, retry_after = login_allowed(key)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many login attempts, try again later",
                            headers={"Retry-After": str(retry_after)})
    user = authenticate(body.username.strip(), body.password)
    if not user:
        record_login_failure(key)
        audit(body.username.strip()[:64], "LOGIN_FAILED", "invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    clear_login(key)
    audit(user["username"], "LOGIN", f"Signed in as {user['role']}")
    sid, csrf = create_session(user["id"])
    _set_session_cookie(response, sid)
    response.set_cookie(CSRF_COOKIE, csrf, samesite="lax", secure=COOKIE_SECURE, path="/",
                        max_age=ABSOLUTE_HOURS * 3600)
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


@router.post("/logout", dependencies=[CsrfChecked])
def logout(request: Request, response: Response) -> dict:
    sid = request.cookies.get(SESSION_COOKIE, "")
    session = get_session(sid)
    destroy_session(sid)
    if session:
        audit(str(session["uid"]), "LOGOUT", "")
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")
    return {"status": "logged out"}


@router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    con = app_db()
    row = con.execute("SELECT username FROM users WHERE id=?", (user["uid"],)).fetchone()
    con.close()
    return {"id": user["uid"], "username": row["username"] if row else "?", "role": user["role"]}
