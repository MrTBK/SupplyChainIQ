"""Executive overview route: operational visibility, not a Power BI duplicate."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..db import warehouse_ro
from ..rbac import require_perm
from ..services.overview import overview

router = APIRouter(prefix="/api/kpis", tags=["kpis"])


@router.get("/overview", dependencies=[Depends(require_perm("ops:read"))])
def get_overview() -> dict:
    con = warehouse_ro()
    try:
        return overview(con)
    finally:
        con.close()
