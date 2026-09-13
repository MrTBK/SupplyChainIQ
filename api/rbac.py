"""RBAC: explicit per-role permissions (ADR-008 matrix). No role gets everything."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request

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


def current_role(request: Request) -> str:
    role = request.session.get("role")
    if request.session.get("uid") is None or role not in ALL_ROLES:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return role


def require_perm(permission: str):
    def check(role: str = Depends(current_role)) -> str:
        if role not in PERMISSIONS.get(permission, frozenset()):
            raise HTTPException(status_code=403, detail=f"Role '{role}' lacks '{permission}'")
        return role
    return check
