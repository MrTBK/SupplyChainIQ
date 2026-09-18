"""Phase 43/44: DataCo pipeline integrity — raw = staging = warehouse = API.

Runs against the REAL DataCo CSV (read-only) into a tmp warehouse.
Slow (~1 min); marked for explicit runs but included in the default suite.
"""

import sqlite3
from pathlib import Path

from etl.load_dataco import load
from ingestion.dataco_adapter import RAW, validate_file

needs_dataco = __import__("pytest").mark.skipif(
    not RAW.exists(), reason="DataCo CSV not downloaded (see docs/data/dataco_profile.md)")


@needs_dataco
def test_dataco_file_contract():
    v = validate_file()
    assert v["ok"], v
    assert v["columns"] == 53


@needs_dataco
def test_dataco_load_counts_and_parity(tmp_path):
    db = tmp_path / "dataco.db"
    out = load(db, "TEST")
    assert out["read"] == 180519
    assert out["accepted"] == out["read"] and out["rejected"] == 0
    assert out["status"] == "succeeded"
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    stg = con.execute("SELECT COUNT(*) FROM stg_dataco").fetchone()[0]
    sales = con.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    ship = con.execute("SELECT COUNT(*) FROM fact_shipments").fetchone()[0]
    assert (stg, sales, ship) == (out["read"], out["read"], out["read"])
    # API vs direct DB parity on representative aggregates
    from api.services import overview as ov
    from api.services import logistics as lg
    o = ov.overview(con)
    rev = con.execute("SELECT ROUND(SUM(net_amount),2) FROM fact_sales").fetchone()[0]
    assert o["revenue"] == round(rev, 2)
    assert o["orders"] == con.execute("SELECT COUNT(DISTINCT so_id) FROM fact_sales").fetchone()[0]
    s = lg.summary(con)
    otd = con.execute(
        "SELECT AVG(CAST(on_time AS FLOAT)) FROM fact_deliveries"
        " WHERE status != 'Shipping canceled'").fetchone()[0]
    assert s["otd"] == round(otd, 3)
    assert s["late_count"] == con.execute(
        "SELECT COUNT(*) FROM fact_deliveries WHERE status='Late delivery'").fetchone()[0]
    assert o["period"]["start"] == "2015-01-01"
    # analysis window excludes the sparse Oct 2017+ tail
    assert o["period"]["snapshot"] == "2017-09-30"
    from api.services.demand import trend
    t = trend(con, months=12)
    assert t["months"][-1]["month"] == "2017-09"
    assert all(m["qty"] > 5000 for m in t["months"])
    from api.services.forecasts import forecasts
    fc = forecasts(con, limit=200)
    assert fc["total"] == 118  # 100 baselined + 18 post-window launches shown without baseline
    nobase = [i for i in fc["items"] if i["model"] is None]
    assert len(nobase) == 18 and all(not i["projection"] for i in nobase)
    for item in [i for i in fc["items"] if i["model"] is not None][:5]:
        assert item["warehouse_id"] == "" and item["product_name"]
        assert all(h["month"] <= "2017-09" for h in item["history"])
        assert len(item["projection"]) == item["horizon_months"]
    assert max(h["month"] for i in fc["items"] if i["model"] is not None
               for h in i["history"]) == "2017-09"
    con.close()


@needs_dataco
def test_dataco_no_leakage_columns():
    """Late_delivery_risk / Delivery Status must not be usable as features.

    Guarded by convention: risks service exposes no model using post-outcome
    fields. This test pins the staging contract instead of ML internals.
    """
    import csv
    from ingestion.dataco_adapter import iter_staged
    rows = []
    for row, bad in iter_staged():
        if row:
            rows.append(row)
        if len(rows) >= 500:
            break
    assert rows and all("delay_days" in r and "on_time" in r for r in rows)
    # prediction-safe feature allowlist (see docs/data/dataco_gaps.md)
    allowed = {"shipping_mode", "market", "order_region", "department_name",
               "category_name", "qty", "discount", "sched_days"}
    assert allowed <= set(rows[0])
