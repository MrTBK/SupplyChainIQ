"""Recommendation routes: explainable prescriptions only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import users as ustore
from ..csrf import CsrfChecked
from ..db import warehouse_ro
from ..rbac import current_user, require_perm
from ..recs import get_map, set_status
from ..services.linkage import link
from ..services.recommendations import recommend
from ..services.risks import evaluate

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("", dependencies=[Depends(require_perm("ops:read"))])
def get_recommendations(product: str = "", kind: str = "", rec_status: str = "") -> dict:
    con = warehouse_ro()
    try:
        items = recommend(con, product=product, kind=kind)
        risks, items = link(evaluate(con), items)
    finally:
        con.close()
    states = get_map([i["id"] for i in items])
    for i in items:
        st = states.get(i["id"], {"status": "pending", "actor": "", "updated_at": ""})
        i["rec_status"] = st["status"]
        i["rec_actor"] = st["actor"]
        i["rec_updated_at"] = st["updated_at"]
    if rec_status:
        items = [i for i in items if i["rec_status"] == rec_status]
    return {"total": len(items), "items": items}


class RecStatusIn(BaseModel):
    status: str = "reviewed"


@router.patch("/{rec_id}", dependencies=[Depends(require_perm("ops:read")), CsrfChecked])
def patch_recommendation(rec_id: str, body: RecStatusIn, actor: dict = Depends(current_user)) -> dict:
    try:
        name = next((u["username"] for u in ustore.list_users() if u["id"] == actor["uid"]),
                    str(actor["uid"]))
        set_status(rec_id, body.status, name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    ustore.audit(str(actor["uid"]), f"recommendation.{body.status}", rec_id)
    return {"id": rec_id, "status": body.status}
