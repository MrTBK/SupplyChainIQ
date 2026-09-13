"""Recommendations: reorder, transfer, preferred supplier. Every item explains WHY."""

from __future__ import annotations

import math
import sqlite3

from analytics.prescriptions import reorder_recommendation, safety_stock
from forecasting.forecast import monthly_series


def _lead_p50(con: sqlite3.Connection, product_id: str) -> int:
    rows = con.execute(
        """SELECT CAST(julianday(f.receipt_date_key)-julianday(f.order_date_key) AS INTEGER)
        FROM fact_purchases f JOIN dim_product p ON p.product_sk=f.product_sk
        WHERE p.product_id=? ORDER BY 1""", (product_id,)).fetchall()
    vals = sorted(r[0] for r in rows)
    return vals[len(vals) // 2] if vals else 10


def recommend(con: sqlite3.Connection, product: str = "", kind: str = "") -> list[dict]:
    out: list[dict] = []
    series = monthly_series(con)
    snaps = con.execute(
        """SELECT p.product_id, w.warehouse_id, s.available, s.product_sk, s.warehouse_sk
        FROM fact_inventory_snapshot s
        JOIN dim_product p ON p.product_sk=s.product_sk
        JOIN dim_warehouse w ON w.warehouse_sk=s.warehouse_sk
        WHERE s.snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)
        AND s.product_sk != 0""").fetchall()
    by_product: dict[str, list] = {}
    for pid, wid, avail, ps, ws in snaps:
        if product and product.lower() not in pid.lower():
            continue
        hist = [qty for _, qty in series.get((ps, ws), [])]
        mu = sum(hist) / len(hist) if hist else 0
        sd = math.sqrt(sum((x - mu) ** 2 for x in hist) / len(hist)) if len(hist) > 1 else mu * 0.3 or 1.0
        lt = _lead_p50(con, pid)
        safety = safety_stock(sd, lt)
        fnext = (mu or 0) * (lt / 30)
        rec = reorder_recommendation(float(avail), 0.0, fnext, safety)
        row = {"kind": "reorder", "entity_id": f"{pid}@{wid}", "product_id": pid, "warehouse_id": wid,
               "current_stock": avail, "forecast_demand": rec["forecast_lead_demand"],
               "safety_stock": rec["safety_stock"], "supplier_lead_time_days": lt,
               "risk": rec["risk"], "recommended_quantity": rec["reorder_qty"], "reason": rec["reason"],
               "action": f"Reorder {rec['reorder_qty']} units of {pid} for {wid}" if rec["reorder_qty"] > 0
                         else f"{pid} at {wid} covered, no order",
               "_surplus": round(float(avail) - fnext - safety, 1)}
        by_product.setdefault(pid, []).append(row)
        if rec["reorder_qty"] > 0:
            out.append(row)
    # transfers: deficit in one warehouse, surplus in another for same product
    for pid, rows in by_product.items():
        deficits = [r for r in rows if r["recommended_quantity"] > 0]
        surpluses = [r for r in rows if r["_surplus"] > 0]
        for d in deficits:
            for s in surpluses:
                if s["warehouse_id"] == d["warehouse_id"]:
                    continue
                qty = round(min(s["_surplus"], d["recommended_quantity"]), 1)
                if qty > 0:
                    out.append({"kind": "transfer", "entity_id": f"{pid}:{s['warehouse_id']}->{d['warehouse_id']}",
                                "product_id": pid, "risk": d["risk"],
                                "reason": f"{d['warehouse_id']} needs {d['recommended_quantity']} while "
                                          f"{s['warehouse_id']} holds {s['_surplus']} surplus",
                                "recommended_quantity": qty,
                                "action": f"Transfer {qty} units of {pid} from {s['warehouse_id']} to {d['warehouse_id']}"})
                    break
    # preferred supplier per product: lowest avg cost among OTIF-acceptable suppliers
    pids = {r[0] for r in snaps if not product or product.lower() in r[0].lower()}
    for pid in sorted(pids):
        cands = con.execute(
            """SELECT s.supplier_id, AVG(f.unit_cost), AVG(CASE WHEN f.late_days<=0 THEN 1.0 ELSE 0 END), COUNT(*)
            FROM fact_purchases f JOIN dim_supplier s ON s.supplier_sk=f.supplier_sk
            JOIN dim_product p ON p.product_sk=f.product_sk
            WHERE p.product_id=? GROUP BY 1 HAVING COUNT(*)>=1""", (pid,)).fetchall()
        if not cands:
            continue
        ok = [c for c in cands if (c[2] or 0) >= 0.8] or cands
        best = min(ok, key=lambda c: c[1] / max(c[2] or 0.5, 0.5))
        out.append({"kind": "supplier", "entity_id": f"{pid}@{best[0]}", "product_id": pid,
                    "risk": "Low",
                    "reason": f"Lowest risk-adjusted cost {best[1]:.2f} with OTIF {(best[2] or 0):.2f} over {best[3]} receipts",
                    "recommended_quantity": 0,
                    "action": f"Prefer {best[0]} for {pid} (avg cost {best[1]:.2f})"})
    for r in out:
        r.pop("_surplus", None)
    if kind:
        out = [r for r in out if r["kind"] == kind]
    sev = {"High": 0, "Medium": 1, "Low": 2}
    out.sort(key=lambda r: (sev.get(r["risk"], 3), r["kind"]))
    return out
