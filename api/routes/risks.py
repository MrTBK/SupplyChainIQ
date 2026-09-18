"""Risk routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..db import warehouse_ro
from ..rbac import require_perm
from ..services.linkage import link
from ..services.recommendations import recommend
from ..services.risks import evaluate

router = APIRouter(prefix="/api/risks", tags=["risks"])


@router.get("", dependencies=[Depends(require_perm("ops:read"))])
def get_risks(kind: str = "", severity: str = "") -> dict:
    con = warehouse_ro()
    try:
        risks = evaluate(con)
        recs = recommend(con)
        risks, _ = link(risks, recs)
    finally:
        con.close()
    if kind:
        risks = [r for r in risks if r["kind"] == kind]
    if severity:
        risks = [r for r in risks if r["severity"] == severity]
    return {"total": len(risks), "items": risks}
