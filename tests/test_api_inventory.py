"""14.7 gate: list/search/filter/pagination + drill with forecast, safety, risk, recommendation."""

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app


def _client(tmp_path, monkeypatch):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(dbmod, "WAREHOUSE_DB", db)
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("inv", hash_password("pw"), "inventory_manager"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": "inv", "password": "pw"}).status_code == 200
    return c


def test_inventory_list_and_search(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        r = c.get("/api/inventory")
        assert r.status_code == 200 and r.json()["total"] >= 1
        assert c.get("/api/inventory", params={"search": "P0001"}).json()["total"] >= 1
        assert c.get("/api/inventory", params={"search": "ZZZ-nope"}).json() == {"total": 0, "items": []}
        assert c.get("/api/inventory", params={"limit": 1}).json()["total"] >= 1
        assert len(c.get("/api/inventory", params={"limit": 1}).json()["items"]) == 1
    finally:
        c.__exit__()


def test_product_drill_explains_itself(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        r = c.get("/api/products/P0001")
        assert r.status_code == 200
        body = r.json()
        assert set(body) >= {"product_id", "recent_monthly_demand", "forecast", "lead_time_p50_days", "warehouses"}
        wh = body["warehouses"][0]
        assert set(wh) >= {"available", "coverage_days", "forecast_lead_demand", "safety_stock",
                           "reorder_qty", "risk", "reason"}
        assert c.get("/api/products/NOPE").status_code == 404
    finally:
        c.__exit__()
