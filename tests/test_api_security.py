"""14.19 gate: unauthorized, role violations, injection input, session tampering/flags."""

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
                ("admin", hash_password("pw"), "administrator"))
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("an", hash_password("pw"), "analyst"))
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("exec", hash_password("pw"), "executive"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    return c


def _login(c, user):
    assert c.post("/api/auth/login", json={"username": user, "password": "pw"}).status_code == 200
    c.headers.update({"X-CSRF-Token": c.cookies.get("sci_csrf")})


def test_role_violation_sweep(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        _login(c, "an")
        assert c.post("/api/etl-runs/trigger", json={"src": "data"}).status_code == 403
        assert c.post("/api/alerts/evaluate").status_code == 403
        assert c.get("/api/users").status_code == 403
        assert c.get("/api/kpis/overview").status_code == 200  # read allowed
        c.post("/api/auth/logout")
        _login(c, "exec")
        assert c.post("/api/etl-runs/trigger", json={"src": "data"}).status_code == 403
        assert c.get("/api/kpis/overview").status_code == 200
    finally:
        c.__exit__()


def test_injection_inputs_are_neutered(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        _login(c, "an")
        r = c.get("/api/inventory", params={"search": "' OR '1'='1"})
        assert r.status_code == 200 and r.json() == {"total": 0, "items": []}
        r = c.get("/api/suppliers", params={"ordering": "score; DROP TABLE dim_supplier"})
        assert r.status_code == 200 and r.json()["total"] >= 1
        r = c.get("/api/etl-runs", params={"limit": 999999})
        assert r.status_code == 200
    finally:
        c.__exit__()


def test_session_cookie_flags_and_tampering(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        r = c.post("/api/auth/login", json={"username": "an", "password": "pw"})
        set_cookie = r.headers.get("set-cookie", "")
        assert "httponly" in set_cookie.lower()
        assert c.get("/api/auth/me").status_code == 200
        c.cookies.set("sci_session", "forged-value")
        assert c.get("/api/auth/me").status_code == 401
    finally:
        c.__exit__()
