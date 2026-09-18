"""Risk evaluation — DataCo real signals, prediction-safe features only.

Post-outcome fields (Late_delivery_risk, Delivery Status, real days, delay)
are NEVER features; they are only labels/evidence. Detection rules use
pre-outcome slices (mode, market/region, department/category, scheduled days)
or realized aggregates clearly labeled as observed (not predicted).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from analytics.analytics import demand_anomalies
from forecasting.forecast import monthly_series


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def evaluate(con: sqlite3.Connection) -> list[dict]:
    if not _is_dataco(con):
        return _evaluate_legacy(con)
    now = _now()
    risks: list[dict] = []
    total = con.execute(
        "SELECT COUNT(*) FROM fact_deliveries WHERE status != 'Shipping canceled'").fetchone()[0] or 0

    def rate(where: str, params: tuple = ()) -> tuple[float, int]:
        r = con.execute(
            f"""SELECT COUNT(*), SUM(CASE WHEN d.status='Late delivery' THEN 1 ELSE 0 END)
            FROM fact_deliveries d JOIN fact_shipments s ON s.shipment_id=d.shipment_id
            JOIN stg_dataco g ON g.order_id || '-' || g.order_item_id = d.shipment_id
            WHERE d.status != 'Shipping canceled' AND ({where})""", params).fetchone()
        n = r[0] or 0
        return ((r[1] or 0) / n if n else 0.0, n)

    overall = con.execute(
        "SELECT AVG(CASE WHEN status='Late delivery' THEN 1.0 ELSE 0 END)"
        " FROM fact_deliveries WHERE status != 'Shipping canceled'").fetchone()[0] or 0

    # mode degradation (observed, decision-time slice: shipping mode chosen at order)
    for mode, n, otd in con.execute(
            """SELECT COALESCE(s.mode,'?'), COUNT(*),
               AVG(CASE WHEN d.status != 'Late delivery' THEN 1.0 ELSE 0 END)
            FROM fact_shipments s JOIN fact_deliveries d ON d.shipment_id=s.shipment_id
            WHERE d.status != 'Shipping canceled'
            GROUP BY 1 HAVING COUNT(*) >= 1000"""):
        late = 1 - (otd or 0)
        if late > overall + 0.05:
            risks.append({"kind": "delivery_risk", "severity": "high" if late > overall + 0.15 else "medium",
                          "entity_type": "shipping_mode", "entity_id": mode, "detected_at": now,
                          "reason": f"Late rate {late:.1%} vs network {overall:.1%} over {n} delivered lines",
                          "metrics": {"late_rate": round(late, 3), "network_late_rate": round(overall, 3),
                                      "lines": n},
                          "evidence": {"source": "fact_deliveries.status", "filter": f"mode={mode}",
                                       "excludes": "Shipping canceled"},
                          "impact": "Higher expedite / credit exposure on this mode",
                          "action": f"Review {mode}: shift time-critical volume or renegotiate SLA"})
    # regional degradation
    for region, n in con.execute(
            """SELECT COALESCE(g.order_region,'?'), COUNT(*)
            FROM stg_dataco g JOIN fact_deliveries d
              ON d.shipment_id = g.order_id || '-' || g.order_item_id
            WHERE d.status != 'Shipping canceled'
            GROUP BY 1 HAVING COUNT(*) >= 1000"""):
        late, _ = rate("COALESCE(g.order_region,'?')=?", (region,))
        if n and late > overall + 0.07:
            risks.append({"kind": "regional_degradation", "severity": "high" if late > overall + 0.2 else "medium",
                          "entity_type": "region", "entity_id": region, "detected_at": now,
                          "reason": f"Late rate {late:.1%} vs network {overall:.1%} over {n} lines",
                          "metrics": {"late_rate": round(late, 3), "network_late_rate": round(overall, 3),
                                      "lines": n},
                          "evidence": {"source": "stg_dataco.order_region × fact_deliveries.status"},
                          "impact": "Lane-level SLA breach risk for customers in this region",
                          "action": f"Investigate {region} lanes: mode mix, customs, last-mile"})
    # cancellation watch (observed)
    cancels = con.execute(
        "SELECT COUNT(*) FROM fact_deliveries WHERE status='Shipping canceled'").fetchone()[0] or 0
    if total and cancels / (total + cancels) > 0.03:
        suspected = con.execute(
            "SELECT COUNT(*) FROM stg_dataco WHERE delivery_status='Shipping canceled'"
            " AND order_status='SUSPECTED_FRAUD'").fetchone()[0] or 0
        by_market = con.execute(
            """SELECT COALESCE(g.market,'?'), COUNT(*) FROM stg_dataco g
            JOIN fact_deliveries d ON d.shipment_id = g.order_id || '-' || g.order_item_id
            WHERE d.status='Shipping canceled' GROUP BY 1 ORDER BY 2 DESC LIMIT 3""").fetchall()
        risks.append({"kind": "cancellation_watch", "severity": "medium", "entity_type": "network",
                      "entity_id": "all", "detected_at": now,
                      "reason": f"{cancels} canceled lines ({cancels/(total+cancels):.1%} of all);"
                                f" top markets: {', '.join(f'{m} {n}' for m, n in by_market)}",
                      "metrics": {"canceled": cancels, "delivered": total,
                                  "suspected_fraud_lines": suspected,
                                  "top_markets": [{"market": m, "canceled": n} for m, n in by_market]},
                      "evidence": {"source": "fact_deliveries.status='Shipping canceled' joined to"
                                             " stg_dataco (Order Status SUSPECTED_FRAUD is a source field,"
                                             " not an analytical label)"},
                      "impact": "Lost revenue + payment-review load",
                      "action": "Drill cancellation by market, shipping mode, category and payment type"
                                " (Type) before changing review policy"})
    # demand anomalies (z>=3 on monthly product series, complete-coverage window)
    try:
        from forecasting.forecast import ANALYSIS_END
        series = monthly_series(con, end=ANALYSIS_END, by_product=True)
    except Exception:  # noqa: BLE001 - empty warehouse
        series = {}
    prod_name = {r[0]: r[1] for r in con.execute("SELECT product_sk, product_id FROM dim_product")}
    for (ps, _wh), months in series.items():
        hist = [qty for _, qty in months]
        for idx in demand_anomalies(hist):
            pid = prod_name.get(ps, "?")
            risks.append({"kind": "demand_anomaly", "severity": "medium",
                          "entity_type": "product", "entity_id": pid, "detected_at": now,
                          "reason": f"Month {months[idx][0]} demand {months[idx][1]:.0f} is a 3-sigma outlier",
                          "metrics": {"month": months[idx][0], "qty": months[idx][1]},
                          "evidence": {"source": "fact_sales monthly aggregation"},
                          "impact": "Forecast bias if one-off not excluded",
                          "action": "Check promo/one-off cause before adjusting forecast"})
    order = {"high": 0, "medium": 1, "low": 2}
    risks.sort(key=lambda r: (order[r["severity"]], r["kind"], str(r["entity_id"])))
    return risks


def _evaluate_legacy(con: sqlite3.Connection) -> list[dict]:
    """Pre-DataCo synthetic-fixture evaluation (inventory/supplier/carrier).

    Kept so hermetic fixture tests stay green; production DataCo warehouse
    always takes the DataCo branch above.
    """
    from analytics.kpis import coverage_days
    from analytics.prescriptions import reorder_recommendation, safety_stock

    now = _now()
    risks: list[dict] = []
    try:
        snaps = con.execute(
            """SELECT p.product_id, w.warehouse_id, s.available, s.product_sk, s.warehouse_sk
            FROM fact_inventory_snapshot s
            JOIN dim_product p ON p.product_sk=s.product_sk
            JOIN dim_warehouse w ON w.warehouse_sk=s.warehouse_sk
            WHERE s.snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)
            AND s.product_sk != 0""").fetchall()
    except Exception:  # noqa: BLE001
        snaps = []
    for pid, wid, avail, ps, ws in snaps:
        try:
            cov = coverage_days(con, ps, ws)
        except Exception:  # noqa: BLE001
            cov = None
        if cov is not None and cov < 14:
            rec = reorder_recommendation(float(avail), 0.0, float(avail) * 0.5 + 10, safety_stock(5, 7))
            risks.append({"kind": "stockout_risk", "severity": "high" if cov < 7 else "medium",
                          "entity_type": "product_warehouse", "entity_id": f"{pid}@{wid}",
                          "detected_at": now, "reason": f"Coverage {cov:.1f} days below 14-day buffer",
                          "metrics": {"coverage_days": round(cov, 1), "available": avail,
                                      "reorder_qty": rec["reorder_qty"]},
                          "evidence": {"source": "fact_inventory_snapshot"},
                          "impact": "Stockout exposure", 
                          "action": f"Reorder {pid} for {wid} (see recommendations)"})
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
                          "evidence": {"source": "fact_purchases"},
                          "impact": "Supply disruption exposure",
                          "action": f"Review {sid}: renegotiate service terms or shift volume"})
    for cid, n, otd in con.execute(
            """SELECT COALESCE(cr.carrier_id,'?'), COUNT(*), AVG(CAST(d.on_time AS FLOAT))
            FROM fact_shipments s LEFT JOIN fact_deliveries d ON d.shipment_id=s.shipment_id
            LEFT JOIN dim_carrier cr ON cr.carrier_sk=s.carrier_sk GROUP BY 1 HAVING COUNT(*)>=5"""):
        if otd is not None and otd < 0.5:
            risks.append({"kind": "delivery_risk", "severity": "medium", "entity_type": "carrier",
                          "entity_id": cid, "detected_at": now,
                          "reason": f"Carrier OTD {otd:.2f} below 0.50 over {n} shipments",
                          "metrics": {"otd": round(otd, 3), "shipments": n},
                          "evidence": {"source": "fact_deliveries"},
                          "impact": "Delivery SLA exposure",
                          "action": f"Reroute volume off {cid}; expedite at-risk lanes"})
    order = {"high": 0, "medium": 1, "low": 2}
    risks.sort(key=lambda r: (order[r["severity"]], r["kind"], str(r["entity_id"])))
    return risks
