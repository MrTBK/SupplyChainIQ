"""Inventory service: stock list + product drill reusing kpis/forecast/prescriptions."""

from __future__ import annotations

import math
import sqlite3

from analytics.kpis import coverage_days
from analytics.prescriptions import reorder_recommendation, safety_stock
from forecasting.forecast import forecast_all

from .overview import overview  # noqa: F401  (keeps service package surface obvious)


def stock_list(con: sqlite3.Connection, search: str = "", warehouse: str = "",
               low_stock: bool = False, limit: int = 50, offset: int = 0,
               coverage_under: float = 14.0) -> dict:
    params: list = []
    where = ["s.snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)"]
    if search:
        where.append("(p.product_id LIKE ? ESCAPE '\\' OR p.sku LIKE ? ESCAPE '\\' OR p.name LIKE ? ESCAPE '\\')")
        from api.foundation import like_param
        params += [like_param(search)] * 3
    if warehouse:
        where.append("w.warehouse_id=?")
        params.append(warehouse)
    rows = con.execute(
        f"""SELECT p.product_id, p.sku, p.name, p.category, w.warehouse_id, w.region,
            s.available, s.unit_cost, s.product_sk, s.warehouse_sk
        FROM fact_inventory_snapshot s
        JOIN dim_product p ON p.product_sk=s.product_sk
        JOIN dim_warehouse w ON w.warehouse_sk=s.warehouse_sk
        WHERE {' AND '.join(where)} ORDER BY p.product_id, w.warehouse_id""", params).fetchall()
    items = []
    for r in rows:
        cov = coverage_days(con, r["product_sk"], r["warehouse_sk"])
        item = {"product_id": r["product_id"], "sku": r["sku"], "name": r["name"],
                "category": r["category"], "warehouse_id": r["warehouse_id"], "region": r["region"],
                "available": r["available"], "unit_cost": r["unit_cost"],
                "value": round(r["available"] * r["unit_cost"], 2),
                "coverage_days": round(cov, 1) if cov is not None else None}
        if low_stock and (cov is None or cov >= coverage_under):
            continue
        items.append(item)
    total = len(items)
    return {"total": total, "items": items[offset:offset + limit]}


def product_drill(con: sqlite3.Connection, product_id: str, warehouse_id: str = "") -> dict | None:
    prow = con.execute("SELECT product_sk, sku, name, category, standard_cost FROM dim_product "
                       "WHERE product_id=? AND is_current=1", (product_id,)).fetchone()
    if not prow:
        return None
    wh_filter, params = ("", [prow["product_sk"]]) if not warehouse_id else ("AND w.warehouse_id=?", [prow["product_sk"], warehouse_id])
    stocks = con.execute(
        f"""SELECT w.warehouse_id, w.region, s.available, s.unit_cost, s.product_sk, s.warehouse_sk
        FROM fact_inventory_snapshot s
        JOIN dim_warehouse w ON w.warehouse_sk=s.warehouse_sk
        WHERE s.product_sk=? AND s.snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)
        {wh_filter}""", params).fetchall()
    if not stocks:
        return None
    demand = con.execute(
        "SELECT substr(date_key,1,7) m, SUM(qty) FROM fact_sales WHERE product_sk=? GROUP BY 1 ORDER BY 1 DESC LIMIT 12",
        (prow["product_sk"],)).fetchall()
    hist = [float(r[1]) for r in reversed(demand)]
    fc = [f for f in forecast_all(con) if f["product_sk"] == prow["product_sk"]]
    if warehouse_id:
        fc = [f for f in fc if con.execute("SELECT warehouse_id FROM dim_warehouse WHERE warehouse_sk=?",
                                           (f["warehouse_sk"],)).fetchone()[0] == warehouse_id]
    lead = con.execute(
        """SELECT CAST(julianday(f.receipt_date_key)-julianday(f.order_date_key) AS INTEGER)
        FROM fact_purchases f JOIN dim_product p ON p.product_sk=f.product_sk
        WHERE p.product_id=? ORDER BY 1""", (product_id,)).fetchall()
    lead_days = sorted(r[0] for r in lead)
    p50 = lead_days[len(lead_days) // 2] if lead_days else 10
    mu = sum(hist) / len(hist) if hist else 0
    sd = math.sqrt(sum((x - mu) ** 2 for x in hist) / len(hist)) if len(hist) > 1 else mu * 0.3
    safety = safety_stock(sd, p50)
    per_wh = []
    for s in stocks:
        fcs = [f for f in fc if f["warehouse_sk"] == s["warehouse_sk"]]
        fnext = fcs[0]["forecast_next"] * (p50 / 30) if fcs else mu * (p50 / 30)
        rec = reorder_recommendation(float(s["available"]), 0.0, fnext, safety)
        cov = coverage_days(con, s["product_sk"], s["warehouse_sk"])
        per_wh.append({"warehouse_id": s["warehouse_id"], "region": s["region"],
                       "available": s["available"], "coverage_days": round(cov, 1) if cov is not None else None,
                       "forecast_lead_demand": rec["forecast_lead_demand"], "safety_stock": rec["safety_stock"],
                       "reorder_qty": rec["reorder_qty"], "risk": rec["risk"], "reason": rec["reason"]})
    return {"product_id": product_id, "sku": prow["sku"], "name": prow["name"], "category": prow["category"],
            "standard_cost": prow["standard_cost"], "recent_monthly_demand": [{"month": r[0], "qty": r[1]} for r in demand],
            "forecast": fc[0] if len(fc) == 1 else fc, "lead_time_p50_days": p50,
            "warehouses": per_wh}
