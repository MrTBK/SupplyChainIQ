"""Supplier service: ranking with OTIF, lead-time, spend, score (reuses analytics)."""

from __future__ import annotations

import sqlite3

from analytics.analytics import lead_time_stats, supplier_score


def supplier_list(con: sqlite3.Connection, search: str = "", limit: int = 50, offset: int = 0,
                  ordering: str = "-score") -> dict:
    conds = ["s.supplier_sk != 0"]
    params: list = []
    if search:
        from api.foundation import like_param
        conds.append("(s.supplier_id LIKE ? ESCAPE '\\' OR s.name LIKE ? ESCAPE '\\')")
        params = [like_param(search)] * 2
    sups = con.execute(
        "SELECT supplier_sk, supplier_id, name, rating_tier FROM dim_supplier s WHERE "
        + " AND ".join(conds) + " ORDER BY supplier_id", params).fetchall()
    items = []
    for s in sups:
        agg = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(received_qty*unit_cost),0) FROM fact_purchases WHERE supplier_sk=?",
            (s["supplier_sk"],)).fetchone()
        score = supplier_score(con, s["supplier_sk"])
        lt = lead_time_stats(con, s["supplier_sk"])
        items.append({"supplier_id": s["supplier_id"], "name": s["name"], "rating_tier": s["rating_tier"],
                      "receipts": agg[0], "spend": round(agg[1], 2), "otif": score["otif"],
                      "score": score["score"], "lead_p50": lt.get("p50"), "lead_p90": lt.get("p90")})
    key = {"-score": lambda x: -x["score"], "score": lambda x: x["score"],
           "-otif": lambda x: -(x["otif"] or 0), "-spend": lambda x: -x["spend"],
           "spend": lambda x: x["spend"]}.get(ordering, lambda x: -x["score"])
    items.sort(key=key)
    return {"total": len(items), "items": items[offset:offset + limit]}


def supplier_detail(con: sqlite3.Connection, supplier_id: str) -> dict | None:
    s = con.execute("SELECT supplier_sk, name, rating_tier FROM dim_supplier "
                    "WHERE supplier_id=? AND is_current=1", (supplier_id,)).fetchone()
    if not s:
        return None
    trend = con.execute(
        "SELECT substr(receipt_date_key,1,7) m, SUM(received_qty*unit_cost), SUM(received_qty) "
        "FROM fact_purchases WHERE supplier_sk=? GROUP BY 1 ORDER BY 1 DESC LIMIT 12", (s["supplier_sk"],)).fetchall()
    return {"supplier_id": supplier_id, "name": s["name"], "rating_tier": s["rating_tier"],
            "score": supplier_score(con, s["supplier_sk"]),
            "lead_time": lead_time_stats(con, s["supplier_sk"]),
            "monthly_spend": [{"month": r[0], "spend": round(r[1], 2), "qty": r[2]} for r in trend]}
