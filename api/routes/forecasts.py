"""Forecast routes: every prediction labeled with model, error, and meaning."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..db import warehouse_ro
from ..foundation import parse_paging
from ..rbac import require_perm
from ..services.forecasts import forecasts

router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])


@router.get("", dependencies=[Depends(require_perm("ops:read"))])
def get_forecasts(product: str = "", category: str = "", warehouse: str = "",
                  horizon: int = 1, limit: int = 50, offset: int = 0) -> dict:
    pg = parse_paging(limit, offset)
    con = warehouse_ro()
    try:
        return forecasts(con, product=product, category=category, warehouse=warehouse,
                         horizon=horizon, limit=pg["limit"], offset=pg["offset"])
    finally:
        con.close()
