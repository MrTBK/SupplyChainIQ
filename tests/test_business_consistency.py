"""Phase 44 (part 2): KPI/risk/rec/alert definitions agree across layers."""

import sqlite3

from analytics.kpis import coverage_days
from analytics.analytics import supplier_score
from api.services import logistics as svc_log
from api.services import recommendations as svc_rec
from api.services import risks as svc_risk
from api.services.forecasts import forecasts
from api.services.linkage import link


def _wh(tmp_path):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    return con


def test_otif_matches_receipt_definition(tmp_path):
    con = _wh(tmp_path)
    sk = con.execute("SELECT supplier_sk FROM dim_supplier WHERE supplier_id='S001'").fetchone()[0]
    expect = con.execute("SELECT AVG(CASE WHEN late_days<=0 THEN 1.0 ELSE 0 END) "
                         "FROM fact_purchases WHERE supplier_sk=?", (sk,)).fetchone()[0]
    assert supplier_score(con, sk)["otif"] == expect
    con.close()


def test_otd_matches_delivery_definition(tmp_path):
    con = _wh(tmp_path)
    expect = con.execute("SELECT AVG(CAST(on_time AS FLOAT)) FROM fact_deliveries").fetchone()[0]
    got = svc_log.summary(con)["otd"]
    assert (got == round(expect, 3)) or (got is None and expect is None)
    con.close()


def test_coverage_matches_available_over_demand(tmp_path):
    con = _wh(tmp_path)
    row = con.execute("SELECT product_sk, warehouse_sk, available FROM fact_inventory_snapshot "
                      "LIMIT 1").fetchone()
    avgd = con.execute(
        "SELECT AVG(qty) FROM fact_sales WHERE product_sk=? AND warehouse_sk=? "
        "AND date_key >= (SELECT date(MAX(date_key), '-30 days') FROM fact_sales)",
        (row[0], row[1])).fetchone()[0]
    got = coverage_days(con, row[0], row[1])
    assert got == (row[2] / avgd if avgd else None)
    con.close()


def test_high_reorders_always_link_a_risk(tmp_path):
    con = _wh(tmp_path)
    con.execute("UPDATE fact_inventory_snapshot SET on_hand=1, available=1")
    con.commit()
    risks, recs = link(svc_risk.evaluate(con), svc_rec.recommend(con))
    highs = [r for r in recs if r["kind"] == "reorder" and r["risk"] == "High"]
    assert highs
    assert all(r["risk_ids"] for r in highs)
    con.close()


def test_forecast_shape_and_horizon(tmp_path):
    con = _wh(tmp_path)
    out = forecasts(con, horizon=3, limit=50)
    assert out["items"]
    for f in out["items"]:
        months = [h["month"] for h in f["history"]]
        assert months == sorted(months)
        assert len(f["projection"]) == f["horizon_months"] == 3
        assert f["wape"] is None or f["wape"] >= 0
    con.close()


def test_no_reorders_for_stale_demand(tmp_path):
    from data_generator.generate import generate
    from etl.load import load_batch
    out = tmp_path / "stale"
    generate(42, out, days=120)
    db = tmp_path / "wh.db"
    load_batch(out, db, "STALE")
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    end = con.execute("SELECT MAX(date_key) FROM fact_sales").fetchone()[0]
    recs = svc_rec.recommend(con)
    from datetime import date
    end_d = date.fromisoformat(end)
    for r in recs:
        if r["kind"] != "reorder":
            continue
        last = con.execute("SELECT MAX(date_key) FROM fact_sales WHERE product_sk="
                           "(SELECT product_sk FROM dim_product WHERE product_id=? AND is_current=1) "
                           "AND warehouse_sk=(SELECT warehouse_sk FROM dim_warehouse WHERE warehouse_id=?)",
                           (r["product_id"], r["warehouse_id"])).fetchone()[0]
        assert last is not None and (end_d - date.fromisoformat(last)).days <= 90, (r["entity_id"], last)
    con.close()
