"""14.6 gate: overview serves gold-logic numbers; RBAC enforced."""

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app


def test_overview_values_and_rbac(tmp_path, monkeypatch):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    import api.config as cfg
    import api.db as dbmod
    monkeypatch.setattr(cfg, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(dbmod, "WAREHOUSE_DB", db)
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("exec", hash_password("pw"), "executive"))
    con.commit()
    con.close()
    with TestClient(create_app()) as c:
        assert c.get("/api/kpis/overview").status_code == 401
        assert c.post("/api/auth/login", json={"username": "exec", "password": "pw"}).status_code == 200
        r = c.get("/api/kpis/overview")
        assert r.status_code == 200
        body = r.json()
        assert body["sales_lines"] == 1 and body["quarantined_rows"] >= 2
        assert set(body) >= {"revenue", "inventory_value", "procurement_otif", "delivery_otd"}
