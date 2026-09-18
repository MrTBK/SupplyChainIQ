"""Logistics date integrity: displayed dates trace to raw DataCo fields.

Source mapping (verified on raw rows, see docs/data/dataco_mapping.md):
- shipping/actual delivery date = `shipping date (DateOrders)`
  (equals order_date + `Days for shipping (real)`)
- scheduled delivery date = `order date (DateOrders)` + `Days for shipment (scheduled)`
- delay_days = delivery - promised = real - sched
- OTD rule (UNCHANGED): on_time = (delay_days <= 0), late = status 'Late delivery'.
"""

import csv
from datetime import datetime
from pathlib import Path

from etl.load_dataco import load

RAW = Path(__file__).resolve().parents[1] / "DataCo" / "DataCoSupplyChainDataset.csv"

needs_dataco = __import__("pytest").mark.skipif(
    not RAW.exists(), reason="DataCo CSV not downloaded (see docs/data/dataco_profile.md)")


def _raw_by_key():
    out = {}
    with RAW.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            out[(row["Order Id"].strip(), row["Order Item Id"].strip())] = row
    return out


@needs_dataco
def test_promised_delivery_keys_match_source_math(tmp_path):
    import sqlite3
    db = tmp_path / "dates.db"
    load(db, "DATES")
    con = sqlite3.connect(str(db))
    bad = con.execute(
        """SELECT COUNT(*) FROM fact_deliveries d JOIN stg_dataco g
        ON g.order_id || '-' || g.order_item_id = d.shipment_id
        WHERE d.promised_date_key != date(g.order_date, '+' || g.sched_days || ' days')
        OR d.delivery_date_key != g.ship_date""").fetchone()[0]
    assert bad == 0
    assert con.execute(
        "SELECT COUNT(*) FROM fact_deliveries"
        " WHERE delay_days != CAST(julianday(delivery_date_key)"
        " - julianday(promised_date_key) AS INTEGER)").fetchone()[0] == 0
    con.close()


@needs_dataco
def test_late_rows_agree_with_otd_rule(tmp_path):
    import sqlite3
    db = tmp_path / "dates2.db"
    load(db, "DATES2")
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    # every displayed-late row is late by the KPI rule, with promised < delivered
    assert con.execute(
        "SELECT COUNT(*) FROM fact_deliveries WHERE status='Late delivery'"
        " AND (on_time != 0 OR promised_date_key >= delivery_date_key)").fetchone()[0] == 0
    # no on-time (non-canceled) row hides a positive date gap
    assert con.execute(
        "SELECT COUNT(*) FROM fact_deliveries WHERE status != 'Late delivery'"
        " AND status != 'Shipping canceled'"
        " AND (on_time != 1 OR promised_date_key < delivery_date_key)").fetchone()[0] == 0
    # KPI parity: late count equals on_time=0 non-canceled count
    assert con.execute(
        "SELECT COUNT(*) FROM fact_deliveries WHERE status='Late delivery'").fetchone()[0] == \
        con.execute(
        "SELECT COUNT(*) FROM fact_deliveries WHERE on_time=0"
        " AND status != 'Shipping canceled'").fetchone()[0]
    con.close()


@needs_dataco
def test_displayed_rows_trace_to_raw_csv(tmp_path):
    """Sample displayed late rows back to raw DataCo records."""
    import sqlite3
    db = tmp_path / "dates3.db"
    load(db, "DATES3")
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    from api.services.logistics import late_deliveries
    page = late_deliveries(con, limit=25, offset=0)
    assert page["total"] > 0 and len(page["items"]) == 25
    raw = _raw_by_key()
    for item in page["items"]:
        oid, iid = item["shipment_id"].rsplit("-", 1)
        row = raw[(oid, iid)]
        o = datetime.strptime(row["order date (DateOrders)"].strip(), "%m/%d/%Y %H:%M").date()
        s = datetime.strptime(row["shipping date (DateOrders)"].strip(), "%m/%d/%Y %H:%M").date()
        real, sched = int(row["Days for shipping (real)"]), int(row["Days for shipment (scheduled)"])
        assert s.isoformat() == item["delivered"] == con.execute(
            "SELECT delivery_date_key FROM fact_deliveries WHERE shipment_id=?",
            (item["shipment_id"],)).fetchone()[0]
        assert date_add(o, sched) == item["promised"]
        assert (s - o).days - sched == item["delay_days"] == real - sched > 0
        assert row["Delivery Status"].strip() == "Late delivery"
    con.close()


def date_add(d, days):
    from datetime import timedelta
    return (d + timedelta(days=days)).isoformat()
