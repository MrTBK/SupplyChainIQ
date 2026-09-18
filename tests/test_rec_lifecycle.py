"""Phase 19 gate: persisted rec lifecycle + alert ack attribution, audited."""

import sqlite3

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app


def _client(tmp_path, monkeypatch, role="supply_manager", user="sup"):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    con = sqlite3.connect(str(db))
    con.execute("UPDATE fact_inventory_snapshot SET on_hand=1, available=1")
    con.commit()
    con.close()
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(dbmod, "WAREHOUSE_DB", db)
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                (user, hash_password("pw"), role))
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("adm", hash_password("pw"), "administrator"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": user, "password": "pw"}).status_code == 200
    c.headers.update({"X-CSRF-Token": c.cookies.get("sci_csrf")})
    return c


def test_lifecycle_pending_to_executed(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        items = c.get("/api/recommendations").json()["items"]
        assert items
        rid = items[0]["id"]
        assert items[0]["rec_status"] == "pending"
        for to in ("reviewed", "approved", "executed"):
            r = c.patch(f"/api/recommendations/{rid}", json={"status": to})
            assert r.status_code == 200, r.text
        got = [i for i in c.get("/api/recommendations").json()["items"] if i["id"] == rid][0]
        assert got["rec_status"] == "executed" and got["rec_actor"] == "sup"
        assert c.get("/api/recommendations", params={"rec_status": "executed"}).json()["total"] >= 1
        assert c.patch(f"/api/recommendations/{rid}", json={"status": "bogus"}).status_code == 422
        assert c.patch("/api/recommendations/NOPE", json={"status": "reviewed"}).status_code == 422
        assert c.post("/api/auth/login", json={"username": "adm", "password": "pw"}).status_code == 200
        c.headers.update({"X-CSRF-Token": c.cookies.get("sci_csrf")})
        audit = c.get("/api/audit", params={"limit": 500}).json()
        assert any(a["action"] == "recommendation.executed" and rid in a["detail"] for a in audit["items"])
    finally:
        c.__exit__()


def test_alert_ack_records_actor(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        c.post("/api/alerts/evaluate")
        aid = c.get("/api/alerts").json()["items"][0]["id"]
        assert c.patch(f"/api/alerts/{aid}", json={"status": "acknowledged"}).status_code == 200
        item = [i for i in c.get("/api/alerts").json()["items"] if i["id"] == aid][0]
        assert item["acknowledged_by"] == "sup" and item["acknowledged_at"] != ""
    finally:
        c.__exit__()
