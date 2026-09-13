"""Inventory routes: operational stock list + drill-down (Power BI keeps deep analysis)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db import warehouse_ro
from ..foundation import parse_paging
from ..rbac import require_perm
from ..services.inventory import product_drill, stock_list

router = APIRouter(prefix="/api", tags=["inventory"])


@router.get("/inventory", dependencies=[Depends(require_perm("ops:read"))])
def get_inventory(search: str = "", warehouse: str = "", low_stock: bool = False,
                  limit: int = 50, offset: int = 0) -> dict:
    pg = parse_paging(limit, offset)
    con = warehouse_ro()
    try:
        return stock_list(con, search=search, warehouse=warehouse, low_stock=low_stock,
                          limit=pg["limit"], offset=pg["offset"])
    finally:
        con.close()


@router.get("/products/{product_id}", dependencies=[Depends(require_perm("ops:read"))])
def get_product(product_id: str, warehouse: str = Query(default="")) -> dict:
    con = warehouse_ro()
    try:
        drill = product_drill(con, product_id, warehouse)
    finally:
        con.close()
    if drill is None:
        raise HTTPException(status_code=404, detail="Product not found or no stock")
    return drill
