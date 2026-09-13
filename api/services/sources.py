"""Data-source service: status from execution log + guarded CSV upload (validate only)."""

from __future__ import annotations

import csv
import hashlib
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

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
MAX_ROWS = 200_000
MAX_COLS = 100
MAX_CELL = 20_000

# Advisory only: real validation is CSV parsing + schema. Anything else is rejected.
ALLOWED_MIME = frozenset({
    "text/csv", "text/plain", "application/vnd.ms-excel",
    "application/octet-stream", "",
})


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


def validate_upload(name: str, content: bytes, content_type: str = "") -> dict:
    if name not in REQUIRED_COLUMNS:
        return {"ok": False, "error": f"Unknown source '{name}'"}
    if content_type.split(";")[0].strip().lower() not in ALLOWED_MIME:
        return {"ok": False, "error": f"Unsupported media type '{content_type}'"}
    if len(content) > MAX_UPLOAD_BYTES:
        return {"ok": False, "error": "File exceeds 10MB limit"}
    if not content.strip():
        return {"ok": False, "error": "Empty file"}
    try:
        text = content.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception:
        return {"ok": False, "error": "File is not valid UTF-8 CSV"}
    if not rows:
        return {"ok": False, "error": "CSV has no data rows"}
    if len(rows) > MAX_ROWS:
        return {"ok": False, "error": f"Row count {len(rows)} exceeds limit {MAX_ROWS}"}
    cols = list(rows[0].keys() or [])
    if len(cols) > MAX_COLS:
        return {"ok": False, "error": f"Column count {len(cols)} exceeds limit {MAX_COLS}"}
    for r in rows:
        for c in cols:
            v = r.get(c) or ""
            if len(v) > MAX_CELL:
                return {"ok": False, "error": f"Cell exceeds {MAX_CELL} chars in column '{c}'"}
    missing = [c for c in REQUIRED_COLUMNS[name] if c not in cols]
    if missing:
        return {"ok": False, "error": f"Missing columns: {', '.join(missing)}"}
    bad = sum(1 for r in rows if any((r.get(c) in (None, "")) for c in REQUIRED_COLUMNS[name]))
    digest = hashlib.sha256(content).hexdigest()
    return {"ok": True, "rows": len(rows), "rows_rejected_preview": bad, "sha256": digest,
            "next_step": "File staged for ETL. Loading runs via POST /api/etl-runs/trigger or CLI."}


def find_duplicate(raw_dir: str, name: str, digest: str) -> str:
    """Same content staged before? Returns existing batch or ''."""
    base = Path(raw_dir)
    if not base.is_dir():
        return ""
    for f in sorted(base.glob(f"*/{name}.csv")):
        try:
            if hashlib.sha256(f.read_bytes()).hexdigest() == digest:
                return f.parent.name
        except OSError:
            continue
    return ""


def stage_upload(raw_dir: str, name: str, content: bytes, batch: str) -> str:
    # Defense in depth: fixed server-side filename; source allowlisted upstream.
    if name not in REQUIRED_COLUMNS or Path(name).name != name:
        raise ValueError(f"Refused unsafe source name '{name}'")
    dest = Path(raw_dir) / batch / f"{name}.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return str(dest)
