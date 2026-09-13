"""H3 gate: cookie mutations require a session-bound CSRF token; safe methods don't."""

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app


def _client(tmp_path, monkeypatch):
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("mgr", hash_password("pw"), "supply_manager"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    return c


def _login(c):
    r = c.post("/api/auth/login", json={"username": "mgr", "password": "pw"})
    assert r.status_code == 200  # login itself needs no token (rate-limited instead)
    assert c.cookies.get("sci_csrf"), "login must issue a readable CSRF cookie"
    return c.cookies.get("sci_csrf")


def test_mutation_without_token_rejected(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        _login(c)
        c.headers.pop("X-CSRF-Token", None)
        r = c.post("/api/alerts/evaluate")
        assert r.status_code == 403
        assert r.json() == {"error": {"code": 403, "message": "Missing or invalid CSRF token"}}
        assert c.get("/api/alerts").status_code == 200  # safe methods unaffected
    finally:
        c.__exit__()


def test_mutation_with_wrong_token_rejected(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        _login(c)
        c.headers.update({"X-CSRF-Token": "attacker-guess"})
        assert c.post("/api/alerts/evaluate").status_code == 403
    finally:
        c.__exit__()


def test_cross_session_token_rejected(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        token_a = _login(c)
        _login(c)  # rotation issues a new token
        token_b = c.cookies.get("sci_csrf")
        assert token_a != token_b
        c.headers.update({"X-CSRF-Token": token_a})  # stale token from previous session
        assert c.post("/api/alerts/evaluate").status_code == 403
        c.headers.update({"X-CSRF-Token": token_b})
        assert c.post("/api/alerts/evaluate").status_code == 200
    finally:
        c.__exit__()
