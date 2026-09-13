"""ETL: Raw CSVs → dims (SCD) → facts (idempotent) → DQ score → audit log.

Usage: python -m etl.load --src data/generated/seed-42 --db data/warehouse.db --batch B1
Idempotent: rerun same batch inserts zero new fact rows (INSERT OR IGNORE on business keys).
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from warehouse.db import connect, init_schema

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

SOURCES = ["products", "suppliers", "warehouses", "customers", "carriers",
           "purchase_orders", "po_lines", "sales_orders", "so_lines",
           "inventory_snapshots", "movements", "shipments", "deliveries", "returns"]


def read_csv(src: Path, name: str) -> list[dict]:
    p = src / f"{name}.csv"
    if not p.exists():
        return []
    with p.open() as f:
        return list(csv.DictReader(f))


def ensure_date(con: sqlite3.Connection, d: str) -> None:
    if not d:
        d = "1900-01-01"
    try:
        dt = datetime.fromisoformat(d)
    except ValueError:
        d, dt = "1900-01-01", datetime(1900, 1, 1)
    con.execute("INSERT OR IGNORE INTO dim_date VALUES (?,?,?,?,?,?,?,?)",
                (d, d, dt.year, dt.month, dt.day, dt.isocalendar()[1], dt.weekday(),
                 dt.strftime("%B")))


def quarantine(con, run_id, source, key, rule_id, reason, payload) -> None:
    con.execute("INSERT INTO dq_quarantine (run_id, source, business_key, rule_id, reason, payload, created_at)"
                " VALUES (?,?,?,?,?,?,?)",
                (run_id, source, key, rule_id, reason, json.dumps(payload)[:2000],
                 _now()))


def load_batch(src: Path, db: Path, batch: str) -> dict:
    t0 = time.time()
    con = connect(db)
    init_schema(con)
    run_id = f"{batch}-{uuid.uuid4().hex[:8]}"
    now = _now()
    stats: dict[str, dict] = {}

    def log_source(source, read, acc, rej, errs):
        stats[source] = {"read": read, "accepted": acc, "rejected": rej}
        con.execute("INSERT INTO etl_execution_log VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (f"{run_id}-{source}", now, _now(), source,
                     read, acc, rej, json.dumps(errs)[:2000],
                     "partial" if rej and acc else ("failed" if not acc and read else "succeeded"),
                     round(time.time() - t0, 2)))

    # ---- dims SCD1 ----
    for name, table, idcol in [("warehouses", "dim_warehouse", "warehouse_id"),
                               ("customers", "dim_customer", "customer_id"),
                               ("carriers", "dim_carrier", "carrier_id")]:
        rows = read_csv(src, name)
        acc = rej = 0
        errs: list[str] = []
        for r in rows:
            if not r.get(idcol):
                quarantine(con, run_id, name, "?", "R01", f"{idcol} null", r)
                rej += 1
                continue
            cols = {"warehouses": ("warehouse_id", "name", "region"),
                    "customers": ("customer_id", "name", "region"),
                    "carriers": ("carrier_id", "name")}[name]
            try:
                if name == "carriers":
                    con.execute("INSERT OR IGNORE INTO dim_carrier (carrier_id, name) VALUES (?,?)",
                                (r["carrier_id"], r["name"]))
                elif name == "warehouses":
                    con.execute("INSERT OR IGNORE INTO dim_warehouse (warehouse_id, name, region) VALUES (?,?,?)",
                                (r["warehouse_id"], r["name"], r["region"]))
                else:
                    con.execute("INSERT OR IGNORE INTO dim_customer (customer_id, name, region) VALUES (?,?,?)",
                                (r["customer_id"], r["name"], r["region"]))
                acc += 1
            except Exception as e:  # noqa: BLE001
                quarantine(con, run_id, name, r.get(idcol, "?"), "R00", str(e), r)
                rej += 1
        log_source(name, len(rows), acc, rej, errs)

    # ---- dims SCD2 (product, supplier): new version on material change ----
    for name in ["products", "suppliers"]:
        rows = read_csv(src, name)
        acc = rej = 0
        for r in rows:
            idcol = "product_id" if name == "products" else "supplier_id"
            if not r.get(idcol):
                quarantine(con, run_id, name, "?", "R01", f"{idcol} null", r)
                rej += 1
                continue
            if name == "products":
                cur = con.execute("SELECT product_sk, category, standard_cost FROM dim_product WHERE product_id=? AND is_current=1",
                                  (r["product_id"],)).fetchone()
                try:
                    cost = float(r["standard_cost"])
                except ValueError:
                    quarantine(con, run_id, name, r[idcol], "R02", "bad cost", r)
                    rej += 1
                    continue
                if cur is None:
                    con.execute("INSERT INTO dim_product (product_id, sku, name, category, standard_cost, valid_from, is_current)"
                                " VALUES (?,?,?,?,?,?,1)", (r["product_id"], r["sku"], r["name"], r["category"], cost, now))
                    acc += 1
                elif abs(cur[2] - cost) > 1e-9 or True and cur[1] != r["category"]:
                    if abs(cur[2] - cost) < 1e-9 and cur[1] == r["category"]:
                        acc += 1
                        continue
                    con.execute("UPDATE dim_product SET valid_to=?, is_current=0 WHERE product_sk=?", (now, cur[0]))
                    con.execute("INSERT INTO dim_product (product_id, sku, name, category, standard_cost, valid_from, is_current)"
                                " VALUES (?,?,?,?,?,?,1)", (r["product_id"], r["sku"], r["name"], r["category"], cost, now))
                    acc += 1
                else:
                    acc += 1
            else:
                cur = con.execute("SELECT supplier_sk, rating_tier FROM dim_supplier WHERE supplier_id=? AND is_current=1",
                                  (r["supplier_id"],)).fetchone()
                if cur is None:
                    con.execute("INSERT INTO dim_supplier (supplier_id, name, rating_tier, valid_from, is_current)"
                                " VALUES (?,?,?, ?,1)", (r["supplier_id"], r["name"], r["rating_tier"], now))
                    acc += 1
                elif cur[1] != r["rating_tier"]:
                    con.execute("UPDATE dim_supplier SET valid_to=?, is_current=0 WHERE supplier_sk=?", (now, cur[0]))
                    con.execute("INSERT INTO dim_supplier (supplier_id, name, rating_tier, valid_from, is_current)"
                                " VALUES (?,?,?, ?,1)", (r["supplier_id"], r["name"], r["rating_tier"], now))
                    acc += 1
                else:
                    acc += 1
        log_source(name, len(rows), acc, rej, [])

    # lookup maps (current SKs)
    pmap = {r[0]: r[1] for r in con.execute("SELECT product_id, product_sk FROM dim_product WHERE is_current=1")}
    smap = {r[0]: r[1] for r in con.execute("SELECT supplier_id, supplier_sk FROM dim_supplier WHERE is_current=1")}
    wmap = {r[0]: r[1] for r in con.execute("SELECT warehouse_id, warehouse_sk FROM dim_warehouse")}
    cmap = {r[0]: r[1] for r in con.execute("SELECT customer_id, customer_sk FROM dim_customer")}
    crmap = {r[0]: r[1] for r in con.execute("SELECT carrier_id, carrier_sk FROM dim_carrier")}
    pcost = {r[0]: r[1] for r in con.execute("SELECT product_id, standard_cost FROM dim_product WHERE is_current=1")}

    def sk(m, k):
        return m.get(k, 0)

    # ---- facts ----
    # sales
    so_date = {r["so_id"]: r["order_date"] for r in read_csv(src, "sales_orders")}
    sol = read_csv(src, "so_lines")
    acc = rej = 0
    for r in sol:
        try:
            q = int(r["qty"])
            if q < 0:
                raise ValueError("qty negative")
        except ValueError:
            quarantine(con, run_id, "so_lines", r.get("so_id", "?"), "R02", "qty negative/invalid", r)
            rej += 1
            continue
        if r["product_id"] not in pmap or r["warehouse_id"] not in wmap:
            quarantine(con, run_id, "so_lines", r["so_id"], "R05", "unknown product/warehouse", r)
            rej += 1
            continue
        d = so_date.get(r["so_id"], "1900-01-01")
        ensure_date(con, d)
        price = float(r["unit_price"])
        con.execute("INSERT OR IGNORE INTO fact_sales (so_id, line_no, product_sk, warehouse_sk, customer_sk, date_key, qty, unit_price, net_amount)"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (r["so_id"], int(r["line_no"]), sk(pmap, r["product_id"]), sk(wmap, r["warehouse_id"]),
                     0, d, q, price, round(q * price, 2)))
        acc += 1 if con.total_changes else acc
        acc += 0 if False else 0
        # count accepted as processed (IGNORE keeps idempotency; accepted = not quarantined)
        acc = acc  # placeholder keeps logic explicit
    # accepted = processed minus quarantined for idempotent simplicity
    acc = len(sol) - rej
    log_source("so_lines", len(sol), acc, rej, [])

    # purchases
    po = {r["po_id"]: r for r in read_csv(src, "purchase_orders")}
    pol = read_csv(src, "po_lines")
    rej = 0
    for r in pol:
        parent = po.get(r["po_id"])
        if parent is None or parent["supplier_id"] not in smap:
            quarantine(con, run_id, "po_lines", r["po_id"], "R04", "unknown PO/supplier", r)
            rej += 1
            continue
        if int(r["ordered_qty"]) < 0 or int(r["received_qty"]) < 0:
            quarantine(con, run_id, "po_lines", r["po_id"], "R02", "qty negative", r)
            rej += 1
            continue
        ensure_date(con, parent["order_date"])
        ensure_date(con, r["receipt_date"])
        late = (datetime.fromisoformat(r["receipt_date"]) - datetime.fromisoformat(parent["promised_date"])).days
        con.execute("INSERT OR IGNORE INTO fact_purchases VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)",
                    (r["po_id"], int(r["line_no"]), sk(smap, parent["supplier_id"]),
                     sk(wmap, parent["warehouse_id"]), sk(pmap, r["product_id"]),
                     parent["order_date"], r["receipt_date"], int(r["ordered_qty"]),
                     int(r["received_qty"]), float(r["unit_cost"]), max(late, -99)))
    log_source("po_lines", len(pol), len(pol) - rej, rej, [])

    # snapshots
    snaps = read_csv(src, "inventory_snapshots")
    rej = 0
    for r in snaps:
        if r["product_id"] not in pmap or r["warehouse_id"] not in wmap:
            quarantine(con, run_id, "snapshots", r["snapshot_date"], "R05", "unknown prod/wh", r)
            rej += 1
            continue
        ensure_date(con, r["snapshot_date"])
        oh, res = int(r["on_hand"]), int(r["reserved"])
        con.execute("INSERT OR IGNORE INTO fact_inventory_snapshot VALUES (NULL,?,?,?,?,?,?,?)",
                    (r["snapshot_date"], sk(pmap, r["product_id"]), sk(wmap, r["warehouse_id"]),
                     oh, res, oh - res, pcost.get(r["product_id"], 0)))
    log_source("inventory_snapshots", len(snaps), len(snaps) - rej, rej, [])

    # movements
    movs = read_csv(src, "movements")
    rej = 0
    for r in movs:
        if r["product_id"] not in pmap or r["warehouse_id"] not in wmap:
            quarantine(con, run_id, "movements", r["movement_id"], "R05", "unknown prod/wh", r)
            rej += 1
            continue
        ensure_date(con, r["event_date"])
        con.execute("INSERT OR IGNORE INTO fact_inventory_movement VALUES (NULL,?,?,?,?,?,?)",
                    (r["movement_id"], r["event_date"], sk(pmap, r["product_id"]),
                     sk(wmap, r["warehouse_id"]), int(r["qty_delta"]), r["reason"]))
    log_source("movements", len(movs), len(movs) - rej, rej, [])

    # shipments + deliveries (R03: delivery >= shipment)
    ships = read_csv(src, "shipments")
    rej = 0
    ship_date = {}
    for r in ships:
        ensure_date(con, r["shipment_date"])
        ship_date[r["shipment_id"]] = r["shipment_date"]
        con.execute("INSERT OR IGNORE INTO fact_shipments VALUES (NULL,?,?,?,?,?,?)",
                    (r["shipment_id"], r["so_id"], sk(crmap, r["carrier_id"]),
                     r["shipment_date"], int(r["shipped_qty"]), float(r["freight_cost"])))
    log_source("shipments", len(ships), len(ships) - rej, rej, [])
    dels = read_csv(src, "deliveries")
    rej = 0
    for r in dels:
        sd = ship_date.get(r["shipment_id"])
        if sd and r["delivery_date"] < sd:
            quarantine(con, run_id, "deliveries", r["shipment_id"], "R03", "delivery before shipment", r)
            rej += 1
            continue
        ensure_date(con, r["promised_date"])
        ensure_date(con, r["delivery_date"])
        delay = (datetime.fromisoformat(r["delivery_date"]) - datetime.fromisoformat(r["promised_date"])).days
        con.execute("INSERT OR IGNORE INTO fact_deliveries VALUES (NULL,?,?,?,?,?,?)",
                    (r["shipment_id"], r["promised_date"], r["delivery_date"],
                     int(r["delivered_qty"]), 1 if delay <= 0 else 0, delay))
    log_source("deliveries", len(dels), len(dels) - rej, rej, [])

    # returns (R07 dup handled by UNIQUE)
    rets = read_csv(src, "returns")
    rej = 0
    for r in rets:
        con.execute("INSERT OR IGNORE INTO fact_returns VALUES (NULL,?,?,?,?,?)",
                    (r["return_id"], r["so_id"], sk(pmap, r["product_id"]), int(r["qty"]), r["reason"]))
    log_source("returns", len(rets), len(rets) - rej, rej, [])

    # DQ scores + watermarks
    for s, v in stats.items():
        score = (v["accepted"] / v["read"]) if v["read"] else 1.0
        con.execute("INSERT OR REPLACE INTO dq_batch_score VALUES (?,?,?,?,?)",
                    (run_id, s, v["read"], v["accepted"], round(score, 4)))
        con.execute("INSERT OR REPLACE INTO etl_watermark VALUES (?,?,?)", (s, batch, now))
    con.commit()
    q = con.execute("SELECT COUNT(*) FROM dq_quarantine WHERE run_id=?", (run_id,)).fetchone()[0]
    con.close()
    return {"run_id": run_id, "quarantined": q, "stats": stats,
            "duration_s": round(time.time() - t0, 2)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--db", default="data/warehouse.db")
    ap.add_argument("--batch", default="B1")
    a = ap.parse_args()
    out = load_batch(Path(a.src), Path(a.db), a.batch)
    print(json.dumps({"run_id": out["run_id"], "quarantined": out["quarantined"],
                      "duration_s": out["duration_s"]}, indent=2))


if __name__ == "__main__":
    main()
