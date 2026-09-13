"""ETL routes: monitor history; trigger is allowlisted, never arbitrary commands."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import config
from ..db import warehouse_ro
from ..foundation import parse_paging
from ..csrf import CsrfChecked
from ..rbac import require_perm
from ..services.etl_runs import run_history, trigger

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
def post_trigger(body: TriggerIn) -> dict:
    try:
        return trigger(body.src, config.REPO, config.WAREHOUSE_DB, body.batch or "")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
