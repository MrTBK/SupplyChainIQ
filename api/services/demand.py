"""Demand trend service: monthly totals + top categories (aggregated in SQL)."""

from __future__ import annotations

import sqlite3


def trend(con: sqlite3.Connection, months: int = 12) -> dict:
    try:
        from forecasting.forecast import ANALYSIS_END
        has_stg = con.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='stg_dataco'").fetchone()[0] > 0
        has_status = any(r[1] == "status"
                         for r in con.execute("PRAGMA table_info(fact_deliveries)").fetchall())
        end = ANALYSIS_END if (has_stg and has_status) else None
    except Exception:  # noqa: BLE001
        end = None
    if end:
        rows = con.execute(
            """SELECT substr(date_key,1,7) m, SUM(qty), SUM(net_amount) FROM fact_sales
            WHERE date_key <= ? GROUP BY 1 ORDER BY 1 DESC LIMIT ?""", (end, months)).fetchall()
    else:
        rows = con.execute(
            """SELECT substr(date_key,1,7) m, SUM(qty), SUM(net_amount) FROM fact_sales
            GROUP BY 1 ORDER BY 1 DESC LIMIT ?""", (months,)).fetchall()
    rows = list(reversed(rows))
    cats = con.execute(
        """SELECT p.category, SUM(f.qty * f.unit_price) FROM fact_sales f
        JOIN dim_product p ON p.product_sk=f.product_sk
        GROUP BY 1 ORDER BY 2 DESC LIMIT 5""").fetchall()
    return {"months": [{"month": r[0], "qty": r[1], "revenue": round(r[2], 2)} for r in rows],
            "top_categories": [{"category": r[0], "revenue": round(r[1], 2)} for r in cats]}
