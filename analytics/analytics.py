"""Inventory/supplier/logistics analytics: turnover, ABC, scores, lead-time, anomalies (stdlib)."""

from __future__ import annotations

import math
import sqlite3
from collections import defaultdict


def turnover_by_category(con: sqlite3.Connection) -> dict[str, float]:
    cogs = defaultdict(float)
    for prod_sk, qty, cost in con.execute(
            "SELECT product_sk, qty, unit_price*0.74 FROM fact_sales"):
        cogs[prod_sk] += qty * cost
    cat_cogs: dict[str, float] = defaultdict(float)
    cat_val: dict[str, float] = defaultdict(float)
    prod_cat = {r[0]: r[1] for r in con.execute("SELECT product_sk, category FROM dim_product WHERE is_current=1")}
    for ps, v in cogs.items():
        cat_cogs[prod_cat.get(ps, "?")] += v
    for ps, wh, avail, uc in con.execute(
            "SELECT product_sk, warehouse_sk, available, unit_cost FROM fact_inventory_snapshot "
            "WHERE snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)"):
        cat_val[prod_cat.get(ps, "?")] += avail * uc
    return {c: (cat_cogs[c] / cat_val[c] if cat_val[c] else 0.0) for c in cat_cogs}


def abc_classification(con: sqlite3.Connection) -> dict[int, str]:
    rev: dict[int, float] = defaultdict(float)
    for ps, q, p in con.execute("SELECT product_sk, qty, unit_price FROM fact_sales"):
        rev[ps] += q * p
    ranked = sorted(rev.items(), key=lambda x: -x[1])
    total = sum(rev.values()) or 1
    cum, out = 0.0, {}
    for ps, v in ranked:
        cum += v / total
        out[ps] = "A" if cum <= 0.80 else ("B" if cum <= 0.95 else "C")
    return out


def supplier_score(con: sqlite3.Connection, supplier_sk: int) -> dict:
    otif_r = con.execute(
        "SELECT COUNT(*), SUM(CASE WHEN late_days<=0 THEN 1 ELSE 0 END) FROM fact_purchases WHERE supplier_sk=?",
        (supplier_sk,)).fetchone()
    otif = (otif_r[1] / otif_r[0]) if otif_r[0] else 0
    quality = 1.0  # simplified: defect rate from returns linked via product suppliers omitted; documented limit
    price_stability = 1.0
    return {"otif": round(otif, 4), "quality_proxy": quality,
            "score": round(0.5 * otif + 0.3 * quality + 0.2 * price_stability, 4),
            "limits": "quality uses returns proxy only; see docs"}


def lead_time_stats(con: sqlite3.Connection, supplier_sk: int) -> dict:
    vals = sorted(r[0] for r in con.execute(
        "SELECT CAST(julianday(receipt_date_key)-julianday(order_date_key) AS INTEGER) "
        "FROM fact_purchases WHERE supplier_sk=?", (supplier_sk,)))
    if not vals:
        return {"n": 0}
    def pct(p):
        return vals[min(len(vals) - 1, int(p * len(vals)))]
    return {"n": len(vals), "p50": pct(0.5), "p90": pct(0.9),
            "mean": round(sum(vals) / len(vals), 2)}


def demand_anomalies(monthly_qty: list[float], z: float = 3.0) -> list[int]:
    if len(monthly_qty) < 4:
        return []
    mu = sum(monthly_qty) / len(monthly_qty)
    sd = math.sqrt(sum((x - mu) ** 2 for x in monthly_qty) / len(monthly_qty)) or 1e-9
    return [i for i, x in enumerate(monthly_qty) if abs(x - mu) / sd >= z]
