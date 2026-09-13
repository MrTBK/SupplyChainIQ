"""Demand trend service: monthly totals + top categories (aggregated in SQL)."""

from __future__ import annotations

import sqlite3


def trend(con: sqlite3.Connection, months: int = 12) -> dict:
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
