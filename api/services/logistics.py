"""Logistics service: delivery performance, late list, carrier and region cuts."""

from __future__ import annotations

import sqlite3


def summary(con: sqlite3.Connection) -> dict:
    base = con.execute("SELECT COUNT(*), SUM(on_time), AVG(delay_days) FROM fact_deliveries").fetchone()
    delays = sorted(r[0] for r in con.execute("SELECT delay_days FROM fact_deliveries"))
    p90 = delays[min(len(delays) - 1, int(0.9 * len(delays)))] if delays else None
    carriers = con.execute(
        """SELECT COALESCE(cr.carrier_id,'?'), COUNT(*),
           ROUND(AVG(CAST(d.on_time AS FLOAT)),3), ROUND(AVG(d.delay_days),1)
        FROM fact_shipments s LEFT JOIN fact_deliveries d ON d.shipment_id=s.shipment_id
        LEFT JOIN dim_carrier cr ON cr.carrier_sk=s.carrier_sk
        GROUP BY 1 ORDER BY 3 ASC""").fetchall()
    regions = con.execute(
        """SELECT COALESCE(w.region,'?'), COUNT(*), ROUND(AVG(CAST(d.on_time AS FLOAT)),3)
        FROM fact_shipments s LEFT JOIN fact_deliveries d ON d.shipment_id=s.shipment_id
        LEFT JOIN fact_sales f ON f.so_id=s.so_id
        LEFT JOIN dim_warehouse w ON w.warehouse_sk=f.warehouse_sk
        GROUP BY 1 ORDER BY 3 ASC""").fetchall()
    return {"deliveries": base[0], "otd": round(base[1] / base[0], 3) if base[0] else None,
            "avg_delay_days": round(base[2], 1) if base[2] is not None else None,
            "p90_delay_days": p90,
            "late_count": con.execute("SELECT COUNT(*) FROM fact_deliveries WHERE on_time=0").fetchone()[0],
            "by_carrier": [{"carrier_id": r[0], "shipments": r[1], "otd": r[2], "avg_delay": r[3]} for r in carriers],
            "by_region": [{"region": r[0], "shipments": r[1], "otd": r[2]} for r in regions]}


def late_deliveries(con: sqlite3.Connection, limit: int = 50, offset: int = 0) -> dict:
    total = con.execute("SELECT COUNT(*) FROM fact_deliveries WHERE on_time=0").fetchone()[0]
    rows = con.execute(
        """SELECT d.shipment_id, COALESCE(cr.carrier_id,'?'), d.promised_date_key, d.delivery_date_key,
           d.delay_days, d.delivered_qty
        FROM fact_deliveries d LEFT JOIN fact_shipments s ON s.shipment_id=d.shipment_id
        LEFT JOIN dim_carrier cr ON cr.carrier_sk=s.carrier_sk
        WHERE d.on_time=0 ORDER BY d.delay_days DESC LIMIT ? OFFSET ?""", (limit, offset)).fetchall()
    return {"total": total, "items": [
        {"shipment_id": r[0], "carrier_id": r[1], "promised": r[2], "delivered": r[3],
         "delay_days": r[4], "qty": r[5]} for r in rows]}
