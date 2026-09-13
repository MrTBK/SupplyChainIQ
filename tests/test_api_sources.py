"""14.13 gate: status reflects runs; upload validates schema; RBAC enforced; no auto-load."""

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app

PRODUCTS_CSV = b"product_id,sku,name,category,standard_cost\nP1,SKU-1,A,Snacks,10\n"
BAD_CSV = b"product_id,sku\nP1,SKU-1\n"


def _client(tmp_path, monkeypatch, role="supply_manager", user="sup"):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(dbmod, "WAREHOUSE_DB", db)
    monkeypatch.chdir(tmp_path)  # uploads stage under tmp data/raw
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


def test_sources_status_and_upload(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        items = c.get("/api/data-sources").json()["items"]
        assert len(items) == 14
        assert set(items[0]) >= {"name", "type", "status", "last_run", "watermark", "required_columns"}
        ok = c.post("/api/data-sources/products/upload", files={"file": ("products.csv", PRODUCTS_CSV)})
        assert ok.status_code == 200 and ok.json()["rows"] == 1
        bad = c.post("/api/data-sources/products/upload", files={"file": ("products.csv", BAD_CSV)})
        assert bad.status_code == 422
    finally:
        c.__exit__()


def test_upload_forbidden_for_analyst(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, role="analyst", user="an")
    try:
        assert c.get("/api/data-sources").status_code == 200
        r = c.post("/api/data-sources/products/upload", files={"file": ("p.csv", PRODUCTS_CSV)})
        assert r.status_code == 403
    finally:
        c.__exit__()
