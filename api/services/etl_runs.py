"""ETL run service: history from the execution log; trigger restricted to data/ dirs."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from etl.load import SOURCES, load_batch


def run_history(con: sqlite3.Connection, source: str = "", status: str = "",
                limit: int = 50, offset: int = 0) -> dict:
    conds, params = [], []
    if source:
        conds.append("source=?")
        params.append(source)
    if status:
        conds.append("status=?")
        params.append(status)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    total = con.execute(f"SELECT COUNT(*) FROM etl_execution_log {where}", params).fetchone()[0]
    rows = con.execute(
        f"""SELECT run_id, started_at, ended_at, source, rows_read, rows_accepted, rows_rejected,
            errors, status, duration_s FROM etl_execution_log {where}
            ORDER BY started_at DESC, run_id DESC LIMIT ? OFFSET ?""", (*params, limit, offset)).fetchall()
    return {"total": total, "items": [dict(r) for r in rows]}


def resolve_src(src: str, repo: Path) -> Path:
    """Allowlist: only directories inside <repo>/data. Blocks traversal and arbitrary paths."""
    base = (repo / "data").resolve()
    p = (repo / src).resolve() if not Path(src).is_absolute() else Path(src).resolve()
    if base not in p.parents and p != base:
        raise ValueError(f"Source '{src}' is outside the data/ allowlist")
    if not p.is_dir():
        raise ValueError(f"Source '{src}' is not an existing data directory")
    return p


def trigger(src: str, repo: Path, db_path: Path, batch: str = "") -> dict:
    if src.strip().lower() == "dataco":
        from etl.load_dataco import load as load_dataco
        out = load_dataco(db_path, batch or ("dataco-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")))
        return {"run_id": out["run_id"], "quarantined": out["rejected"],
                "duration_s": out["seconds"],
                "stats": {"dataco": {"accepted": out["accepted"], "rejected": out["rejected"]}}}
    src_dir = resolve_src(src, repo)
    batch = batch or ("api-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    out = load_batch(src_dir, db_path, batch)
    return {"run_id": out["run_id"], "quarantined": out["quarantined"],
            "duration_s": out["duration_s"],
            "stats": {k: v for k, v in out["stats"].items()}}
