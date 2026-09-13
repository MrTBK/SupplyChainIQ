"""Data-source routes: monitor status; guarded upload validates but never auto-loads."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..db import warehouse_ro
from ..csrf import CsrfChecked
from ..rbac import require_perm
from ..services.sources import find_duplicate, stage_upload, source_status, validate_upload

router = APIRouter(prefix="/api/data-sources", tags=["sources"])


@router.get("", dependencies=[Depends(require_perm("ops:read"))])
def get_sources() -> dict:
    con = warehouse_ro()
    try:
        items = source_status(con)
    finally:
        con.close()
    return {"total": len(items), "items": items}


@router.post("/{name}/upload", dependencies=[Depends(require_perm("sources:upload")), CsrfChecked])
async def upload_source(name: str, file: UploadFile = File(...)) -> dict:
    content = await file.read()
    report = validate_upload(name, content, file.content_type or "")
    if not report["ok"]:
        raise HTTPException(status_code=422, detail=report["error"])
    dup = find_duplicate("data/raw", name, report["sha256"])
    if dup:
        raise HTTPException(status_code=409, detail=f"Identical file already staged in batch '{dup}'")
    batch = "upload-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dest = stage_upload("data/raw", name, content, batch)
    return {**report, "staged_at": dest, "batch": batch}
