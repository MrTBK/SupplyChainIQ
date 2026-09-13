"""RBAC: explicit per-role permissions (ADR-008 matrix). No role gets everything."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from .config import SESSION_COOKIE
from .sessions import get_session

# permission -> roles allowed. Keep in sync with docs (14.23 writes the RBAC doc).
PERMISSIONS: dict[str, frozenset[str]] = {
    "ops:read": frozenset({"executive", "supply_manager", "procurement_manager",
                            "inventory_manager", "logistics_manager", "analyst", "administrator"}),
    "etl:trigger": frozenset({"supply_manager", "procurement_manager", "inventory_manager",
                              "logistics_manager", "administrator"}),
    "sources:upload": frozenset({"supply_manager", "procurement_manager", "inventory_manager",
                                 "logistics_manager", "administrator"}),
    "admin:users": frozenset({"administrator"}),
}

ALL_ROLES = frozenset({"executive", "supply_manager", "procurement_manager",
                       "inventory_manager", "logistics_manager", "analyst", "administrator"})


def current_user(request: Request) -> dict:
    """Authoritative check per request: session must exist server-side and user be live."""
    session = get_session(request.cookies.get(SESSION_COOKIE, ""))
    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session


def current_role(request: Request) -> str:
    role = current_user(request)["role"]
    if role not in ALL_ROLES:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return role


def require_perm(permission: str):
    def check(role: str = Depends(current_role)) -> str:
        if role not in PERMISSIONS.get(permission, frozenset()):
            raise HTTPException(status_code=403, detail=f"Role '{role}' lacks '{permission}'")
        return role
    return check
