"""Phase 51: end-to-end business scenarios through real services (no browser)."""

import sqlite3

from api.services import logistics as svc_log
from api.services import recommendations as svc_rec
from api.services import risks as svc_risk
from api.services.linkage import link


def _wh(tmp_path):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    return con


def _sks(con):
    s = con.execute("SELECT supplier_sk FROM dim_supplier WHERE supplier_id='S001'").fetchone()[0]
    p = con.execute("SELECT product_sk FROM dim_product WHERE product_id='P0001'").fetchone()[0]
    w = con.execute("SELECT warehouse_sk FROM dim_warehouse WHERE warehouse_id='W1'").fetchone()[0]
    c = con.execute("SELECT carrier_sk FROM dim_carrier WHERE carrier_id='CR1'").fetchone()[0]
    return s, p, w, c


def test_s1_supplier_deterioration_to_recommendation(tmp_path):
    con = _wh(tmp_path)
    s, p, w, c = _sks(con)
    for i in range(5):
        con.execute("INSERT INTO fact_purchases (po_id, line_no, supplier_sk, warehouse_sk, product_sk,"
                    " order_date_key, receipt_date_key, ordered_qty, received_qty, unit_cost, late_days)"
                    f" VALUES ('POX{i}',1,{s},{w},{p},'2024-01-01','2024-01-20',10,10,9.0,10)")
    con.commit()
    risks, recs = link(svc_risk.evaluate(con), svc_rec.recommend(con))
    deg = [r for r in risks if r["kind"] == "supplier_degradation" and r["entity_id"] == "S001"]
    assert deg and deg[0]["rec_ids"], "degraded supplier must link to a preferred-supplier rec"
    con.close()


def test_s2_demand_spike_to_stockout_to_reorder(tmp_path):
    con = _wh(tmp_path)
    con.execute("UPDATE fact_inventory_snapshot SET on_hand=0, available=0")
    con.commit()
    risks, recs = link(svc_risk.evaluate(con), svc_rec.recommend(con))
    so = [r for r in risks if r["kind"] == "stockout_risk"]
    assert so
    target = [r for r in recs if r["kind"] == "reorder" and r["entity_id"] == so[0]["entity_id"]]
    assert target and so[0]["id"] in target[0]["risk_ids"]
    assert target[0]["recommended_quantity"] > 0
    con.close()


def test_s3_carrier_delays_to_logistics_risk(tmp_path):
    con = _wh(tmp_path)
    s, p, w, c = _sks(con)
    for i in range(5):
        con.execute("INSERT INTO fact_shipments (shipment_id, so_id, carrier_sk, shipment_date_key,"
                    f" shipped_qty, freight_cost) VALUES ('SHX{i}','SO1',{c},'2024-02-01',5,10.0)")
        con.execute("INSERT INTO fact_deliveries (shipment_id, promised_date_key, delivery_date_key,"
                    f" delivered_qty, on_time, delay_days) VALUES ('SHX{i}','2024-02-05','2024-02-12',5,0,7)")
    con.commit()
    risks, _ = link(svc_risk.evaluate(con), [])
    assert [r for r in risks if r["kind"] == "delivery_risk" and r["entity_id"] == "CR1"]
    late = svc_log.late_deliveries(con, carrier="CR1")
    assert late["total"] >= 5 and all(i["carrier_id"] == "CR1" for i in late["items"])
    con.close()


def test_s4_upload_validate_stage_load_analytics(tmp_path):
    from api.services.sources import stage_upload, validate_upload
    from api.services.overview import overview
    from etl.load import load_batch
    content = (b"product_id,sku,name,category,standard_cost\n"
               b"P9999,SKU-9999,Test Widget,Snacks,5.00\n")
    v = validate_upload("products", content, "text/csv")
    assert v["ok"] and v["rows"] == 1
    batch = stage_upload(str(tmp_path / "raw"), "products", content, "B1")
    assert "B1" in batch
    from tests.test_etl_dq import _mini_src
    db = tmp_path / "wh.db"
    load_batch(_mini_src(tmp_path), db, "B1")
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    assert overview(con)["sales_lines"] == 1
    con.close()
