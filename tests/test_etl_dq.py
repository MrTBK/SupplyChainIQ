"""ETL + DQ + warehouse gates: idempotency, quarantine, grain, unknowns."""

import csv
import sqlite3
from pathlib import Path

from etl.load import load_batch


def _mini_src(tmp: Path) -> Path:
    src = tmp / "src"
    src.mkdir()
    def w(name, fields, rows):
        with (src / f"{name}.csv").open("w", newline="") as f:
            d = csv.DictWriter(f, fieldnames=fields)
            d.writeheader()
            d.writerows(rows)
    w("products", ["product_id", "sku", "name", "category", "standard_cost", "is_synthetic"],
      [{"product_id": "P0001", "sku": "SKU-1", "name": "A", "category": "Snacks", "standard_cost": "10", "is_synthetic": "true"}])
    w("suppliers", ["supplier_id", "name", "rating_tier", "is_synthetic"],
      [{"supplier_id": "S001", "name": "S", "rating_tier": "A", "is_synthetic": "true"}])
    w("warehouses", ["warehouse_id", "name", "region"],
      [{"warehouse_id": "W1", "name": "WH-N", "region": "North"}])
    w("customers", ["customer_id", "name", "region"],
      [{"customer_id": "C1", "name": "C", "region": "North"}])
    w("carriers", ["carrier_id", "name"], [{"carrier_id": "CR1", "name": "Car"}])
    w("purchase_orders", ["po_id", "supplier_id", "warehouse_id", "order_date", "promised_date"],
      [{"po_id": "PO1", "supplier_id": "S001", "warehouse_id": "W1", "order_date": "2024-01-01", "promised_date": "2024-01-10"}])
    w("po_lines", ["po_id", "line_no", "product_id", "ordered_qty", "received_qty", "unit_cost", "receipt_date"],
      [{"po_id": "PO1", "line_no": 1, "product_id": "P0001", "ordered_qty": 100, "received_qty": 100,
        "unit_cost": 9, "receipt_date": "2024-01-11"}])
    w("sales_orders", ["so_id", "customer_id", "order_date"],
      [{"so_id": "SO1", "customer_id": "C1", "order_date": "2024-02-01"},
       {"so_id": "SO2", "customer_id": "C1", "order_date": "2024-02-02"}])
    w("so_lines", ["so_id", "line_no", "product_id", "warehouse_id", "qty", "unit_price"],
      [{"so_id": "SO1", "line_no": 1, "product_id": "P0001", "warehouse_id": "W1", "qty": 5, "unit_price": 12},
       {"so_id": "SO2", "line_no": 1, "product_id": "P0001", "warehouse_id": "W1", "qty": -3, "unit_price": 12},  # R02 bad
       {"so_id": "SO2", "line_no": 2, "product_id": "NOPE", "warehouse_id": "W1", "qty": 2, "unit_price": 12}])  # R05 bad
    w("inventory_snapshots", ["snapshot_date", "product_id", "warehouse_id", "on_hand", "reserved"],
      [{"snapshot_date": "2024-02-01", "product_id": "P0001", "warehouse_id": "W1", "on_hand": 100, "reserved": 5}])
    w("movements", ["movement_id", "event_date", "product_id", "warehouse_id", "qty_delta", "reason"],
      [{"movement_id": "M1", "event_date": "2024-02-01", "product_id": "P0001", "warehouse_id": "W1", "qty_delta": -5, "reason": "SALE"}])
    w("shipments", ["shipment_id", "so_id", "line_no", "carrier_id", "shipment_date", "shipped_qty", "freight_cost"],
      [{"shipment_id": "SH1", "so_id": "SO1", "line_no": 1, "carrier_id": "CR1", "shipment_date": "2024-02-03",
        "shipped_qty": 5, "freight_cost": 10}])
    w("deliveries", ["shipment_id", "promised_date", "delivery_date", "delivered_qty"],
      [{"shipment_id": "SH1", "promised_date": "2024-02-05", "delivery_date": "2024-02-06", "delivered_qty": 5},
       {"shipment_id": "SHX", "promised_date": "2024-02-05", "delivery_date": "2024-02-01", "delivered_qty": 1}])  # R03 bad (no ship date? has none -> accepted? make SH1 dup bad)
    w("returns", ["return_id", "so_id", "line_no", "product_id", "qty", "reason"],
      [{"return_id": "R1", "so_id": "SO1", "line_no": 1, "product_id": "P0001", "qty": 1, "reason": "QUALITY"}])
    return src


def test_quarantine_catches_r02_r05(tmp_path):
    src = _mini_src(tmp_path)
    db = tmp_path / "wh.db"
    out = load_batch(src, db, "T1")
    con = sqlite3.connect(db)
    rules = {r[0] for r in con.execute("SELECT DISTINCT rule_id FROM dq_quarantine")}
    assert "R02" in rules and "R05" in rules
    assert con.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0] == 1
    # grain: one row per so line business key
    assert con.execute("SELECT COUNT(*) FROM (SELECT so_id, line_no, COUNT(*) c FROM fact_sales GROUP BY 1,2 HAVING c>1)").fetchone()[0] == 0


def test_idempotent_rerun_zero_delta(tmp_path):
    src = _mini_src(tmp_path)
    db = tmp_path / "wh.db"
    load_batch(src, db, "T1")
    con = sqlite3.connect(db)
    n1 = con.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    con.close()
    load_batch(src, db, "T1")
    con = sqlite3.connect(db)
    n2 = con.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    assert n1 == n2 == 1


def test_unknown_members_and_scd(tmp_path):
    src = _mini_src(tmp_path)
    db = tmp_path / "wh.db"
    load_batch(src, db, "T1")
    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM dim_product WHERE product_sk=0").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM (SELECT product_id FROM dim_product WHERE is_current=1 GROUP BY 1 HAVING COUNT(*)>1)").fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM etl_execution_log").fetchone()[0] >= 10
