"""DataCo adapter: raw CSV validation + profiling (read-only raw, PII dropped).

Raw file is NEVER modified. This module validates file/schema, parses the two
timestamp columns, drops masked PII, and returns typed staging rows.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "DataCo" / "DataCoSupplyChainDataset.csv"

EXPECTED_COLS = 53
REQUIRED = [
    "Order Id", "Order Item Id", "Order Item Quantity",
    "Order Item Product Price", "Order Item Total",
    "order date (DateOrders)", "shipping date (DateOrders)",
    "Days for shipping (real)", "Days for shipment (scheduled)",
    "Delivery Status", "Order Status", "Product Card Id", "Product Name",
    "Category Id", "Category Name", "Customer Id", "Shipping Mode",
]

ORDER_STATUSES = {"COMPLETE", "PENDING", "CLOSED", "PENDING_PAYMENT", "CANCELED",
                  "PROCESSING", "SUSPECTED_FRAUD", "ON_HOLD", "PAYMENT_REVIEW"}
DELIVERY_STATUSES = {"Advance shipping", "Late delivery", "Shipping on time",
                     "Shipping canceled"}


def parse_ts(s: str) -> str:
    """'%m/%d/%Y %H:%M' -> ISO 'YYYY-MM-DD'. Raises ValueError on bad input."""
    return datetime.strptime(s.strip(), "%m/%d/%Y %H:%M").date().isoformat()


def validate_file(path: Path = RAW) -> dict:
    if not path.exists():
        return {"ok": False, "error": f"missing {path}"}
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        cols = list(reader.fieldnames or [])
        if len(cols) != EXPECTED_COLS:
            return {"ok": False, "error": f"expected {EXPECTED_COLS} cols, got {len(cols)}"}
        missing = [c for c in REQUIRED if c not in cols]
        if missing:
            return {"ok": False, "error": f"missing columns: {missing}"}
    size = path.stat().st_size
    return {"ok": True, "path": str(path), "bytes": size, "columns": len(cols)}


def iter_staged(path: Path = RAW):
    """Yield (staging_row, quarantine_reason|None). Never raises on bad rows."""
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        # line_no per Order Id (row_number ordered by Item Id)
        seen_order: dict[str, int] = {}
        seen_key: set[tuple[str, str]] = set()
        for raw in reader:
            oid = (raw.get("Order Id") or "").strip()
            iid = (raw.get("Order Item Id") or "").strip()
            key = (oid, iid)
            if not oid or not iid:
                yield None, ("R01", "null order/item id", key)
                continue
            if key in seen_key:
                yield None, ("R07", "duplicate (Order Id, Order Item Id)", key)
                continue
            seen_key.add(key)
            seen_order[oid] = seen_order.get(oid, 0) + 1
            try:
                qty = int((raw.get("Order Item Quantity") or "").strip())
                if qty <= 0:
                    raise ValueError("qty<=0")
                unit = float((raw.get("Order Item Product Price") or "").strip())
                total = float((raw.get("Order Item Total") or "").strip())
                if unit < 0 or total < 0:
                    raise ValueError("negative price/total")
                real = int((raw.get("Days for shipping (real)") or "").strip())
                sched = int((raw.get("Days for shipment (scheduled)") or "").strip())
                if not (0 <= real <= 10 and 0 <= sched <= 10):
                    raise ValueError("ship days out of range")
                odate = parse_ts(raw.get("order date (DateOrders)") or "")
                sdate = parse_ts(raw.get("shipping date (DateOrders)") or "")
                if sdate < "2015-01-01" or odate < "2015-01-01":
                    raise ValueError("date before dataset epoch")
            except Exception as e:  # noqa: BLE001 - row-level quarantine, not crash
                yield None, ("R02", f"invalid numeric/date: {e}", key)
                continue
            ostatus = (raw.get("Order Status") or "").strip()
            dstatus = (raw.get("Delivery Status") or "").strip()
            if ostatus not in ORDER_STATUSES:
                yield None, ("R03", f"unknown Order Status {ostatus!r}", key)
                continue
            if dstatus not in DELIVERY_STATUSES:
                yield None, ("R03", f"unknown Delivery Status {dstatus!r}", key)
                continue
            delay = real - sched
            row = {
                "order_id": oid, "order_item_id": iid, "line_no": seen_order[oid],
                "qty": qty, "unit_price": unit, "net_amount": total,
                "discount": _f(raw.get("Order Item Discount")),
                "discount_rate": _f(raw.get("Order Item Discount Rate")),
                "benefit": _f(raw.get("Benefit per order")),
                "order_date": odate, "ship_date": sdate,
                "real_days": real, "sched_days": sched,
                "delay_days": delay, "on_time": 1 if delay <= 0 else 0,
                "delivery_status": dstatus, "order_status": ostatus,
                "product_id": (raw.get("Product Card Id") or "").strip(),
                "product_name": (raw.get("Product Name") or "").strip(),
                "category_id": (raw.get("Category Id") or "").strip(),
                "category_name": (raw.get("Category Name") or "").strip(),
                "customer_id": (raw.get("Customer Id") or "").strip(),
                "customer_name": (
                    (raw.get("Customer Fname") or "").strip() + " " +
                    (raw.get("Customer Lname") or "").strip()).strip(),
                "customer_segment": (raw.get("Customer Segment") or "").strip(),
                "order_region": (raw.get("Order Region") or "").strip(),
                "market": (raw.get("Market") or "").strip(),
                "order_country": (raw.get("Order Country") or "").strip(),
                "order_state": (raw.get("Order State") or "").strip(),
                "order_city": (raw.get("Order City") or "").strip(),
                "department_id": (raw.get("Department Id") or "").strip(),
                "department_name": (raw.get("Department Name") or "").strip(),
                "shipping_mode": (raw.get("Shipping Mode") or "").strip(),
                "payment_type": (raw.get("Type") or "").strip(),
            }
            if not row["product_id"] or not row["customer_id"]:
                yield None, ("R01", "null product/customer id", key)
                continue
            yield row, None


def _f(v) -> float:
    try:
        return float((v or "").strip() or 0)
    except ValueError:
        return 0.0


def profile(path: Path = RAW, limit: int = 20000) -> dict:
    """Lightweight profile over first `limit` rows (full scan lives in docs)."""
    n = 0
    statuses: Counter = Counter()
    modes: Counter = Counter()
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, r in enumerate(reader):
            if i >= limit:
                break
            n += 1
            statuses[r.get("Delivery Status", "")] += 1
            modes[r.get("Shipping Mode", "")] += 1
    return {"sample_rows": n, "delivery": dict(statuses), "modes": dict(modes)}
