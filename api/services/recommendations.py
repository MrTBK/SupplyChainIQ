"""Recommendations — generated ONLY from real detected conditions.

No inventory quantities: DataCo has no stock/safety/reorder inputs, so this
module emits investigations and mode/region/product actions with evidence.
Every item carries kind, entity, reason (with numbers), evidence source, action.
"""

from __future__ import annotations

import sqlite3

from .risks import evaluate


def _has_table(con: sqlite3.Connection, table: str) -> bool:
    try:
        return con.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name=?", (table,)).fetchone()[0] > 0
    except Exception:  # noqa: BLE001
        return False


def _has_col(con: sqlite3.Connection, table: str, col: str) -> bool:
    try:
        return any(r[1] == col for r in con.execute(f"PRAGMA table_info({table})").fetchall())
    except Exception:  # noqa: BLE001
        return False


def _is_dataco(con: sqlite3.Connection) -> bool:
    return (_has_table(con, "stg_dataco")
            and _has_col(con, "fact_deliveries", "status"))


def recommend(con: sqlite3.Connection, product: str = "", kind: str = "") -> list[dict]:
    if not _is_dataco(con):
        return _recommend_legacy(con, product, kind)
    out: list[dict] = []
    for r in evaluate(con):
        k = r["kind"]
        if k == "delivery_risk":
            out.append({"kind": "investigate_mode", "entity_id": r["entity_id"],
                        "product_id": None, "risk": r["severity"],
                        "reason": r["reason"],
                        "evidence": r.get("evidence", {}),
                        "recommended_quantity": 0,
                        "action": f"Prioritize {r['entity_id']} audit: sample delayed lines,"
                                  " compare scheduled vs lane norms, then shift urgent orders"})
        elif k == "regional_degradation":
            out.append({"kind": "investigate_region", "entity_id": r["entity_id"],
                        "product_id": None, "risk": r["severity"],
                        "reason": r["reason"],
                        "evidence": r.get("evidence", {}),
                        "recommended_quantity": 0,
                        "action": f"Open lane review for {r['entity_id']}: mode mix first,"
                                  " then carrier/last-mile handoff for top delayed corridors"})
        elif k == "demand_anomaly":
            if product and product.lower() not in str(r["entity_id"]).lower():
                continue
            out.append({"kind": "review_demand", "entity_id": r["entity_id"],
                        "product_id": r["entity_id"], "risk": r["severity"],
                        "reason": r["reason"],
                        "evidence": r.get("evidence", {}),
                        "recommended_quantity": 0,
                        "action": f"Freeze auto-forecast for {r['entity_id']} {r['metrics'].get('month')}:"
                                  " confirm one-off, exclude from baseline if so"})
        elif k == "cancellation_watch":
            out.append({"kind": "review_cancellations", "entity_id": "all",
                        "product_id": None, "risk": r["severity"],
                        "reason": r["reason"],
                        "evidence": r.get("evidence", {}),
                        "recommended_quantity": 0,
                        "action": "Investigate cancellation concentration by market, shipping mode,"
                                  " category and payment type"})
    if kind:
        out = [x for x in out if x["kind"] == kind]
    sev = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda x: (sev.get(x["risk"], 3), x["kind"], str(x["entity_id"])))
    return out


def _recommend_legacy(con: sqlite3.Connection, product: str = "", kind: str = "") -> list[dict]:
    """Pre-DataCo fixture path (reorder/transfer/supplier with stock math)."""
    import math
    from datetime import date

    from analytics.prescriptions import reorder_recommendation, safety_stock
    from forecasting.forecast import monthly_series

    def lead_p50(pid: str) -> int:
        rows = con.execute(
            """SELECT CAST(julianday(f.receipt_date_key)-julianday(f.order_date_key) AS INTEGER)
            FROM fact_purchases f JOIN dim_product p ON p.product_sk=f.product_sk
            WHERE p.product_id=? ORDER BY 1""", (pid,)).fetchall()
        vals = sorted(r[0] for r in rows)
        return vals[len(vals) // 2] if vals else 10

    out: list[dict] = []
    series = monthly_series(con)
    snaps = con.execute(
        """SELECT p.product_id, w.warehouse_id, s.available, s.product_sk, s.warehouse_sk
        FROM fact_inventory_snapshot s
        JOIN dim_product p ON p.product_sk=s.product_sk
        JOIN dim_warehouse w ON w.warehouse_sk=s.warehouse_sk
        WHERE s.snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)
        AND s.product_sk != 0""").fetchall()
    data_end = con.execute("SELECT MAX(date_key) FROM fact_sales").fetchone()[0] or ""
    by_product: dict[str, list] = {}
    for pid, wid, avail, _ps, _ws in snaps:
        if product and product.lower() not in pid.lower():
            continue
        hist = [qty for _, qty in series.get((_ps, _ws), [])]
        mu = sum(hist) / len(hist) if hist else 0
        sd = math.sqrt(sum((x - mu) ** 2 for x in hist) / len(hist)) if len(hist) > 1 else mu * 0.3 or 1.0
        lt = lead_p50(pid)
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
    for pid in sorted(by_product):
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
