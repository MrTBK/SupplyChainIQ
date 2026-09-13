"""14.16 gate: evaluate persists with day dedupe; ack workflow; RBAC; filters."""

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
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": user, "password": "pw"}).status_code == 200
    c.headers.update({"X-CSRF-Token": c.cookies.get("sci_csrf")})
    return c


def test_evaluate_dedupe_ack(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        first = c.post("/api/alerts/evaluate").json()
        assert first["stored_new"] >= 1
        second = c.post("/api/alerts/evaluate").json()
        assert second["stored_new"] == 0  # same-day dedupe, no spam
        assert second["open_total"] == first["open_total"]
        lst = c.get("/api/alerts").json()
        assert lst["total"] >= 1
        aid = lst["items"][0]["id"]
        assert c.patch(f"/api/alerts/{aid}", json={"status": "acknowledged"}).status_code == 200
        assert c.get("/api/alerts", params={"status": "open"}).json()["total"] == lst["total"] - 1
        assert c.patch("/api/alerts/99999", json={"status": "acknowledged"}).status_code == 404
        assert c.patch(f"/api/alerts/{aid}", json={"status": "bogus"}).status_code == 422
    finally:
        c.__exit__()


def test_evaluate_forbidden_for_analyst(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, role="analyst", user="an")
    try:
        assert c.post("/api/alerts/evaluate").status_code == 403
        assert c.get("/api/alerts").status_code == 200
    finally:
        c.__exit__()
