"""Auth routes: login/logout/me over server-side sessions (cookie holds only a random ID)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from ..auth import authenticate
from ..config import COOKIE_SECURE, SESSION_COOKIE
from ..rbac import current_user
from ..sessions import ABSOLUTE_HOURS, create_session, destroy_session

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
    user = authenticate(body.username.strip(), body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    _set_session_cookie(response, create_session(user["id"]))
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict:
    destroy_session(request.cookies.get(SESSION_COOKIE, ""))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"status": "logged out"}


@router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    return {"id": user["uid"], "role": user["role"]}
