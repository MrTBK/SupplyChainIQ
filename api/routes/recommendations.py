"""Recommendation routes: explainable prescriptions only."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..db import warehouse_ro
from ..rbac import require_perm
from ..services.recommendations import recommend

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("", dependencies=[Depends(require_perm("ops:read"))])
def get_recommendations(product: str = "", kind: str = "") -> dict:
    con = warehouse_ro()
    try:
        items = recommend(con, product=product, kind=kind)
    finally:
        con.close()
    return {"total": len(items), "items": items}
