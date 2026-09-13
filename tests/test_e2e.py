"""E2E: seed-7 generate → load → KPI + forecast + prescription smoke."""

from pathlib import Path

from analytics.prescriptions import reorder_recommendation
from data_generator.generate import generate
from etl.load import load_batch
from forecasting.forecast import forecast_all
import sqlite3


def test_e2e_seed7(tmp_path):
    src = tmp_path / "src"
    generate(7, src, days=90)
    db = tmp_path / "wh.db"
    out = load_batch(src, db, "E2E")
    assert out["quarantined"] >= 0
    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0] > 500
    assert con.execute("SELECT COUNT(*) FROM fact_inventory_snapshot").fetchone()[0] > 0
    fc = forecast_all(con)
    assert len(fc) > 0 and all("forecast_next" in r and "model" in r for r in fc[:5])
    r = reorder_recommendation(450, 0, 700, 150)
    assert r["reorder_qty"] == 400 and r["risk"] == "High"
