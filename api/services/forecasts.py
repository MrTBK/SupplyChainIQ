"""Forecast service: history + labeled projections (model, WAPE, horizon). No unexplained numbers."""

from __future__ import annotations

import sqlite3

from forecasting.forecast import monthly_series, moving_avg_next, naive_next, rolling_wape, ses_next

MODELS = {"naive": naive_next, "ma3": lambda h: moving_avg_next(h, 3), "ses": ses_next}


def _project(history: list[float], model: str, horizon: int) -> list[float]:
    fn = MODELS[model]
    hist, out = list(history), []
    for _ in range(horizon):
        f = fn(hist)
        out.append(round(f, 2))
        hist.append(f)
    return out


def forecasts(con: sqlite3.Connection, product: str = "", category: str = "", warehouse: str = "",
              horizon: int = 1, limit: int = 50, offset: int = 0) -> dict:
    horizon = max(1, min(horizon, 3))
    prod_filter = {r[0]: r[1] for r in con.execute(
        "SELECT product_sk, category FROM dim_product WHERE is_current=1")}
    wh_filter = {r[0]: r[1] for r in con.execute("SELECT warehouse_sk, warehouse_id FROM dim_warehouse")}
    items = []
    for (ps, wh), series in monthly_series(con).items():
        hist = [qty for _, qty in series]
        info = con.execute("SELECT product_id FROM dim_product WHERE product_sk=?", (ps,)).fetchone()
        pid = info[0] if info else "?"
        cat = prod_filter.get(ps, "?")
        wid = wh_filter.get(wh, "?")
        if product and product.lower() not in pid.lower():
            continue
        if category and cat != category:
            continue
        if warehouse and wid != warehouse:
            continue
        scores = {k: rolling_wape(hist, fn) for k, fn in MODELS.items()}
        valid = {k: v for k, v in scores.items() if v is not None}
        best = min(valid, key=valid.get) if valid else "naive"
        items.append({"product_id": pid, "category": cat, "warehouse_id": wid,
                      "history": [{"month": m, "qty": q} for m, q in series],
                      "model": best,
                      "wape": round(valid[best], 4) if valid else None,
                      "horizon_months": horizon,
                      "projection": _project(hist, best, horizon),
                      "note": "Level projection from selected baseline; simplest within 2% WAPE wins per ADR-004."})
    items.sort(key=lambda x: (x["product_id"], x["warehouse_id"]))
    return {"total": len(items), "items": items[offset:offset + limit]}
