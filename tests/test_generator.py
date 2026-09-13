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
