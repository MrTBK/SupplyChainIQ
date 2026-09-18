"""Phase 4 gates: reproducibility + realistic scenarios + integrity."""

import json
from pathlib import Path

from data_generator.generate import generate

REPO = Path(__file__).resolve().parents[1]


def test_same_seed_identical_hashes(tmp_path):
    m1 = generate(42, tmp_path / "a", days=60)
    m2 = generate(42, tmp_path / "b", days=60)
    assert m1["tables"] == m2["tables"]


def test_different_seed_differs(tmp_path):
    m1 = generate(42, tmp_path / "a", days=60)
    m2 = generate(43, tmp_path / "b", days=60)
    assert m1["tables"]["so_lines"]["sha256"] != m2["tables"]["so_lines"]["sha256"]


def test_scenarios_present(tmp_path):
    m = generate(42, tmp_path / "g", days=120)
    assert m["tables"]["so_lines"]["rows"] > 500
    assert m["tables"]["deliveries"]["rows"] > 500
    assert m["tables"]["returns"]["rows"] > 0
    assert m["tables"]["po_lines"]["rows"] > 0
    # late deliveries exist (slow carrier regime)
    import csv
    late = 0
    total = 0
    with (tmp_path / "g" / "shipments.csv").open() as f:
        ships = {r["shipment_id"]: r for r in csv.DictReader(f)}
    with (tmp_path / "g" / "deliveries.csv").open() as f:
        for r in csv.DictReader(f):
            total += 1
            if r["delivery_date"] > r["promised_date"]:
                late += 1
    assert total > 0 and late > 0

def test_manifest_tagged_synthetic(tmp_path):
    m = generate(7, tmp_path / "g", days=30)
    assert m["seed"] == 7
    assert (tmp_path / "g" / "manifest.json").exists()
    assert (tmp_path / "g" / "products.csv").exists()


def test_scenario_end_anchor(tmp_path):
    from data_generator.generate import SCENARIO_END
    m = generate(7, tmp_path / "g", days=30)
    assert m["end"] == SCENARIO_END
    assert m["start"] < m["end"]
    import csv
    with (tmp_path / "g" / "inventory_snapshots.csv").open() as f:
        snaps = [r["snapshot_date"] for r in csv.DictReader(f)]
    assert max(snaps) == SCENARIO_END
    # explicit start keeps back-compat (end derived)
    m2 = generate(7, tmp_path / "h", days=30, start="2024-01-01")
    assert m2["start"] == "2024-01-01" and m2["end"] == "2024-01-30"


def test_behavior_tiers_and_names(tmp_path):
    import csv
    from datetime import date
    m = generate(42, tmp_path / "g", days=120)
    with (tmp_path / "g" / "suppliers.csv").open() as f:
        sups = list(csv.DictReader(f))
    assert {s["rating_tier"] for s in sups} >= {"A", "B", "C"}
    assert not any(s["name"].startswith("Supplier ") for s in sups)
    tiers = {s["supplier_id"]: s["rating_tier"] for s in sups}
    with (tmp_path / "g" / "purchase_orders.csv").open() as f:
        po_sup = {r["po_id"]: tiers[r["supplier_id"]] for r in csv.DictReader(f)}
    with (tmp_path / "g" / "po_lines.csv").open() as f:
        lines = list(csv.DictReader(f))
    with (tmp_path / "g" / "purchase_orders.csv").open() as f:
        promised = {r["po_id"]: r["promised_date"] for r in csv.DictReader(f)}
    late = {}
    for r in lines:
        d = (date.fromisoformat(r["receipt_date"]) - date.fromisoformat(promised[r["po_id"]])).days
        late.setdefault(po_sup[r["po_id"]], []).append(d)
    # C-tier receipts run later than A-tier by construction
    import statistics
    assert statistics.mean(late["C"]) > statistics.mean(late["A"])
    with (tmp_path / "g" / "products.csv").open() as f:
        names = [r["name"] for r in csv.DictReader(f)]
    assert not any(n.startswith("Product ") for n in names)
    assert len(set(names)) == len(names)
    with (tmp_path / "g" / "carriers.csv").open() as f:
        cnames = [r["name"] for r in csv.DictReader(f)]
    assert not any(n.startswith("Carrier ") for n in cnames)
