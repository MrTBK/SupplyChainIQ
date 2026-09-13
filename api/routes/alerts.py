"""Alert routes: persisted, deduplicated, acknowledgeable."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..alerts import list_alerts, set_status, store_evaluation
from ..db import warehouse_ro
from ..foundation import parse_paging
from ..csrf import CsrfChecked
from ..rbac import require_perm
from ..services.risks import evaluate

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", dependencies=[Depends(require_perm("ops:read"))])
def get_alerts(status: str = "", severity: str = "", kind: str = "",
               limit: int = 50, offset: int = 0) -> dict:
    pg = parse_paging(limit, offset)
    return list_alerts(status=status, severity=severity, kind=kind,
                       limit=pg["limit"], offset=pg["offset"])


@router.post("/evaluate", dependencies=[Depends(require_perm("etl:trigger")), CsrfChecked])
def post_evaluate() -> dict:
    con = warehouse_ro()
    try:
        items = evaluate(con)
    finally:
        con.close()
    return store_evaluation(items)


class AckIn(BaseModel):
    status: str = "acknowledged"


@router.patch("/{alert_id}", dependencies=[Depends(require_perm("ops:read")), CsrfChecked])
def patch_alert(alert_id: int, body: AckIn) -> dict:
    try:
        ok = set_status(alert_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"id": alert_id, "status": body.status}
