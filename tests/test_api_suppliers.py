"""14.8 gate: ranking, ordering, detail with score + lead-time + trend."""

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
                ("pro", hash_password("pw"), "procurement_manager"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": "pro", "password": "pw"}).status_code == 200
    return c


def test_supplier_ranking_and_detail(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        r = c.get("/api/suppliers")
        assert r.status_code == 200 and r.json()["total"] >= 1
        item = r.json()["items"][0]
        assert set(item) >= {"supplier_id", "spend", "otif", "score", "lead_p50", "lead_p90"}
        d = c.get(f"/api/suppliers/{item['supplier_id']}")
        assert d.status_code == 200
        assert set(d.json()) >= {"score", "lead_time", "monthly_spend"}
        assert c.get("/api/suppliers/NOPE").status_code == 404
    finally:
        c.__exit__()


def test_supplier_detail_receipts(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        item = c.get("/api/suppliers").json()["items"][0]
        d = c.get(f"/api/suppliers/{item['supplier_id']}").json()
        assert isinstance(d["recent_receipts"], list) and d["recent_receipts"]
        r0 = d["recent_receipts"][0]
        assert set(r0) >= {"po_id", "product_id", "ordered_qty", "received_qty", "late_days", "receipt_date"}
    finally:
        c.__exit__()
