"""14.9 gate: summary cuts + late list identify delay hotspots."""

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
                ("log", hash_password("pw"), "logistics_manager"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": "log", "password": "pw"}).status_code == 200
    return c


def test_logistics_summary_and_late(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        s = c.get("/api/logistics/summary").json()
        assert set(s) >= {"otd", "p90_delay_days", "late_count", "by_carrier", "by_region"}
        assert s["deliveries"] >= 1 and len(s["by_carrier"]) >= 1
        late = c.get("/api/logistics/late").json()
        assert late["total"] == s["late_count"]
        if late["total"]:
            assert late["items"][0]["delay_days"] > 0
    finally:
        c.__exit__()
