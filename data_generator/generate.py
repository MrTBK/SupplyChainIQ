"""Deterministic SYNTHETIC supply-chain generator (stdlib only)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import random
from datetime import date, timedelta
from pathlib import Path

GENERATOR_VERSION = "v0.1.0"
CATEGORIES = ["Beverages", "Snacks", "Household", "Personal Care", "Electronics Acc"]
REGIONS = ["North", "South", "East", "West"]


def monthly_seasonality(m: int) -> float:
    return 1.0 + 0.25 * math.sin(2 * math.pi * (m - 1) / 12)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def generate(seed: int, out: Path, days: int = 730, start: str = "2024-01-01") -> dict:
    rng = random.Random(seed)
    start_d = date.fromisoformat(start)
    out.mkdir(parents=True, exist_ok=True)

    n_products, n_suppliers, n_wh, n_cust, n_car = 120, 24, 4, 300, 5
    products = [
        {
            "product_id": f"P{i:04d}",
            "sku": f"SKU-{i:04d}",
            "name": f"Product {i:04d}",
            "category": CATEGORIES[i % len(CATEGORIES)],
            "standard_cost": round(rng.uniform(2, 120), 2),
            "is_synthetic": "true",
        }
        for i in range(1, n_products + 1)
    ]
    # 5% discontinued halfway (dead stock scenario)
    dead = {p["product_id"] for p in rng.sample(products, k=6)}
    suppliers = [
        {"supplier_id": f"S{i:03d}", "name": f"Supplier {i:03d}",
         "rating_tier": rng.choice(["A", "B", "C"]), "is_synthetic": "true"}
        for i in range(1, n_suppliers + 1)
    ]
    slow_suppliers = {suppliers[0]["supplier_id"], suppliers[1]["supplier_id"]}
    warehouses = [
        {"warehouse_id": f"W{i}", "name": f"WH-{r}", "region": r}
        for i, r in enumerate(REGIONS[:n_wh], 1)
    ]
    customers = [
        {"customer_id": f"C{i:04d}", "name": f"Customer {i:04d}",
         "region": rng.choice(REGIONS)}
        for i in range(1, n_cust + 1)
    ]
    carriers = [{"carrier_id": f"CR{i}", "name": f"Carrier {i}"} for i in range(1, n_car + 1)]
    slow_carrier = carriers[0]["carrier_id"]

    contracts = []
    for p in products:
        for s in rng.sample(suppliers, k=2):
            contracts.append({
                "contract_id": f"K-{s['supplier_id']}-{p['product_id']}",
                "supplier_id": s["supplier_id"], "product_id": p["product_id"],
                "unit_cost": round(p["standard_cost"] * rng.uniform(0.85, 1.05), 2),
                "lead_time_days": rng.randint(4, 21), "capacity": rng.randint(500, 5000),
            })

    # price step mid-period for Snacks +10%
    price_step_day = days // 2

    so_rows, sol_rows, ship_rows, del_rows, ret_rows = [], [], [], [], []
    po_rows, pol_rows = [], []
    so_id = po_id = ship_id = ret_id = 0
    base_demand = {p["product_id"]: rng.randint(2, 40) for p in products}

    for d in range(days):
        day = start_d + timedelta(days=d)
        m = day.month
        promo = 2.0 if (day.month in (11, 6) and day.day <= 10) else 1.0
        for p in products:
            if p["product_id"] in dead and d > days // 2:
                continue
            lam = base_demand[p["product_id"]] * monthly_seasonality(m) * promo
            lam *= 0.7 if day.weekday() >= 5 else 1.0
            # poisson-ish via rounded exponential
            n_orders = max(0, int(rng.expovariate(1 / max(lam / 8, 0.5)) - 1)) if lam > 0 else 0
            for _ in range(min(n_orders, 6)):
                so_id += 1
                cust = rng.choice(customers)
                wh = rng.choice(warehouses)
                qty = max(1, int(rng.expovariate(1 / max(lam / 3, 1))))
                price = round(p["standard_cost"] * 1.35 * (1.10 if (p["category"] == "Snacks" and d > price_step_day) else 1.0), 2)
                so_rows.append({"so_id": f"SO{so_id:06d}", "customer_id": cust["customer_id"], "order_date": day.isoformat()})
                sol_rows.append({"so_id": f"SO{so_id:06d}", "line_no": 1, "product_id": p["product_id"],
                                 "warehouse_id": wh["warehouse_id"], "qty": qty, "unit_price": price})
                ship_id += 1
                car = carriers[0] if (wh["region"] == "East" and rng.random() < 0.5) else rng.choice(carriers)
                sdate = day + timedelta(days=rng.randint(0, 2))
                ship_rows.append({"shipment_id": f"SH{ship_id:06d}", "so_id": f"SO{so_id:06d}", "line_no": 1,
                                  "carrier_id": car["carrier_id"], "shipment_date": sdate.isoformat(),
                                  "shipped_qty": qty, "freight_cost": round(rng.uniform(5, 60), 2)})
                late_extra = rng.randint(3, 9) if car["carrier_id"] == slow_carrier else rng.randint(0, 3)
                ddate = sdate + timedelta(days=rng.randint(1, 4) + late_extra)
                promised = sdate + timedelta(days=4)
                del_rows.append({"shipment_id": f"SH{ship_id:06d}", "promised_date": promised.isoformat(),
                                 "delivery_date": ddate.isoformat(), "delivered_qty": qty})
                # returns: quality incident window for supplier-linked cats + random damage
                if rng.random() < (0.04 if d in range(days // 3, days // 3 + 30) else 0.012):
                    ret_id += 1
                    ret_rows.append({"return_id": f"R{ret_id:05d}", "so_id": f"SO{so_id:06d}", "line_no": 1,
                                     "product_id": p["product_id"], "qty": max(1, qty // 4),
                                     "reason": rng.choice(["QUALITY", "DAMAGE", "OTHER"])})
        # weekly POs (replenishment + overstock scenario in W1)
        if d % 7 == 0:
            for _ in range(6):
                po_id += 1
                sup = rng.choice(suppliers)
                wh = warehouses[0] if rng.random() < 0.35 else rng.choice(warehouses)  # W1 overstock bias
                odate = day
                promised = odate + timedelta(days=10)
                late = rng.randint(4, 12) if sup["supplier_id"] in slow_suppliers else rng.randint(0, 3)
                rdate = odate + timedelta(days=10 + late)
                po_rows.append({"po_id": f"PO{po_id:05d}", "supplier_id": sup["supplier_id"],
                                "warehouse_id": wh["warehouse_id"], "order_date": odate.isoformat(),
                                "promised_date": promised.isoformat()})
                for ln, p in enumerate(rng.sample(products, k=3), 1):
                    oq = rng.randint(50, 400) * (2 if wh["warehouse_id"] == "W1" and rng.random() < 0.3 else 1)
                    pol_rows.append({"po_id": f"PO{po_id:05d}", "line_no": ln, "product_id": p["product_id"],
                                     "ordered_qty": oq, "received_qty": max(0, oq - rng.randint(0, 5)),
                                     "unit_cost": round(p["standard_cost"] * 0.95, 2),
                                     "receipt_date": rdate.isoformat()})

    # snapshots + movements derived from flows (simplified on-hand walk)
    from collections import defaultdict
    oh: dict[tuple[str, str], int] = defaultdict(lambda: 200)
    snap_rows, mov_rows = [], []
    mov_id = 0
    # index receipts/sales by date
    from collections import defaultdict as dd
    rec_by_day: dict[tuple[str, str, str], int] = dd(int)
    for r in pol_rows:
        po = next(x for x in po_rows if x["po_id"] == r["po_id"])
        rec_by_day[(r["receipt_date"], r["product_id"], po["warehouse_id"])] += r["received_qty"]
    sale_by_day: dict[tuple[str, str, str], int] = dd(int)
    for r in sol_rows:
        pass  # so_lines lack date; join via so_rows below
    so_date = {r["so_id"]: r["order_date"] for r in so_rows}
    for r in sol_rows:
        sale_by_day[(so_date[r["so_id"]], r["product_id"], r["warehouse_id"])] += r["qty"]

    for d in range(days):
        day = start_d + timedelta(days=d)
        ds = day.isoformat()
        for p in products:
            for wh in warehouses:
                rec = rec_by_day.get((ds, p["product_id"], wh["warehouse_id"]), 0)
                sal = sale_by_day.get((ds, p["product_id"], wh["warehouse_id"]), 0)
                if rec:
                    mov_id += 1
                    mov_rows.append({"movement_id": f"M{mov_id:07d}", "event_date": ds,
                                     "product_id": p["product_id"], "warehouse_id": wh["warehouse_id"],
                                     "qty_delta": rec, "reason": "RECEIPT"})
                if sal:
                    mov_id += 1
                    mov_rows.append({"movement_id": f"M{mov_id:07d}", "event_date": ds,
                                     "product_id": p["product_id"], "warehouse_id": wh["warehouse_id"],
                                     "qty_delta": -sal, "reason": "SALE"})
                oh[(p["product_id"], wh["warehouse_id"])] += rec - sal
                if d % 7 == 0 or d == days - 1:
                    snap_rows.append({"snapshot_date": ds, "product_id": p["product_id"],
                                      "warehouse_id": wh["warehouse_id"],
                                      "on_hand": oh[(p["product_id"], wh["warehouse_id"])],
                                      "reserved": int(sal * 0.2)})

    tables = {
        "products": (["product_id", "sku", "name", "category", "standard_cost", "is_synthetic"], products),
        "suppliers": (["supplier_id", "name", "rating_tier", "is_synthetic"], suppliers),
        "contracts": (["contract_id", "supplier_id", "product_id", "unit_cost", "lead_time_days", "capacity"], contracts),
        "warehouses": (["warehouse_id", "name", "region"], warehouses),
        "customers": (["customer_id", "name", "region"], customers),
        "carriers": (["carrier_id", "name"], carriers),
        "purchase_orders": (["po_id", "supplier_id", "warehouse_id", "order_date", "promised_date"], po_rows),
        "po_lines": (["po_id", "line_no", "product_id", "ordered_qty", "received_qty", "unit_cost", "receipt_date"], pol_rows),
        "sales_orders": (["so_id", "customer_id", "order_date"], so_rows),
        "so_lines": (["so_id", "line_no", "product_id", "warehouse_id", "qty", "unit_price"], sol_rows),
        "inventory_snapshots": (["snapshot_date", "product_id", "warehouse_id", "on_hand", "reserved"], snap_rows),
        "movements": (["movement_id", "event_date", "product_id", "warehouse_id", "qty_delta", "reason"], mov_rows),
        "shipments": (["shipment_id", "so_id", "line_no", "carrier_id", "shipment_date", "shipped_qty", "freight_cost"], ship_rows),
        "deliveries": (["shipment_id", "promised_date", "delivery_date", "delivered_qty"], del_rows),
        "returns": (["return_id", "so_id", "line_no", "product_id", "qty", "reason"], ret_rows),
    }
    manifest = {"seed": seed, "generator_version": GENERATOR_VERSION, "days": days, "start": start, "tables": {}}
    for name, (fields, rows) in tables.items():
        write_csv(out / f"{name}.csv", fields, rows)
        h = hashlib.sha256()
        for r in rows:
            h.update(repr(sorted(r.items())).encode())
        manifest["tables"][name] = {"rows": len(rows), "sha256": h.hexdigest()[:16]}
    import json
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=str, default="data/generated/seed-42")
    ap.add_argument("--days", type=int, default=730)
    args = ap.parse_args()
    m = generate(args.seed, Path(args.out), args.days)
    print(f"generated seed={m['seed']} version={GENERATOR_VERSION} tables={len(m['tables'])}")


if __name__ == "__main__":
    main()
