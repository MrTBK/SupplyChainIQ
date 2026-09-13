"""H2 gate: brute-force throttled with 429+Retry-After; success resets; envelope kept."""

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app
from api.rate_limit import MAX_ATTEMPTS, reset_all


def _client(tmp_path, monkeypatch):
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("victim", hash_password("pw"), "analyst"))
    con.commit()
    con.close()
    reset_all()
    c = TestClient(create_app())
    c.__enter__()
    return c


def test_login_rate_limited_then_envelope(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        for _ in range(MAX_ATTEMPTS):
            r = c.post("/api/auth/login", json={"username": "victim", "password": "wrong"})
            assert r.status_code == 401
        blocked = c.post("/api/auth/login", json={"username": "victim", "password": "wrong"})
        assert blocked.status_code == 429
        assert blocked.json() == {"error": {"code": 429, "message": "Too many login attempts, try again later"}}
        assert "retry-after" in {k.lower() for k in blocked.headers}
        # even the right password is refused while blocked (no oracle, no bypass)
        assert c.post("/api/auth/login", json={"username": "victim", "password": "pw"}).status_code == 429
    finally:
        c.__exit__()


def test_success_resets_bucket(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        for _ in range(MAX_ATTEMPTS - 1):
            c.post("/api/auth/login", json={"username": "victim", "password": "wrong"})
        assert c.post("/api/auth/login", json={"username": "victim", "password": "pw"}).status_code == 200
        # bucket cleared: a new failure streak starts from zero, not from MAX-1
        assert c.post("/api/auth/login", json={"username": "victim", "password": "wrong"}).status_code == 401
    finally:
        c.__exit__()
