"""Forecast service: history + labeled projections (model, WAPE, horizon). No unexplained numbers."""

from __future__ import annotations

import sqlite3

from forecasting.forecast import (ANALYSIS_END, monthly_series, moving_avg_next,
                                    naive_next, rolling_wape, ses_next)

MODELS = {"naive": naive_next, "ma3": lambda h: moving_avg_next(h, 3), "ses": ses_next}
MODEL_LABELS = {"naive": "Naive carry-forward", "ma3": "3-month moving average",
                "ses": "Simple exponential smoothing"}


def _is_dataco(con: sqlite3.Connection) -> bool:
    try:
        has_stg = con.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='stg_dataco'").fetchone()[0] > 0
        has_status = any(r[1] == "status"
                         for r in con.execute("PRAGMA table_info(fact_deliveries)").fetchall())
        return bool(has_stg and has_status)
    except Exception:  # noqa: BLE001
        return False


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
    dataco = _is_dataco(con)
    prod_filter = {r[0]: r[1] for r in con.execute(
        "SELECT product_sk, category FROM dim_product WHERE is_current=1")}
    prod_names = {r[0]: r[1] for r in con.execute(
        "SELECT product_sk, name FROM dim_product WHERE is_current=1")}
    prod_ids = {r[0]: r[1] for r in con.execute(
        "SELECT product_sk, product_id FROM dim_product WHERE is_current=1")}
    series_all = monthly_series(con, end=ANALYSIS_END if dataco else None,
                                by_product=dataco)
    wh_filter = {} if dataco else {r[0]: r[1] for r in
                                   con.execute("SELECT warehouse_sk, warehouse_id FROM dim_warehouse")}
    items = []
    for (ps, _wh), series in series_all.items():
        hist = [qty for _, qty in series]
        pid = prod_ids.get(ps, "?")
        cat = prod_filter.get(ps, "?")
        wid = "" if dataco else wh_filter.get(_wh, "?")
        if product and product.lower() not in pid.lower() \
                and product.lower() not in prod_names.get(ps, "").lower():
            continue
        if category and cat != category:
            continue
        if warehouse and not dataco and wid != warehouse:
            continue
        scores = {k: rolling_wape(hist, fn) for k, fn in MODELS.items()}
        valid = {k: v for k, v in scores.items() if v is not None}
        best = min(valid, key=valid.get) if valid else "naive"
        avg = round(sum(hist) / len(hist), 1) if hist else 0.0
        proj = _project(hist, best, horizon)
        items.append({"product_id": pid, "product_name": prod_names.get(ps, ""),
                      "category": cat, "warehouse_id": wid,
                      "history": [{"month": m, "qty": q} for m, q in series],
                      "history_avg": avg,
                      "model": best, "model_label": MODEL_LABELS[best],
                      "wape": round(valid[best], 4) if valid else None,
                      "horizon_months": horizon,
                      "projection": proj,
                      "projection_next": proj[0] if proj else None,
                      "change_vs_avg": round((proj[0] - avg) / avg, 4) if proj and avg else None,
                      "window": {"start": series[0][0] if series else None,
                                 "end": series[-1][0] if series else None},
                      "note": "Level projection from selected baseline on complete-coverage months"
                              " through Sep 2017; simplest within 2% WAPE wins per ADR-004."})
    if dataco:
        # Products launched after the analysis window have real but too-short
        # history for a baseline: include them explicitly as no-baseline items
        # rather than silently dropping them.
        have = {ps for ps, _ in series_all}
        full_all = monthly_series(con, by_product=True)
        for (ps,) in con.execute(
                "SELECT DISTINCT product_sk FROM fact_sales WHERE product_sk NOT IN"
                " (SELECT product_sk FROM fact_sales WHERE date_key <= ?)",
                (ANALYSIS_END,)):
            if ps in have or ps == 0:
                continue
            full = full_all.get((ps, 0), [])
            items.append({"product_id": prod_ids.get(ps, "?"),
                          "product_name": prod_names.get(ps, ""),
                          "category": prod_filter.get(ps, "?"), "warehouse_id": "",
                          "history": [{"month": m, "qty": q} for m, q in full],
                          "history_avg": None, "model": None, "model_label": None,
                          "wape": None, "horizon_months": horizon, "projection": [],
                          "projection_next": None, "change_vs_avg": None,
                          "window": {"start": full[0][0] if full else None,
                                     "end": full[-1][0] if full else None},
                          "note": "Launched after Sep 2017; fewer than 7 months of history —"
                                  " no baseline yet. Shown for completeness, not forecast."})
    items.sort(key=lambda x: (x["product_id"], x.get("warehouse_id", "")))
    return {"total": len(items), "items": items[offset:offset + limit]}
