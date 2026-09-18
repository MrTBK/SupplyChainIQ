"""Recommendation lifecycle: persisted review states keyed by stable rec IDs.

States persist across reloads/users; every transition is audited by the route.
Absent row == 'pending'. Unknown-but-wellformed IDs are accepted (a rec may
age out of the engine while its review history remains meaningful).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from .db import app_db

STATUSES = ("pending", "reviewed", "approved", "rejected", "executed", "expired")
REC_ID_RE = re.compile(r"^REC-[A-Za-z0-9_]+-[A-Za-z0-9_@.:>-]+$")


def init_rec_schema() -> None:
    con = app_db()
    con.execute("""CREATE TABLE IF NOT EXISTS rec_status (
        rec_id TEXT PRIMARY KEY, status TEXT NOT NULL DEFAULT 'pending',
        actor TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT '')""")
    con.commit()
    con.close()


def get_map(rec_ids: list[str]) -> dict:
    if not rec_ids:
        return {}
    con = app_db()
    rows = con.execute(
        f"SELECT rec_id, status, actor, updated_at FROM rec_status WHERE rec_id IN "
        f"({','.join('?' * len(rec_ids))})", rec_ids).fetchall()
    con.close()
    return {r[0]: {"status": r[1], "actor": r[2], "updated_at": r[3]} for r in rows}


def set_status(rec_id: str, status: str, actor: str) -> None:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    if not REC_ID_RE.match(rec_id):
        raise ValueError(f"unknown recommendation '{rec_id}'")
    con = app_db()
    con.execute("INSERT INTO rec_status (rec_id, status, actor, updated_at) VALUES (?,?,?,?) "
                "ON CONFLICT(rec_id) DO UPDATE SET status=excluded.status, actor=excluded.actor, "
                "updated_at=excluded.updated_at",
                (rec_id, status, actor, datetime.now(timezone.utc).isoformat()))
    con.commit()
    con.close()
