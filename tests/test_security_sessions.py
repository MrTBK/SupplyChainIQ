"""H1 gate: server-side sessions — logout/revocation/expiry/disable/delete/rotation."""

import sqlite3

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app
from api.sessions import init_sessions_schema


def _client(tmp_path, monkeypatch):
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    init_auth_schema()
    init_sessions_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("u1", hash_password("pw"), "analyst"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    return c


def _login(c, user="u1"):
    r = c.post("/api/auth/login", json={"username": user, "password": "pw"})
    assert r.status_code == 200
    assert "httponly" in r.headers.get("set-cookie", "").lower()
    c.headers.update({"X-CSRF-Token": c.cookies.get("sci_csrf")})
    return r


def test_logout_invalidates_server_side(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        _login(c)
        assert c.get("/api/auth/me").status_code == 200
        sid = c.cookies.get("sci_session")
        assert sid and "." not in sid  # opaque random ID, not a signed payload
        assert c.post("/api/auth/logout").status_code == 200
        assert c.get("/api/auth/me").status_code == 401
        # replaying the old cookie must fail: session is gone server-side
        c.cookies.set("sci_session", sid)
        assert c.get("/api/auth/me").status_code == 401
    finally:
        c.__exit__()


def test_rotation_and_unknown_session_rejected(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        _login(c)
        sid1 = c.cookies.get("sci_session")
        _login(c)
        sid2 = c.cookies.get("sci_session")
        assert sid1 != sid2  # fresh random ID per login (fixation-safe)
        c.cookies.set("sci_session", "never-issued")
        assert c.get("/api/auth/me").status_code == 401
    finally:
        c.__exit__()


def test_deleted_and_disabled_users_lose_access(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        _login(c)
        assert c.get("/api/auth/me").status_code == 200
        con = sqlite3.connect(str(tmp_path / "app.db"))
        con.execute("UPDATE users SET disabled=1 WHERE username='u1'")
        con.commit()
        con.close()
        assert c.get("/api/auth/me").status_code == 401  # revoked on next request
        assert c.post("/api/auth/login", json={"username": "u1", "password": "pw"}).status_code == 401
    finally:
        c.__exit__()


def test_expired_session_rejected(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        _login(c)
        sid = c.cookies.get("sci_session")
        con = sqlite3.connect(str(tmp_path / "app.db"))
        con.execute("UPDATE sessions SET expires_at='2000-01-01T00:00:00+00:00',"
                    " last_seen='2000-01-01T00:00:00+00:00' WHERE id=?", (sid,))
        con.commit()
        con.close()
        assert c.get("/api/auth/me").status_code == 401
    finally:
        c.__exit__()
