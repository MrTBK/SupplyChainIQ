"""Alerts store: persisted evaluations with day-level dedupe + acknowledge workflow."""

from __future__ import annotations

import json
import sqlite3

from .db import app_db

STATUSES = ("open", "acknowledged", "resolved")


def init_alerts_schema() -> None:
    con = app_db()
    con.execute("""CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY,
        detected_at TEXT NOT NULL,
        kind TEXT NOT NULL,
        severity TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        metrics_json TEXT NOT NULL DEFAULT '{}',
        action TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'open',
        dedupe_key TEXT NOT NULL UNIQUE)""")
    con.commit()
    con.close()


def store_evaluation(items: list[dict]) -> dict:
    """Persist evaluation; same kind+entity+day collapses via dedupe (no spam)."""
    con = app_db()
    new = 0
    for it in items:
        day = it["detected_at"][:10]
        key = f"{it['kind']}|{it['entity_id']}|{day}"
        cur = con.execute(
            "INSERT OR IGNORE INTO alerts (detected_at, kind, severity, entity_type, entity_id,"
            " reason, metrics_json, action, status, dedupe_key) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (it["detected_at"], it["kind"], it["severity"], it["entity_type"], it["entity_id"],
             it["reason"], json.dumps(it["metrics"]), it["action"], "open", key))
        new += cur.rowcount
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM alerts WHERE status='open'").fetchone()[0]
    con.close()
    return {"stored_new": new, "open_total": total}


def list_alerts(status: str = "", severity: str = "", kind: str = "",
                limit: int = 50, offset: int = 0) -> dict:
    con = app_db()
    conds, params = [], []
    for col, val in (("status", status), ("severity", severity), ("kind", kind)):
        if val:
            conds.append(f"{col}=?")
            params.append(val)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    total = con.execute(f"SELECT COUNT(*) FROM alerts {where}", params).fetchone()[0]
    rows = con.execute(
        f"""SELECT id, detected_at, kind, severity, entity_type, entity_id, reason,
            metrics_json, action, status FROM alerts {where}
            ORDER BY detected_at DESC, id DESC LIMIT ? OFFSET ?""",
        (*params, limit, offset)).fetchall()
    con.close()
    items = []
    for r in rows:
        d = dict(r)
        d["metrics"] = json.loads(d.pop("metrics_json"))
        items.append(d)
    return {"total": total, "items": items}


def set_status(alert_id: int, status: str) -> bool:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    con = app_db()
    cur = con.execute("UPDATE alerts SET status=? WHERE id=?", (status, alert_id))
    con.commit()
    con.close()
    return cur.rowcount == 1
