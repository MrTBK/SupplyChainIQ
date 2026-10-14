"""H8 gate: request IDs unique + echoed; logs secret-free; readiness reflects DB state."""

import logging

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app


def _client(tmp_path, monkeypatch):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    import api.config as cfg
    import api.db as dbmod
    monkeypatch.setattr(cfg, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(cfg, "WAREHOUSE_DB", db)
    monkeypatch.setattr(dbmod, "WAREHOUSE_DB", db)
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("u1", hash_password("pw"), "analyst"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    return c


def test_request_id_unique_and_echoed(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        r1 = c.get("/api/health")
        r2 = c.get("/api/health")
        assert r1.headers["X-Request-ID"] != r2.headers["X-Request-ID"]
        r3 = c.get("/api/health", headers={"X-Request-ID": "caller-supplied"})
        assert r3.headers["X-Request-ID"] == "caller-supplied"
    finally:
        c.__exit__()


def test_access_log_has_no_secrets(tmp_path, monkeypatch, caplog):
    c = _client(tmp_path, monkeypatch)
    try:
        with caplog.at_level(logging.INFO, logger="supplychainiq.access"):
            c.post("/api/auth/login", json={"username": "u1", "password": "pw"})
            c.get("/api/kpis/overview")
        text = "\n".join(r.getMessage() for r in caplog.records)
        assert "POST" in text and "/api/auth/login" in text and "uid=" in text
        assert "pw" not in text and "sci_session" not in text and "sci_csrf" not in text
    finally:
        c.__exit__()


def test_readiness_checks_both_dbs(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        body = c.get("/api/ready").json()
        assert body["checks"]["app_db"] == "ok"
        assert set(body["checks"]) == {"app_db", "warehouse"}
        assert body["status"] in ("ok", "degraded")
    finally:
        c.__exit__()
