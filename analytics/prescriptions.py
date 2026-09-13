"""Explainable prescriptions: reorder, safety stock, transfer, risk. Every row carries inputs."""

from __future__ import annotations

import math
import sqlite3


def safety_stock(demand_std: float, lead_time_days: int, z: float = 1.65) -> float:
    return z * demand_std * math.sqrt(max(lead_time_days, 1))


def reorder_recommendation(on_hand: float, on_order: float, forecast_lead_demand: float,
                           safety: float) -> dict:
    qty = max(0.0, forecast_lead_demand + safety - on_hand - on_order)
    if qty <= 0:
        risk = "Low"
    elif on_hand < forecast_lead_demand:
        risk = "High"
    else:
        risk = "Medium"
    return {"reorder_qty": round(qty, 1), "forecast_lead_demand": round(forecast_lead_demand, 1),
            "safety_stock": round(safety, 1), "on_hand": on_hand, "on_order": on_order,
            "reason": "ROP breach" if qty > 0 else "covered",
            "risk": risk}
