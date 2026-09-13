"""Auth routes: login/logout/me over server-side sessions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..auth import authenticate

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginIn, request: Request) -> dict:
    user = authenticate(body.username.strip(), body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    request.session["uid"] = user["id"]
    request.session["role"] = user["role"]
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


@router.post("/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"status": "logged out"}


@router.get("/me")
def me(request: Request) -> dict:
    if "uid" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"id": request.session["uid"], "role": request.session.get("role")}
