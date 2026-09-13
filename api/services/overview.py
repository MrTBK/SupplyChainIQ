"""Executive overview service: current state of the supply chain (reuses kpis.py gold logic)."""

from __future__ import annotations

import sqlite3


def overview(con: sqlite3.Connection) -> dict:
    sales = con.execute("SELECT COUNT(*), COALESCE(SUM(qty),0), COALESCE(SUM(net_amount),0) FROM fact_sales").fetchone()
    inv = con.execute("SELECT COALESCE(SUM(available*unit_cost),0) FROM fact_inventory_snapshot "
                      "WHERE snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)").fetchone()
    otif = con.execute("SELECT AVG(CASE WHEN late_days<=0 THEN 1.0 ELSE 0 END) FROM fact_purchases").fetchone()
    otd = con.execute("SELECT AVG(CAST(on_time AS FLOAT)) FROM fact_deliveries").fetchone()
    quar = con.execute("SELECT COUNT(*) FROM dq_quarantine").fetchone()
    return {"sales_lines": sales[0], "units_sold": sales[1], "revenue": round(sales[2], 2),
            "inventory_value": round(inv[0], 2),
            "procurement_otif": round(otif[0], 3) if otif[0] is not None else None,
            "delivery_otd": round(otd[0], 3) if otd[0] is not None else None,
            "quarantined_rows": quar[0]}
