"""Demand routes: aggregated trend for overview charts (reuses fact_sales, no new logic)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..db import warehouse_ro
from ..rbac import require_perm
from ..services.demand import trend

router = APIRouter(prefix="/api/demand", tags=["demand"])


@router.get("/trend", dependencies=[Depends(require_perm("ops:read"))])
def get_trend(months: int = 12) -> dict:
    con = warehouse_ro()
    try:
        return trend(con, months=max(1, min(months, 24)))
    finally:
        con.close()
