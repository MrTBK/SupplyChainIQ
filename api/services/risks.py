"""Risk evaluation: every risk carries severity, entity, time, reason, metrics, action."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from analytics.analytics import demand_anomalies
from analytics.kpis import coverage_days
from analytics.prescriptions import reorder_recommendation, safety_stock
from forecasting.forecast import monthly_series


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def evaluate(con: sqlite3.Connection) -> list[dict]:
    now = _now()
    risks: list[dict] = []
    # stock-out risk per product/warehouse from coverage + reorder math
    snaps = con.execute(
        """SELECT p.product_id, w.warehouse_id, s.available, s.product_sk, s.warehouse_sk
        FROM fact_inventory_snapshot s
        JOIN dim_product p ON p.product_sk=s.product_sk
        JOIN dim_warehouse w ON w.warehouse_sk=s.warehouse_sk
        WHERE s.snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)
        AND s.product_sk != 0""").fetchall()
    for pid, wid, avail, ps, ws in snaps:
        cov = coverage_days(con, ps, ws)
        if cov is not None and cov < 14:
            rec = reorder_recommendation(float(avail), 0.0, float(avail) * 0.5 + 10, safety_stock(5, 7))
            risks.append({"kind": "stockout_risk", "severity": "high" if cov < 7 else "medium",
                          "entity_type": "product_warehouse", "entity_id": f"{pid}@{wid}",
                          "detected_at": now, "reason": f"Coverage {cov:.1f} days below 14-day buffer",
                          "metrics": {"coverage_days": round(cov, 1), "available": avail,
                                      "reorder_qty": rec["reorder_qty"]},
                          "action": f"Reorder {pid} for {wid} (see recommendations)"})
    # supplier degradation
    for sk, sid, n in con.execute(
            """SELECT f.supplier_sk, s.supplier_id, COUNT(*) FROM fact_purchases f
            JOIN dim_supplier s ON s.supplier_sk=f.supplier_sk
            GROUP BY 1,2 HAVING COUNT(*)>=5"""):
        otif = con.execute("SELECT AVG(CASE WHEN late_days<=0 THEN 1.0 ELSE 0 END) FROM fact_purchases "
                           "WHERE supplier_sk=?", (sk,)).fetchone()[0] or 0
        if otif < 0.8:
            risks.append({"kind": "supplier_degradation", "severity": "medium", "entity_type": "supplier",
                          "entity_id": sid, "detected_at": now,
                          "reason": f"OTIF {otif:.2f} below 0.80 over {n} receipts",
                          "metrics": {"otif": round(otif, 3), "receipts": n},
                          "action": f"Review {sid}: renegotiate service terms or shift volume"})
    # carrier degradation
    for cid, n, otd in con.execute(
            """SELECT COALESCE(cr.carrier_id,'?'), COUNT(*), AVG(CAST(d.on_time AS FLOAT))
            FROM fact_shipments s LEFT JOIN fact_deliveries d ON d.shipment_id=s.shipment_id
            LEFT JOIN dim_carrier cr ON cr.carrier_sk=s.carrier_sk GROUP BY 1 HAVING COUNT(*)>=5"""):
        if otd is not None and otd < 0.5:
            risks.append({"kind": "delivery_risk", "severity": "medium", "entity_type": "carrier",
                          "entity_id": cid, "detected_at": now,
                          "reason": f"Carrier OTD {otd:.2f} below 0.50 over {n} shipments",
                          "metrics": {"otd": round(otd, 3), "shipments": n},
                          "action": f"Reroute volume off {cid}; expedite at-risk lanes"})
    # demand anomalies (z>=3 on monthly series)
    for (ps, ws), series in monthly_series(con).items():
        hist = [qty for _, qty in series]
        for idx in demand_anomalies(hist):
            pid = con.execute("SELECT product_id FROM dim_product WHERE product_sk=?", (ps,)).fetchone()[0]
            wid = con.execute("SELECT warehouse_id FROM dim_warehouse WHERE warehouse_sk=?", (ws,)).fetchone()[0]
            risks.append({"kind": "demand_anomaly", "severity": "medium", "entity_type": "product_warehouse",
                          "entity_id": f"{pid}@{wid}", "detected_at": now,
                          "reason": f"Month {series[idx][0]} demand {series[idx][1]:.0f} is a 3-sigma outlier",
                          "metrics": {"month": series[idx][0], "qty": series[idx][1]},
                          "action": "Check promo/one-off cause before adjusting forecast"})
    order = {"high": 0, "medium": 1, "low": 2}
    risks.sort(key=lambda r: (order[r["severity"]], r["kind"], r["entity_id"]))
    return risks
