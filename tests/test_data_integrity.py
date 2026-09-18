"""Phase 44 (part 1): generated-dataset integrity — orphans, date order, domains, period."""

import csv
from datetime import date
from pathlib import Path

import pytest

from data_generator.generate import SCENARIO_END, generate


@pytest.fixture(scope="module")
def ds(tmp_path_factory):
    out = tmp_path_factory.mktemp("integ") / "seed-7"
    m = generate(7, out, days=90)
    return out, m


def rows(ds, name):
    with (ds[0] / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def test_no_orphans(ds):
    prods = {r["product_id"] for r in rows(ds, "products")}
    sups = {r["supplier_id"] for r in rows(ds, "suppliers")}
    whs = {r["warehouse_id"] for r in rows(ds, "warehouses")}
    custs = {r["customer_id"] for r in rows(ds, "customers")}
    cars = {r["carrier_id"] for r in rows(ds, "carriers")}
    pos = {r["po_id"] for r in rows(ds, "purchase_orders")}
    sos = {r["so_id"] for r in rows(ds, "sales_orders")}
    ships = {r["shipment_id"] for r in rows(ds, "shipments")}
    for r in rows(ds, "po_lines"):
        assert r["po_id"] in pos and r["product_id"] in prods
    for r in rows(ds, "purchase_orders"):
        assert r["supplier_id"] in sups and r["warehouse_id"] in whs
    for r in rows(ds, "so_lines"):
        assert r["so_id"] in sos and r["product_id"] in prods and r["warehouse_id"] in whs
    for r in rows(ds, "sales_orders"):
        assert r["customer_id"] in custs
    for r in rows(ds, "shipments"):
        assert r["so_id"] in sos and r["carrier_id"] in cars
    for r in rows(ds, "deliveries"):
        assert r["shipment_id"] in ships
    for r in rows(ds, "returns"):
        assert r["so_id"] in sos and r["product_id"] in prods
    for r in rows(ds, "movements") + rows(ds, "inventory_snapshots"):
        assert r["product_id"] in prods and r["warehouse_id"] in whs


def test_date_order_and_period(ds):
    start, end = ds[1]["start"], ds[1]["end"]
    assert end == SCENARIO_END
    ships = {s["shipment_id"]: s["shipment_date"] for s in rows(ds, "shipments")}
    for r in rows(ds, "deliveries"):
        assert r["delivery_date"] >= ships[r["shipment_id"]]
    pos = {r["po_id"]: r["order_date"] for r in rows(ds, "purchase_orders")}
    for r in rows(ds, "po_lines"):
        assert r["receipt_date"] >= pos[r["po_id"]]
    for name in ("sales_orders", "movements", "inventory_snapshots"):
        dcol = {"sales_orders": "order_date", "movements": "event_date",
                "inventory_snapshots": "snapshot_date"}[name]
        for r in rows(ds, name):
            assert start <= r[dcol] <= end, (name, r[dcol])


def test_non_negative_domains(ds):
    for r in rows(ds, "inventory_snapshots"):
        assert int(r["on_hand"]) >= 0 and int(r["reserved"]) >= 0
        assert int(r["reserved"]) <= int(r["on_hand"])
    for r in rows(ds, "so_lines"):
        assert int(r["qty"]) > 0 and float(r["unit_price"]) > 0
    for r in rows(ds, "po_lines"):
        assert int(r["ordered_qty"]) > 0 and int(r["received_qty"]) >= 0
        assert float(r["unit_cost"]) > 0
