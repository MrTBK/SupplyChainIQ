"""Forecasting: monthly series + naive/MA/SES baselines + WAPE + rolling CV (stdlib)."""

from __future__ import annotations

import sqlite3
from collections import defaultdict


def monthly_series(con: sqlite3.Connection) -> dict[tuple[int, int], list[tuple[str, float]]]:
    q = con.execute(
        "SELECT product_sk, warehouse_sk, substr(date_key,1,7) m, SUM(qty) FROM fact_sales GROUP BY 1,2,3 ORDER BY 3")
    out: dict[tuple[int, int], list[tuple[str, float]]] = defaultdict(list)
    for ps, wh, m, qty in q:
        out[(ps, wh)].append((m, float(qty)))
    return out


def naive_next(history: list[float]) -> float:
    return history[-1] if history else 0.0


def moving_avg_next(history: list[float], k: int = 3) -> float:
    h = history[-k:] if history else [0.0]
    return sum(h) / len(h)


def ses_next(history: list[float], alpha: float = 0.3) -> float:
    if not history:
        return 0.0
    level = history[0]
    for x in history[1:]:
        level = alpha * x + (1 - alpha) * level
    return level


def wape(actual: list[float], fc: list[float]) -> float | None:
    d = sum(abs(a) for a in actual)
    return (sum(abs(a - f) for a, f in zip(actual, fc)) / d) if d else None


def rolling_wape(history: list[float], model, min_train: int = 6) -> float | None:
    if len(history) < min_train + 1:
        return None
    errs_a, errs_f = [], []
    for t in range(min_train, len(history)):
        f = model(history[:t])
        errs_a.append(history[t])
        errs_f.append(f)
    return wape(errs_a, errs_f)


def forecast_all(con: sqlite3.Connection, horizon: int = 3) -> list[dict]:
    out = []
    for (ps, wh), series in monthly_series(con).items():
        hist = [q for _, q in series]
        cands = {"naive": naive_next(hist), "ma3": moving_avg_next(hist, 3), "ses": ses_next(hist)}
        scores = {k: rolling_wape(hist, {"naive": naive_next, "ma3": lambda h: moving_avg_next(h, 3), "ses": ses_next}[k])
                  for k in cands}
        valid = {k: v for k, v in scores.items() if v is not None}
        best = min(valid, key=valid.get) if valid else "naive"
        out.append({"product_sk": ps, "warehouse_sk": wh, "history_months": len(hist),
                    "forecast_next": round(cands[best], 2), "model": best,
                    "wape": round(valid[best], 4) if valid else None,
                    "candidates": {k: round(v, 2) for k, v in cands.items()}})
    return out
