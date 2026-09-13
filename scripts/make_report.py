"""Static browser-readable demo report from the warehouse (SYNTHETIC data).

Generates reports/demo.html. No dependencies, no server code, no app.
Run: .venv/bin/python scripts/make_report.py [--db data/warehouse.db --out reports/demo.html]
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def q(c: sqlite3.Connection, sql: str, args: tuple = ()):
    return c.execute(sql, args).fetchall()


def build(db_path: Path) -> str:
    c = sqlite3.connect(db_path)
    sales = q(c, "SELECT COUNT(*), COALESCE(SUM(qty),0), COALESCE(SUM(net_amount),0) FROM fact_sales")[0]
    snaps = q(c, "SELECT COUNT(*), COALESCE(SUM(available*unit_cost),0) FROM fact_inventory_snapshot "
                 "WHERE snapshot_date_key=(SELECT MAX(snapshot_date_key) FROM fact_inventory_snapshot)")[0]
    otif = q(c, "SELECT ROUND(AVG(CASE WHEN late_days<=0 THEN 1.0 ELSE 0 END),3) FROM fact_purchases")[0][0]
    otd = q(c, "SELECT ROUND(AVG(CAST(on_time AS FLOAT)),3) FROM fact_deliveries")[0][0]
    quar = q(c, "SELECT COUNT(*) FROM dq_quarantine")[0][0]
    top_cat = q(c, "SELECT p.category, SUM(f.qty*f.unit_price) v FROM fact_sales f "
                   "JOIN dim_product p ON p.product_sk=f.product_sk GROUP BY 1 ORDER BY 2 DESC LIMIT 5")
    worst_sup = q(c, "SELECT s.supplier_id, COUNT(*), ROUND(AVG(CASE WHEN f.late_days<=0 THEN 1.0 ELSE 0 END),3) "
                     "FROM fact_purchases f JOIN dim_supplier s ON s.supplier_sk=f.supplier_sk "
                     "GROUP BY 1 HAVING COUNT(*)>=5 ORDER BY 3 ASC LIMIT 5")
    carriers = q(c, "SELECT COALESCE(cr.carrier_id,'?'), COUNT(*), ROUND(AVG(CAST(d.on_time AS FLOAT)),3) "
                    "FROM fact_shipments s LEFT JOIN fact_deliveries d ON d.shipment_id=s.shipment_id "
                    "LEFT JOIN dim_carrier cr ON cr.carrier_sk=s.carrier_sk GROUP BY 1 ORDER BY 3 ASC")
    c.close()

    def rows(rs):
        return "\n".join("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>" for r in rs)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SupplyChainIQ — Demo Report (SYNTHETIC)</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#1a1a1a}}
.banner{{background:#fff3cd;border:1px solid #e6c200;padding:.75rem 1rem;border-radius:8px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.75rem;margin:1rem 0}}
.card{{border:1px solid #ddd;border-radius:8px;padding:.75rem 1rem}}
.card b{{font-size:1.4rem;display:block}}
table{{border-collapse:collapse;width:100%;margin:.5rem 0 1.5rem}}
th,td{{border:1px solid #ddd;padding:.4rem .6rem;text-align:left;font-size:.9rem}}
th{{background:#f4f4f4}}
h2{{margin-top:2rem;border-bottom:2px solid #222;padding-bottom:.25rem}}
</style></head><body>
<div class="banner"><b>SYNTHETIC demo data only.</b> Never present these numbers as real company figures. Source: warehouse marts.</div>
<h1>SupplyChainIQ — Decision Demo</h1>
<h2>Executive snapshot</h2>
<div class="grid">
<div class="card"><span>Sales lines</span><b>{sales[0]:,}</b></div>
<div class="card"><span>Units sold</span><b>{int(sales[1]):,}</b></div>
<div class="card"><span>Revenue</span><b>{sales[2]:,.0f}</b></div>
<div class="card"><span>Latest inventory value</span><b>{snaps[1]:,.0f}</b></div>
<div class="card"><span>Procurement OTIF</span><b>{otif}</b></div>
<div class="card"><span>Delivery OTD</span><b>{otd}</b></div>
<div class="card"><span>Quarantined rows</span><b>{quar}</b></div>
</div>
<h2>Demand by category (top 5)</h2>
<table><tr><th>Category</th><th>Revenue</th></tr>{rows([(a, f"{b:,.0f}") for a, b in top_cat])}</table>
<h2>Suppliers needing attention (lowest OTIF)</h2>
<table><tr><th>Supplier</th><th>Receipts</th><th>OTIF</th></tr>{rows(worst_sup)}</table>
<h2>Carrier performance</h2>
<table><tr><th>Carrier</th><th>Shipments</th><th>OTD</th></tr>{rows(carriers)}</table>
<h2>Recommended actions</h2>
<ol>
<li>Renegotiate or replace the lowest-OTIF suppliers above (procurement review).</li>
<li>Reroute East-lane volume off the lowest-OTD carrier.</li>
<li>Work the dead/overstock list in Power BI page 2 before next buy cycle.</li>
</ol>
<p><small>Method: docs/kpis.md. Forecast + prescriptions: analytics/ + forecasting/. Full plan: docs/PROJECT_PLAN.md.</small></p>
</body></html>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/warehouse.db")
    ap.add_argument("--out", default="reports/demo.html")
    a = ap.parse_args()
    out = REPO / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(REPO / a.db))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
