"""Executive overview service — DataCo real data (no synthetic inventory/procurement)."""

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


def overview(con: sqlite3.Connection) -> dict:
    sales = con.execute(
        "SELECT COUNT(*), COALESCE(SUM(qty),0), COALESCE(SUM(net_amount),0),"
        " COUNT(DISTINCT so_id) FROM fact_sales").fetchone()
    orders = sales[3]
    aov = round(sales[2] / orders, 2) if orders else None
    if _has_col(con, "fact_deliveries", "status"):
        otd = con.execute(
            "SELECT AVG(CAST(on_time AS FLOAT)), COUNT(*) FROM fact_deliveries"
            " WHERE status != 'Shipping canceled'").fetchone()
        late = con.execute(
            "SELECT COUNT(*) FROM fact_deliveries WHERE status = 'Late delivery'").fetchone()[0]
        delivered = otd[1] or 0
        cancel = con.execute(
            "SELECT COUNT(*) FROM fact_deliveries WHERE status = 'Shipping canceled'").fetchone()[0]
    else:  # legacy synthetic fixture warehouse (no DataCo status column)
        otd = con.execute("SELECT AVG(CAST(on_time AS FLOAT)), COUNT(*) FROM fact_deliveries").fetchone()
        late = con.execute("SELECT COUNT(*) FROM fact_deliveries WHERE on_time=0").fetchone()[0]
        delivered = otd[1] or 0
        cancel = 0
    quar = con.execute("SELECT COUNT(*) FROM dq_quarantine").fetchone()
    period = con.execute("SELECT MIN(date_key), MAX(date_key) FROM fact_sales").fetchone()
    try:
        from forecasting.forecast import ANALYSIS_END
        dataco = _has_table(con, "stg_dataco") and _has_col(con, "fact_deliveries", "status")
        snapshot = ANALYSIS_END[:10] if dataco else period[1]
    except Exception:  # noqa: BLE001
        snapshot = period[1]
    meta = None
    if _has_table(con, "dataco_source_meta"):
        try:
            meta = con.execute(
                "SELECT source_name, source_url, dataset_start, dataset_end, rows,"
                " last_processed, last_run_id, last_status FROM dataco_source_meta WHERE id=1").fetchone()
        except Exception:  # noqa: BLE001 - pre-DataCo DBs
            meta = None
    last_run = con.execute("SELECT started_at, status FROM etl_execution_log "
                           "ORDER BY started_at DESC LIMIT 1").fetchone()
    return {
        "sales_lines": sales[0], "units_sold": sales[1],
        "revenue": round(sales[2], 2), "orders": orders,
        "avg_order_value": aov,
        "delivery_otd": round(otd[0], 3) if otd[0] is not None else None,
        "late_deliveries": late,
        "late_rate": round(late / delivered, 4) if delivered else None,
        "canceled_shipments": cancel,
        "quarantined_rows": quar[0],
        "procurement_otif": None,
        "inventory_value": None,
        "unavailable": ["inventory", "suppliers", "purchase_orders"],
        "period": {"start": period[0], "end": period[1], "snapshot": snapshot,
                   "last_etl_at": last_run[0] if last_run else None,
                   "last_etl_status": last_run[1] if last_run else None},
        "source": {"name": meta[0] if meta else "DataCo Smart Supply Chain",
                   "url": meta[1] if meta else "https://data.mendeley.com/datasets/8gx2fvg2k6/5",
                   "dataset_start": meta[2] if meta else period[0],
                   "dataset_end": meta[3] if meta else period[1],
                   "rows": meta[4] if meta else sales[0],
                   "last_processed": meta[5] if meta else None,
                   "status": meta[6] if meta else None},
    }
