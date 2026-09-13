"""H7 gate: auth/ETL/upload lifecycle audited; no secrets in audit rows."""

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app
from api.users import read_audit


def _client(tmp_path, monkeypatch):
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.chdir(tmp_path)  # uploads stage under tmp, never the repo
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("mgr", hash_password("pw"), "supply_manager"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    return c


def test_auth_lifecycle_audited(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        c.post("/api/auth/login", json={"username": "mgr", "password": "wrong"})
        c.post("/api/auth/login", json={"username": "mgr", "password": "pw"})
        c.headers.update({"X-CSRF-Token": c.cookies.get("sci_csrf")})
        c.post("/api/auth/logout")
        actions = [a["action"] for a in read_audit()]
        assert "LOGIN_FAILED" in actions and "LOGIN" in actions and "LOGOUT" in actions
    finally:
        c.__exit__()


def test_etl_and_upload_audited_without_secrets(tmp_path, monkeypatch):
    from tests.api_fixtures import build_warehouse  # noqa
    c = _client(tmp_path, monkeypatch)
    try:
        c.post("/api/auth/login", json={"username": "mgr", "password": "pw"})
        c.headers.update({"X-CSRF-Token": c.cookies.get("sci_csrf")})
        c.post("/api/etl-runs/trigger", json={"src": "nope"})
        c.post("/api/data-sources/products/upload",
               files={"file": ("p.csv", b"product_id,sku,name,category,standard_cost\nP1,S,A,C,1\n", "text/csv")})
        actions = [a["action"] for a in read_audit()]
        assert "ETL_STARTED" in actions and "ETL_FAILED" in actions and "UPLOAD_STAGED" in actions
        blob = " ".join(f"{a['action']} {a['actor']} {a['detail']}" for a in read_audit()).lower()
        for secret in ["pw", "sci_session", "sci_csrf", "pbkdf2"]:
            assert secret not in blob, secret
    finally:
        c.__exit__()
