"""KPI queries (SQL gold logic). DAX in powerbi/measures.dax mirrors these definitions."""

from __future__ import annotations

import sqlite3


def inventory_value(con: sqlite3.Connection) -> float:
    return con.execute(
        "SELECT COALESCE(SUM(s.available * s.unit_cost),0) FROM fact_inventory_snapshot s "
        "WHERE s.snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)"
    ).fetchone()[0]


def coverage_days(con: sqlite3.Connection, product_sk: int, warehouse_sk: int) -> float | None:
    oh = con.execute(
        "SELECT available FROM fact_inventory_snapshot WHERE product_sk=? AND warehouse_sk=? "
        "ORDER BY snapshot_date_key DESC LIMIT 1", (product_sk, warehouse_sk)).fetchone()
    if not oh:
        return None
    avgd = con.execute(
        "SELECT AVG(qty) FROM fact_sales WHERE product_sk=? AND warehouse_sk=? "
        "AND date_key >= (SELECT date(MAX(date_key), '-30 days') FROM fact_sales)",
        (product_sk, warehouse_sk)).fetchone()[0]
    if not avgd:
        return None
    return oh[0] / avgd


def supplier_otif(con: sqlite3.Connection, supplier_sk: int) -> float | None:
    r = con.execute(
        "SELECT COUNT(*), SUM(CASE WHEN late_days<=0 THEN 1 ELSE 0 END) FROM fact_purchases WHERE supplier_sk=?",
        (supplier_sk,)).fetchone()
    return (r[1] / r[0]) if r[0] else None


def on_time_delivery(con: sqlite3.Connection) -> float | None:
    r = con.execute("SELECT COUNT(*), SUM(on_time) FROM fact_deliveries").fetchone()
    return (r[1] / r[0]) if r[0] else None


def dead_stock_value(con: sqlite3.Connection, cutoff_date: str) -> float:
    return con.execute(
        """SELECT COALESCE(SUM(s.available * s.unit_cost),0) FROM fact_inventory_snapshot s
        WHERE s.snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)
        AND NOT EXISTS (SELECT 1 FROM fact_sales f WHERE f.product_sk=s.product_sk AND f.date_key >= date(?, '-90 days'))""",
        (cutoff_date,)).fetchone()[0]


def wape(actual: list[float], forecast: list[float]) -> float | None:
    denom = sum(abs(a) for a in actual)
    if not denom:
        return None
    return sum(abs(a - f) for a, f in zip(actual, forecast)) / denom
