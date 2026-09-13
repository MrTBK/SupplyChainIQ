"""DQ routes: score gate visibility + quarantine drill-down."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import config
from ..db import warehouse_ro
from ..foundation import parse_paging
from ..rbac import require_perm
from ..services.quality import latest_scores, quarantine, rules

router = APIRouter(prefix="/api/data-quality", tags=["quality"])


@router.get("/score", dependencies=[Depends(require_perm("ops:read"))])
def get_score() -> dict:
    con = warehouse_ro()
    try:
        return latest_scores(con)
    finally:
        con.close()


@router.get("/quarantine", dependencies=[Depends(require_perm("ops:read"))])
def get_quarantine(source: str = "", rule: str = "", limit: int = 50, offset: int = 0) -> dict:
    pg = parse_paging(limit, offset)
    con = warehouse_ro()
    try:
        return quarantine(con, source=source, rule=rule, limit=pg["limit"], offset=pg["offset"])
    finally:
        con.close()


@router.get("/rules", dependencies=[Depends(require_perm("ops:read"))])
def get_rules() -> dict:
    items = rules(config.REPO)
    return {"total": len(items), "items": items}
