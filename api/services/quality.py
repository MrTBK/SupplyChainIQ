"""DQ service: batch scores vs gate, quarantine drill-down, rule catalog from yml."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

DQ_THRESHOLD = 0.98


def rules(repo: Path) -> list[dict]:
    text = (repo / "etl" / "dq_rules.yml").read_text()
    out = []
    for m in re.finditer(r"id:\s*(\w+),\s*dimension:\s*(\w+),\s*severity:\s*(\w+)", text):
        out.append({"id": m.group(1), "dimension": m.group(2), "severity": m.group(3)})
    return out


def latest_scores(con: sqlite3.Connection) -> dict:
    rows = con.execute(
        """SELECT s.source, s.score, s.rows_read, s.rows_accepted, s.run_id
        FROM dq_batch_score s
        WHERE s.run_id = (SELECT MAX(run_id) FROM dq_batch_score d WHERE d.source=s.source)""").fetchall()
    items = [{"source": r[0], "score": r[1], "rows_read": r[2], "rows_accepted": r[3],
              "run_id": r[4], "gate": "pass" if r[1] >= DQ_THRESHOLD else "BLOCKED"} for r in rows]
    overall = round(sum(r[1] for r in rows) / len(rows), 4) if rows else None
    return {"threshold": DQ_THRESHOLD,
            "overall": overall,
            "gate": "pass" if overall is not None and overall >= DQ_THRESHOLD else ("empty" if overall is None else "BLOCKED"),
            "sources": items}


def quarantine(con: sqlite3.Connection, source: str = "", rule: str = "",
               limit: int = 50, offset: int = 0) -> dict:
    conds, params = [], []
    if source:
        conds.append("source=?")
        params.append(source)
    if rule:
        conds.append("rule_id=?")
        params.append(rule)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    total = con.execute(f"SELECT COUNT(*) FROM dq_quarantine {where}", params).fetchone()[0]
    rows = con.execute(
        f"""SELECT run_id, source, business_key, rule_id, reason, payload, created_at
        FROM dq_quarantine {where} ORDER BY id DESC LIMIT ? OFFSET ?""",
        (*params, limit, offset)).fetchall()
    return {"total": total, "items": [dict(r) for r in rows]}
