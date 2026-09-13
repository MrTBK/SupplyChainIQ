"""ETL routes: monitor history; trigger is allowlisted, never arbitrary commands."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import config
from ..csrf import CsrfChecked
from ..db import warehouse_ro
from ..foundation import parse_paging
from ..rbac import current_user, require_perm
from ..services.etl_runs import run_history, trigger
from ..users import audit

router = APIRouter(prefix="/api/etl-runs", tags=["etl"])


@router.get("", dependencies=[Depends(require_perm("ops:read"))])
def get_runs(source: str = "", status: str = "", limit: int = 50, offset: int = 0) -> dict:
    pg = parse_paging(limit, offset)
    con = warehouse_ro()
    try:
        return run_history(con, source=source, status=status, limit=pg["limit"], offset=pg["offset"])
    finally:
        con.close()


class TriggerIn(BaseModel):
    src: str = "data/generated/seed-7"
    batch: str = ""


@router.post("/trigger", dependencies=[Depends(require_perm("etl:trigger")), CsrfChecked])
def post_trigger(body: TriggerIn, actor: dict = Depends(current_user)) -> dict:
    audit(str(actor["uid"]), "ETL_STARTED", f"src={body.src}")
    try:
        result = trigger(body.src, config.REPO, config.WAREHOUSE_DB, body.batch or "")
    except ValueError as e:
        audit(str(actor["uid"]), "ETL_FAILED", str(e)[:200])
        raise HTTPException(status_code=422, detail=str(e))
    audit(str(actor["uid"]), "ETL_COMPLETED",
          f"run={result['run_id']} quarantined={result['quarantined']}")
    return result
