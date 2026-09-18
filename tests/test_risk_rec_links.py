"""Phase 17 gate: stable risk/rec IDs + bidirectional links on real engine output."""

import sqlite3

from api.services.linkage import link, rec_id, risk_id
from api.services.recommendations import recommend
from api.services.risks import evaluate


def _con(tmp_path):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    con = sqlite3.connect(str(db))
    con.execute("UPDATE fact_inventory_snapshot SET on_hand=1, available=1")
    con.commit()
    con.row_factory = sqlite3.Row
    return con


def test_ids_stable_and_prefixed(tmp_path):
    con = _con(tmp_path)
    risks, recs = link(evaluate(con), recommend(con))
    assert risks and recs
    for r in risks:
        assert r["id"].startswith("RSK-") and r["id"] == risk_id(r)
    for r in recs:
        assert r["id"].startswith("REC-") and r["id"] == rec_id(r)
    con.close()


def test_stockout_links_to_reorder_both_directions(tmp_path):
    con = _con(tmp_path)
    risks, recs = link(evaluate(con), recommend(con))
    by_rec = {r["id"]: r for r in recs}
    linked = [r for r in risks if r["kind"] == "stockout_risk" and r["rec_ids"]]
    assert linked, "drained stockout must link to at least one recommendation"
    for r in linked:
        assert any(by_rec[i]["kind"] in ("reorder", "transfer") for i in r["rec_ids"])
        for i in r["rec_ids"]:
            assert r["id"] in by_rec[i]["risk_ids"]
    con.close()
