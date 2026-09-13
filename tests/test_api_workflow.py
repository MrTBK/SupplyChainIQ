"""14.18 gate: critical workflow through the API the frontend consumes."""

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
                ("mgr", hash_password("pw"), "supply_manager"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    return c


def test_critical_workflow(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        # login -> dashboard -> inventory -> product detail -> forecast -> recommendation
        assert c.post("/api/auth/login", json={"username": "mgr", "password": "pw"}).status_code == 200
        assert c.get("/api/kpis/overview").status_code == 200
        inv = c.get("/api/inventory").json()
        assert inv["total"] >= 1
        pid = inv["items"][0]["product_id"]
        assert c.get(f"/api/products/{pid}").status_code == 200
        assert c.get("/api/forecasts", params={"product": pid}).json()["total"] >= 1
        recs = c.get("/api/recommendations").json()
        assert recs["total"] >= 1
        assert c.post("/api/auth/logout").status_code == 200
        assert c.get("/api/kpis/overview").status_code == 401
    finally:
        c.__exit__()
