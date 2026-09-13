"""Data-source service: status from execution log + guarded CSV upload (validate only)."""

from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime, timezone

SOURCES = ["products", "suppliers", "warehouses", "customers", "carriers",
           "purchase_orders", "po_lines", "sales_orders", "so_lines",
           "inventory_snapshots", "movements", "shipments", "deliveries", "returns"]

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "products": ["product_id", "sku", "name", "category", "standard_cost"],
    "suppliers": ["supplier_id", "name", "rating_tier"],
    "warehouses": ["warehouse_id", "name", "region"],
    "customers": ["customer_id", "name", "region"],
    "carriers": ["carrier_id", "name"],
    "purchase_orders": ["po_id", "supplier_id", "warehouse_id", "order_date", "promised_date"],
    "po_lines": ["po_id", "line_no", "product_id", "ordered_qty", "received_qty", "unit_cost", "receipt_date"],
    "sales_orders": ["so_id", "customer_id", "order_date"],
    "so_lines": ["so_id", "line_no", "product_id", "warehouse_id", "qty", "unit_price"],
    "inventory_snapshots": ["snapshot_date", "product_id", "warehouse_id", "on_hand", "reserved"],
    "movements": ["movement_id", "event_date", "product_id", "warehouse_id", "qty_delta", "reason"],
    "shipments": ["shipment_id", "so_id", "line_no", "carrier_id", "shipment_date", "shipped_qty", "freight_cost"],
    "deliveries": ["shipment_id", "promised_date", "delivery_date", "delivered_qty"],
    "returns": ["return_id", "so_id", "line_no", "product_id", "qty", "reason"],
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def source_status(con: sqlite3.Connection) -> list[dict]:
    out = []
    for name in SOURCES:
        last = con.execute(
            "SELECT status, ended_at, rows_accepted FROM etl_execution_log WHERE source=? "
            "ORDER BY ended_at DESC LIMIT 1", (name,)).fetchone()
        fail = con.execute(
            "SELECT ended_at FROM etl_execution_log WHERE source=? AND status='failed' "
            "ORDER BY ended_at DESC LIMIT 1", (name,)).fetchone()
        wm = con.execute("SELECT last_key, updated_at FROM etl_watermark WHERE source=?", (name,)).fetchone()
        out.append({"name": name, "type": "csv", "status": last[0] if last else "never_run",
                    "last_run": last[1] if last else None, "last_records": last[2] if last else 0,
                    "last_failure": fail[0] if fail else None,
                    "watermark": wm[0] if wm else None,
                    "required_columns": REQUIRED_COLUMNS[name]})
    return out


def validate_upload(name: str, content: bytes) -> dict:
    if name not in REQUIRED_COLUMNS:
        return {"ok": False, "error": f"Unknown source '{name}'"}
    if len(content) > MAX_UPLOAD_BYTES:
        return {"ok": False, "error": "File exceeds 10MB limit"}
    try:
        text = content.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception:
        return {"ok": False, "error": "File is not valid UTF-8 CSV"}
    if not rows:
        return {"ok": False, "error": "CSV has no data rows"}
    missing = [c for c in REQUIRED_COLUMNS[name] if c not in (rows[0].keys() or [])]
    if missing:
        return {"ok": False, "error": f"Missing columns: {', '.join(missing)}"}
    bad = sum(1 for r in rows if any((r.get(c) in (None, "")) for c in REQUIRED_COLUMNS[name]))
    return {"ok": True, "rows": len(rows), "rows_rejected_preview": bad,
            "next_step": "File staged for ETL. Loading runs via POST /api/etl-runs/trigger or CLI."}


def stage_upload(raw_dir: str, name: str, content: bytes, batch: str) -> str:
    from pathlib import Path
    dest = Path(raw_dir) / batch / f"{name}.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return str(dest)
