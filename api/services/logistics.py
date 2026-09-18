"""Logistics service — DataCo real data (shipping mode + region, no fake carriers)."""

from __future__ import annotations

import sqlite3


def _has_col(con: sqlite3.Connection, table: str, col: str) -> bool:
    try:
        return any(r[1] == col for r in con.execute(f"PRAGMA table_info({table})").fetchall())
    except Exception:  # noqa: BLE001
        return False


def _has_table(con: sqlite3.Connection, table: str) -> bool:
    try:
        return con.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name=?", (table,)).fetchone()[0] > 0
    except Exception:  # noqa: BLE001
        return False


def _is_dataco(con: sqlite3.Connection) -> bool:
    return (_has_col(con, "fact_deliveries", "status")
            and _has_col(con, "fact_shipments", "mode")
            and _has_table(con, "stg_dataco"))


def summary(con: sqlite3.Connection) -> dict:
    if not _is_dataco(con):  # legacy synthetic fixture warehouse
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
                "canceled_count": 0,
                "by_carrier": [{"carrier_id": r[0], "shipments": r[1], "otd": r[2], "avg_delay": r[3]}
                               for r in carriers],
                "by_mode": [],
                "by_region": [{"region": r[0], "shipments": r[1], "otd": r[2]} for r in regions]}
    base = con.execute(
        "SELECT COUNT(*), SUM(on_time), AVG(delay_days) FROM fact_deliveries"
        " WHERE status != 'Shipping canceled'").fetchone()
    delays = sorted(
        r[0] for r in con.execute(
            "SELECT delay_days FROM fact_deliveries WHERE status != 'Shipping canceled'"))
    p90 = delays[min(len(delays) - 1, int(0.9 * len(delays)))] if delays else None
    modes = con.execute(
        """SELECT COALESCE(s.mode,'?'), COUNT(*),
           ROUND(AVG(CAST(d.on_time AS FLOAT)),3), ROUND(AVG(d.delay_days),1)
        FROM fact_shipments s JOIN fact_deliveries d ON d.shipment_id=s.shipment_id
        WHERE d.status != 'Shipping canceled'
        GROUP BY 1 ORDER BY 3 ASC""").fetchall()
    regions = con.execute(
        """SELECT COALESCE(g.order_region,'?'), COUNT(*),
           ROUND(AVG(CAST(d.on_time AS FLOAT)),3), ROUND(AVG(d.delay_days),1)
        FROM stg_dataco g JOIN fact_deliveries d
          ON d.shipment_id = g.order_id || '-' || g.order_item_id
        WHERE d.status != 'Shipping canceled'
        GROUP BY 1 ORDER BY 3 ASC""").fetchall()
    return {"deliveries": base[0], "otd": round(base[1] / base[0], 3) if base[0] else None,
            "avg_delay_days": round(base[2], 1) if base[2] is not None else None,
            "p90_delay_days": p90,
            "late_count": con.execute(
                "SELECT COUNT(*) FROM fact_deliveries WHERE status='Late delivery'").fetchone()[0],
            "canceled_count": con.execute(
                "SELECT COUNT(*) FROM fact_deliveries WHERE status='Shipping canceled'").fetchone()[0],
            "by_carrier": [],
            "by_mode": [{"mode": r[0], "shipments": r[1], "otd": r[2], "avg_delay": r[3]}
                        for r in modes],
            "by_region": [{"region": r[0], "shipments": r[1], "otd": r[2], "avg_delay": r[3]}
                          for r in regions]}


def late_deliveries(con: sqlite3.Connection, limit: int = 50, offset: int = 0,
                    carrier: str = "", region: str = "", mode: str = "") -> dict:
    if not _is_dataco(con):  # legacy synthetic fixture warehouse
        conds = ["d.on_time=0"]
        params: list = []
        if carrier:
            conds.append("COALESCE(cr.carrier_id,'?')=?")
            params.append(carrier)
        if region:
            conds.append("COALESCE(w.region,'?')=?")
            params.append(region)
        where = "WHERE " + " AND ".join(conds)
        total = con.execute(
            f"""SELECT COUNT(*) FROM fact_deliveries d LEFT JOIN fact_shipments s ON s.shipment_id=d.shipment_id
            LEFT JOIN dim_carrier cr ON cr.carrier_sk=s.carrier_sk
            LEFT JOIN fact_sales f ON f.so_id=s.so_id
            LEFT JOIN dim_warehouse w ON w.warehouse_sk=f.warehouse_sk {where}""", params).fetchone()[0]
        rows = con.execute(
            f"""SELECT d.shipment_id, COALESCE(cr.carrier_id,'?'), d.promised_date_key, d.delivery_date_key,
               d.delay_days, d.delivered_qty, COALESCE(w.region,'?')
            FROM fact_deliveries d LEFT JOIN fact_shipments s ON s.shipment_id=d.shipment_id
            LEFT JOIN dim_carrier cr ON cr.carrier_sk=s.carrier_sk
            LEFT JOIN fact_sales f ON f.so_id=s.so_id
            LEFT JOIN dim_warehouse w ON w.warehouse_sk=f.warehouse_sk
            {where} ORDER BY d.delay_days DESC LIMIT ? OFFSET ?""", (*params, limit, offset)).fetchall()
        return {"total": total, "items": [
            {"shipment_id": r[0], "carrier_id": r[1], "mode": None, "promised": r[2],
             "delivered": r[3], "delay_days": r[4], "qty": r[5], "region": r[6],
             "market": None, "country": None} for r in rows]}
    conds = ["d.status='Late delivery'"]
    params: list = []
    if mode:
        conds.append("COALESCE(s.mode,'?')=?")
        params.append(mode)
    if region:
        conds.append("COALESCE(g.order_region,'?')=?")
        params.append(region)
    where = "WHERE " + " AND ".join(conds)
    total = con.execute(
        f"""SELECT COUNT(*) FROM fact_deliveries d
        JOIN fact_shipments s ON s.shipment_id=d.shipment_id
        JOIN stg_dataco g ON g.order_id || '-' || g.order_item_id = d.shipment_id
        {where}""", params).fetchone()[0]
    rows = con.execute(
        f"""SELECT d.shipment_id, COALESCE(s.mode,'?'), d.promised_date_key, d.delivery_date_key,
           d.delay_days, d.delivered_qty, COALESCE(g.order_region,'?'),
           COALESCE(g.market,'?'), COALESCE(g.order_country,'?')
        FROM fact_deliveries d
        JOIN fact_shipments s ON s.shipment_id=d.shipment_id
        JOIN stg_dataco g ON g.order_id || '-' || g.order_item_id = d.shipment_id
        {where} ORDER BY d.delay_days DESC, d.shipment_id LIMIT ? OFFSET ?""",
        (*params, limit, offset)).fetchall()
    return {"total": total, "items": [
        {"shipment_id": r[0], "carrier_id": None, "mode": r[1], "promised": r[2],
         "delivered": r[3], "delay_days": r[4], "qty": r[5], "region": r[6],
         "market": r[7], "country": r[8]} for r in rows]}
