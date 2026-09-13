"""14.10 gate: history + labeled projection + filters; no prediction without explanation."""

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


def test_forecasts_labeled_and_filterable(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        r = c.get("/api/forecasts")
        assert r.status_code == 200 and r.json()["total"] >= 1
        item = r.json()["items"][0]
        assert set(item) >= {"product_id", "history", "model", "horizon_months", "projection", "note"}
        assert item["model"] in ("naive", "ma3", "ses")
        assert len(item["projection"]) == 1
        assert len(c.get("/api/forecasts", params={"horizon": 3}).json()["items"][0]["projection"]) == 3
        assert c.get("/api/forecasts", params={"product": "P0001"}).json()["total"] >= 1
        assert c.get("/api/forecasts", params={"product": "ZZZ"}).json() == {"total": 0, "items": []}
    finally:
        c.__exit__()
