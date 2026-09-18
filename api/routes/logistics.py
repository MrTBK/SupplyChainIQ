"""Logistics routes: where delays occur."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..db import warehouse_ro
from ..foundation import parse_paging
from ..rbac import require_perm
from ..services.logistics import late_deliveries, summary

router = APIRouter(prefix="/api/logistics", tags=["logistics"])


@router.get("/summary", dependencies=[Depends(require_perm("ops:read"))])
def get_summary() -> dict:
    con = warehouse_ro()
    try:
        return summary(con)
    finally:
        con.close()


@router.get("/late", dependencies=[Depends(require_perm("ops:read"))])
def get_late(limit: int = 50, offset: int = 0, carrier: str = "", region: str = "",
             mode: str = "") -> dict:
    pg = parse_paging(limit, offset)
    con = warehouse_ro()
    try:
        return late_deliveries(con, limit=pg["limit"], offset=pg["offset"],
                               carrier=carrier, region=region, mode=mode or carrier)
    finally:
        con.close()
