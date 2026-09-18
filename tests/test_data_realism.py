"""Phase 45: synthetic-artifact warnings — distributions must look like a business."""

from analytics.analytics import supplier_score
from api.services import logistics as svc_log
from etl.load import load_batch


def _db(tmp_path_factory):
    from data_generator.generate import generate
    out = tmp_path_factory.mktemp("realism") / "seed-7"
    generate(7, out, days=90)
    db = out.parent / "wh.db"
    load_batch(out, db, "REALISM")
    import sqlite3
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    return con


def test_scores_bands_and_names(tmp_path_factory):
    import sqlite3
    con = _db(tmp_path_factory)
    scores = []
    names = []
    for (sk,) in con.execute("SELECT supplier_sk FROM dim_supplier WHERE supplier_sk != 0"):
        s = supplier_score(con, sk)
        scores.append(s["score"])
        names.append(con.execute("SELECT supplier_id FROM dim_supplier WHERE supplier_sk=?",
                                 (sk,)).fetchone()[0])
    bands = {"Healthy" if s >= 0.8 else "Watch" if s >= 0.6 else "At Risk" if s >= 0.4 else "Critical"
             for s in scores if s is not None}
    assert len(bands) >= 3, bands
    carriers = [r[0] for r in con.execute("SELECT name FROM dim_carrier")]
    assert not any(n.startswith("Carrier ") for n in carriers)
    prods = [r[0] for r in con.execute("SELECT name FROM dim_product WHERE product_sk != 0 LIMIT 50")]
    assert not any(n.startswith("Product ") for n in prods)
    con.close()


def test_carrier_warehouse_spread_and_dates(tmp_path_factory):
    con = _db(tmp_path_factory)
    otds = [r["otd"] for r in svc_log.summary(con)["by_carrier"] if r["otd"] is not None]
    assert max(otds) - min(otds) > 0.05
    totals = [r[0] for r in con.execute(
        "SELECT SUM(qty) FROM fact_sales GROUP BY warehouse_sk")]
    assert max(totals) != min(totals)
    ndays = con.execute("SELECT COUNT(DISTINCT date_key) FROM fact_sales").fetchone()[0]
    assert ndays > 30
    con.close()


def test_quality_scores_reflect_quarantine(tmp_path_factory):
    con = _db(tmp_path_factory)
    for r in con.execute("SELECT source, score FROM dq_batch_score"):
        q = con.execute("SELECT COUNT(*) FROM dq_quarantine WHERE source=?", (r[0],)).fetchone()[0]
        assert (r[1] < 1.0) == (q > 0), (r[0], r[1], q)
    con.close()
