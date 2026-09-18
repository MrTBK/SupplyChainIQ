"""ETL: DataCo CSV -> stg_dataco -> dims/facts (idempotent, audited).

Usage: python -m etl.load_dataco --db data/warehouse.db --batch DATACO1
Idempotent: PRIMARY KEY (order_id, order_item_id) on stg + UNIQUE (so_id,line_no)
on fact_sales and shipment/delivery business keys -> rerun = zero delta.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ingestion.dataco_adapter import iter_staged, validate_file
from warehouse.db import connect, init_schema

SQL_DIR = Path(__file__).resolve().parents[1] / "warehouse" / "sql"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_date(con: sqlite3.Connection, d: str) -> None:
    dt = datetime.fromisoformat(d)
    con.execute("INSERT OR IGNORE INTO dim_date VALUES (?,?,?,?,?,?,?,?)",
                (d, d, dt.year, dt.month, dt.day, dt.isocalendar()[1],
                 dt.weekday(), dt.strftime("%B")))


def _sk(con: sqlite3.Connection, table: str, idcol: str, ident: str) -> int:
    row = con.execute(f"SELECT rowid FROM {table} WHERE {idcol}=?", (ident,)).fetchone()
    # dim tables use INTEGER PRIMARY KEY surrogate; rowid works for all of them
    return row[0] if row else 0


def load(db: Path, batch: str) -> dict:
    t0 = time.time()
    v = validate_file()
    if not v["ok"]:
        raise SystemExit(v["error"])
    con = connect(db)
    con.row_factory = sqlite3.Row
    init_schema(con)
    con.executescript((SQL_DIR / "011_dataco.sql").read_text())
    # DataCo truth column: delivery status on fact_deliveries (OTD excludes canceled)
    cols = [r[1] for r in con.execute("PRAGMA table_info(fact_deliveries)").fetchall()]
    if "status" not in cols:
        con.execute("ALTER TABLE fact_deliveries ADD COLUMN status TEXT NOT NULL DEFAULT ''")
    scol = [r[1] for r in con.execute("PRAGMA table_info(fact_shipments)").fetchall()]
    if "mode" not in scol:
        con.execute("ALTER TABLE fact_shipments ADD COLUMN mode TEXT NOT NULL DEFAULT ''")
    run_id = f"{batch}-{uuid.uuid4().hex[:8]}"
    started = _now()
    read = acc = rej = 0
    min_d = "9999-99-99"
    max_d = "0000-00-00"
    for row, bad in iter_staged():
        read += 1
        if bad:
            rule, reason, key = bad
            con.execute(
                "INSERT INTO dq_quarantine (run_id, source, business_key, rule_id, reason, payload, created_at)"
                " VALUES (?,?,?,?,?,?,?)",
                (run_id, "dataco", "|".join(key), rule, reason,
                 json.dumps({"key": key})[:2000], _now()))
            rej += 1
            continue
        assert row is not None
        min_d = min(min_d, row["order_date"])
        max_d = max(max_d, row["order_date"])
        con.execute(
            """INSERT OR IGNORE INTO stg_dataco VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (row["order_id"], row["order_item_id"], row["line_no"], row["qty"],
             row["unit_price"], row["net_amount"], row["discount"], row["discount_rate"],
             row["benefit"], row["order_date"], row["ship_date"], row["real_days"],
             row["sched_days"], row["delay_days"], row["on_time"], row["delivery_status"],
             row["order_status"], row["product_id"], row["product_name"],
             row["category_id"], row["category_name"], row["customer_id"],
             row["customer_name"], row["customer_segment"], row["order_region"],
             row["market"], row["order_country"], row["order_state"], row["order_city"],
             row["department_id"], row["department_name"], row["shipping_mode"],
             row["payment_type"]))
        acc += 1
        if acc % 20000 == 0:
            con.commit()
    con.commit()

    # ---- dims ----
    _ensure_date(con, "1900-01-01")
    for (d,) in con.execute("SELECT DISTINCT order_date FROM stg_dataco"):
        _ensure_date(con, d)
    for (d,) in con.execute("SELECT DISTINCT ship_date FROM stg_dataco"):
        _ensure_date(con, d)
    for pid, pname, cid, cname in con.execute(
            "SELECT DISTINCT product_id, product_name, category_id, category_name FROM stg_dataco"):
        con.execute("INSERT OR IGNORE INTO dim_product "
                    "(product_id, sku, name, category, standard_cost, valid_from, is_current)"
                    " VALUES (?,?,?,?,?,?,1)",
                    (pid, pid, pname or pid, cname or "Unknown", 0.0, min_d))
        con.execute("INSERT OR IGNORE INTO dim_category (category_id, name) VALUES (?,?)",
                    (cid or cname, cname or cid))
    for cid, cname, seg in con.execute(
            "SELECT DISTINCT customer_id, customer_name, customer_segment FROM stg_dataco"):
        con.execute("INSERT OR IGNORE INTO dim_customer (customer_id, name, region) VALUES (?,?,?)",
                    (cid, cname or cid, seg or ""))
    for region, market in con.execute("SELECT DISTINCT order_region, market FROM stg_dataco"):
        if region:
            con.execute("INSERT OR IGNORE INTO dim_region (region, market) VALUES (?,?)",
                        (region, market or ""))
        if market:
            con.execute("INSERT OR IGNORE INTO dim_market (market) VALUES (?)", (market,))
    for did, dname in con.execute("SELECT DISTINCT department_id, department_name FROM stg_dataco"):
        if did or dname:
            con.execute("INSERT OR IGNORE INTO dim_department (dept_id, name) VALUES (?,?)",
                        (did or dname, dname or did))
    for (mode,) in con.execute("SELECT DISTINCT shipping_mode FROM stg_dataco"):
        if mode:
            con.execute("INSERT OR IGNORE INTO dim_shipping_mode (mode) VALUES (?)", (mode,))
    # unknown members for new dims
    con.execute("INSERT OR IGNORE INTO dim_shipping_mode (mode_sk, mode) VALUES (0,'UNKNOWN')")
    con.execute("INSERT OR IGNORE INTO dim_category (category_sk, category_id, name) VALUES (0,'UNKNOWN','Unknown')")
    con.execute("INSERT OR IGNORE INTO dim_region (region_sk, region, market) VALUES (0,'UNKNOWN','')")
    con.execute("INSERT OR IGNORE INTO dim_market (market_sk, market) VALUES (0,'UNKNOWN')")
    con.execute("INSERT OR IGNORE INTO dim_department (dept_sk, dept_id, name) VALUES (0,'UNKNOWN','Unknown')")

    # ---- facts (idempotent) ----
    for r in con.execute("SELECT * FROM stg_dataco"):
        d = dict(r)
        prow = con.execute("SELECT product_sk FROM dim_product WHERE product_id=? AND is_current=1",
                           (d["product_id"],)).fetchone()
        crow = con.execute("SELECT customer_sk FROM dim_customer WHERE customer_id=?",
                           (d["customer_id"],)).fetchone()
        ps, cs = (prow[0] if prow else 0), (crow[0] if crow else 0)
        con.execute(
            "INSERT OR IGNORE INTO fact_sales (so_id, line_no, product_sk, warehouse_sk, customer_sk,"
            " date_key, qty, unit_price, net_amount) VALUES (?,?,?,?,?,?,?,?,?)",
            (d["order_id"], d["line_no"], ps, 0, cs, d["order_date"], d["qty"],
             d["unit_price"], d["net_amount"]))
        ship_id = f"{d['order_id']}-{d['order_item_id']}"
        con.execute(
            "INSERT OR IGNORE INTO fact_shipments (shipment_id, so_id, carrier_sk,"
            " shipment_date_key, shipped_qty, freight_cost, mode) VALUES (?,?,?,?,?,?,?)",
            (ship_id, d["order_id"], 0, d["ship_date"], d["qty"], 0.0, d["shipping_mode"]))
        # Scheduled delivery = order_date + sched_days (verified: ship_date ==
        # order_date + real_days on raw rows, so delivery - promised == delay).
        promised = con.execute("SELECT date(?, '+' || ? || ' days')",
                               (d["order_date"], d["sched_days"])).fetchone()[0]
        _ensure_date(con, promised)
        con.execute(
            "INSERT OR REPLACE INTO fact_deliveries (shipment_id, promised_date_key,"
            " delivery_date_key, delivered_qty, on_time, delay_days, status) VALUES (?,?,?,?,?,?,?)",
            (ship_id, promised, d["ship_date"], d["qty"], d["on_time"], d["delay_days"],
             d["delivery_status"]))
    con.commit()

    dur = round(time.time() - t0, 2)
    status = "succeeded" if acc else "failed"
    con.execute("INSERT INTO etl_execution_log VALUES (?,?,?,?,?,?,?,?,?,?)",
                (f"{run_id}-dataco", started, _now(), "dataco", read, acc, rej,
                 json.dumps([{"dataset": f"{min_d}..{max_d}"}])[:2000], status, dur))
    score = round(acc / read, 4) if read else 0.0
    con.execute("INSERT OR REPLACE INTO dq_batch_score VALUES (?,?,?,?,?)",
                (run_id, "dataco", read, acc, score))
    con.execute("UPDATE dataco_source_meta SET rows=?, last_processed=?, last_run_id=?, last_status=?"
                " WHERE id=1", (acc, _now(), run_id, status))
    con.commit()
    out = {"run_id": run_id, "read": read, "accepted": acc, "rejected": rej,
           "score": score, "period": f"{min_d}..{max_d}", "seconds": dur, "status": status}
    con.close()
    print(json.dumps(out, indent=2))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/warehouse.db")
    ap.add_argument("--batch", default="DATACO1")
    args = ap.parse_args()
    load(Path(args.db), args.batch)


if __name__ == "__main__":
    main()
