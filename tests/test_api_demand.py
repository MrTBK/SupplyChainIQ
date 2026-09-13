"""F5 gate: trend endpoint aggregates honestly; bounded months."""

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
                ("an", hash_password("pw"), "analyst"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": "an", "password": "pw"}).status_code == 200
    return c


def test_demand_trend_shape(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        body = c.get("/api/demand/trend").json()
        assert set(body) == {"months", "top_categories"}
        assert len(body["months"]) >= 1
        assert set(body["months"][0]) == {"month", "qty", "revenue"}
        assert len(c.get("/api/demand/trend", params={"months": 1}).json()["months"]) == 1
    finally:
        c.__exit__()
