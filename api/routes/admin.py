"""Admin routes: users, roles, audit. Administrator only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import users as store
from ..csrf import CsrfChecked
from ..rbac import current_role, current_user, require_perm

router = APIRouter(prefix="/api", tags=["admin"])
_guard = Depends(require_perm("admin:users"))


@router.get("/users", dependencies=[_guard])
def get_users() -> dict:
    items = store.list_users()
    return {"total": len(items), "items": items}


class UserIn(BaseModel):
    username: str
    password: str
    role: str


@router.post("/users", dependencies=[_guard, CsrfChecked])
def post_user(body: UserIn, actor: dict = Depends(current_user)) -> dict:
    try:
        user = store.create_user(body.username, body.password, body.role)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=409 if "already exists" in msg else 422, detail=msg)
    store.audit(str(actor["uid"]), "user.create", user["username"])
    return user


class UserPatch(BaseModel):
    role: str = ""
    password: str = ""
    disabled: bool | None = None


@router.patch("/users/{uid}", dependencies=[Depends(require_perm("admin:users")), CsrfChecked])
def patch_user(uid: int, body: UserPatch, actor: dict = Depends(current_user)) -> dict:
    try:
        user = store.update_user(uid, role=body.role, password=body.password, disabled=body.disabled)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    store.audit(str(actor["uid"]), "user.update", user["username"])
    return user


@router.delete("/users/{uid}", dependencies=[Depends(require_perm("admin:users")), CsrfChecked])
def delete_user(uid: int, actor: dict = Depends(current_user),
                role: str = Depends(current_role)) -> dict:
    result = store.delete_user(uid, actor["uid"])
    if result == "self":
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    if result == "missing":
        raise HTTPException(status_code=404, detail="User not found")
    if result == "last-admin":
        raise HTTPException(status_code=400, detail="Cannot delete the last administrator")
    store.audit(str(actor["uid"]), "user.delete", str(uid))
    return {"status": "deleted", "id": uid}


@router.get("/roles", dependencies=[_guard])
def get_roles() -> dict:
    items = store.role_matrix()
    return {"total": len(items), "items": items}


@router.get("/audit", dependencies=[_guard])
def get_audit(limit: int = 100) -> dict:
    items = store.read_audit(min(limit, 500))
    return {"total": len(items), "items": items}
