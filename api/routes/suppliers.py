"""Supplier routes: performance ranking + detail."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..db import warehouse_ro
from ..foundation import parse_paging
from ..rbac import require_perm
from ..services.suppliers import supplier_detail, supplier_list

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("", dependencies=[Depends(require_perm("ops:read"))])
def get_suppliers(search: str = "", ordering: str = "-score", limit: int = 50, offset: int = 0) -> dict:
    pg = parse_paging(limit, offset)
    con = warehouse_ro()
    try:
        return supplier_list(con, search=search, limit=pg["limit"], offset=pg["offset"], ordering=ordering)
    finally:
        con.close()


@router.get("/{supplier_id}", dependencies=[Depends(require_perm("ops:read"))])
def get_supplier(supplier_id: str) -> dict:
    con = warehouse_ro()
    try:
        detail = supplier_detail(con, supplier_id)
    finally:
        con.close()
    if detail is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return detail
