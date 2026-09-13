"""14.17 gate: admin CRUD guards, roles matrix, audit trail."""

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
                ("admin", hash_password("pw"), "administrator"))
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("an", hash_password("pw"), "analyst"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    return c


def _login(c, user):
    assert c.post("/api/auth/login", json={"username": user, "password": "pw"}).status_code == 200
    c.headers.update({"X-CSRF-Token": c.cookies.get("sci_csrf")})


def test_admin_crud_guards_and_audit(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        _login(c, "admin")
        me = c.get("/api/auth/me").json()["id"]
        assert c.post("/api/users", json={"username": "op", "password": "long-enough", "role": "analyst"}).status_code == 200
        assert c.post("/api/users", json={"username": "op", "password": "long-enough", "role": "analyst"}).status_code == 409
        assert c.post("/api/users", json={"username": "x", "password": "short", "role": "analyst"}).status_code == 422
        assert c.post("/api/users", json={"username": "x", "password": "long-enough", "role": "ceo"}).status_code == 422
        users = c.get("/api/users").json()
        op = [u for u in users["items"] if u["username"] == "op"][0]
        assert c.patch(f"/api/users/{op['id']}", json={"role": "executive"}).json()["role"] == "executive"
        assert c.delete(f"/api/users/{me}").status_code == 400  # self
        assert c.delete(f"/api/users/{op['id']}").status_code == 200
        assert c.delete("/api/users/1").status_code == 400  # last admin (admin id 1)
        roles = c.get("/api/roles").json()
        assert roles["total"] == 7
        audit = c.get("/api/audit").json()["items"]
        assert {a["action"] for a in audit} >= {"user.create", "user.update", "user.delete"}
    finally:
        c.__exit__()


def test_non_admin_blocked(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        _login(c, "an")
        assert c.get("/api/users").status_code == 403
        assert c.get("/api/audit").status_code == 403
        assert c.post("/api/users", json={"username": "z", "password": "long-enough", "role": "analyst"}).status_code == 403
    finally:
        c.__exit__()
