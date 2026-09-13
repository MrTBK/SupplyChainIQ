"""KPI/analytics/forecast/prescription gates on mini fixture + leakage + hand-calc."""

import sqlite3
from pathlib import Path

from analytics.analytics import abc_classification, demand_anomalies, turnover_by_category
from analytics.kpis import on_time_delivery, supplier_otif, wape
from analytics.prescriptions import reorder_recommendation, safety_stock
from etl.load import load_batch
from forecasting.forecast import moving_avg_next, naive_next, rolling_wape, ses_next

from test_etl_dq import _mini_src


def _db(tmp_path):
    src = _mini_src(tmp_path)
    db = tmp_path / "wh.db"
    load_batch(src, db, "K")
    return sqlite3.connect(db)


def test_kpi_functions_run(tmp_path):
    con = _db(tmp_path)
    assert on_time_delivery(con) == 0.5  # SH1 late +1d, SHX early → 1 of 2 on time
    sk = con.execute("SELECT supplier_sk FROM dim_supplier WHERE supplier_id='S001'").fetchone()[0]
    assert supplier_otif(con, sk) == 0.0  # receipt 01-11 vs promised 01-10 → late
    assert wape([10, 10], [8, 12]) == 0.2


def test_analytics_run(tmp_path):
    con = _db(tmp_path)
    assert isinstance(turnover_by_category(con), dict)
    assert isinstance(abc_classification(con), dict)
    assert demand_anomalies([10, 11, 10, 12, 50], z=1.5) == [4]
    assert demand_anomalies([10, 11, 10, 12, 50]) == []  # z=3.0 needs stronger spike
    assert demand_anomalies([10, 11]) == []


def test_forecast_no_leakage_and_baselines():
    hist = [10, 12, 11, 13, 12, 14, 13, 15]
    # models use only history prefix inside rolling_wape (no future peeking by construction)
    for m in (naive_next, lambda h: moving_avg_next(h, 3), ses_next):
        assert rolling_wape(hist, m) is not None
    assert naive_next(hist) == 15
    assert moving_avg_next(hist, 3) == (14 + 13 + 15) / 3


def test_prescription_hand_calc():
    # hand-computed: forecast 700 over lead time, safety 150, on hand 450, on order 0 → reorder 400
    r = reorder_recommendation(450, 0, 700, 150)
    assert r["reorder_qty"] == 400
    assert r["risk"] == "High"
    assert set(r) >= {"reorder_qty", "forecast_lead_demand", "safety_stock", "on_hand", "reason", "risk"}
    assert round(safety_stock(10, 9, 1.65), 2) == round(1.65 * 10 * 3.0, 2)
