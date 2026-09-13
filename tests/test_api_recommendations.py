"""14.12 gate: reorder example from directive reproduces; supplier pick explained; no bare claims."""

import sqlite3

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app


def _client(tmp_path, monkeypatch):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    con = sqlite3.connect(str(db))
    con.execute("UPDATE fact_inventory_snapshot SET on_hand=0, available=0")
    con.commit()
    con.close()
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(dbmod, "WAREHOUSE_DB", db)
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("mgr", hash_password("pw"), "supply_manager"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": "mgr", "password": "pw"}).status_code == 200
    return c


def test_recommendations_explain_why(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        body = c.get("/api/recommendations").json()
        assert body["total"] >= 2
        reorder = [r for r in body["items"] if r["kind"] == "reorder"][0]
        assert set(reorder) >= {"current_stock", "forecast_demand", "safety_stock",
                                "supplier_lead_time_days", "risk", "recommended_quantity",
                                "reason", "action"}
        assert reorder["current_stock"] == 0 and reorder["recommended_quantity"] > 0
        supplier = [r for r in body["items"] if r["kind"] == "supplier"][0]
        assert "OTIF" in supplier["reason"] and supplier["action"].startswith("Prefer ")
        only = c.get("/api/recommendations", params={"kind": "supplier"}).json()
        assert all(r["kind"] == "supplier" for r in only["items"])
    finally:
        c.__exit__()
