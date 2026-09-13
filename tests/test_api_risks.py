"""14.11 gate: every risk has severity/entity/time/reason/metrics/action; filters work."""

import sqlite3

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app

REQUIRED = {"kind", "severity", "entity_type", "entity_id", "detected_at",
            "reason", "metrics", "action"}


def _client(tmp_path, monkeypatch):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    # force a stockout-risk case: drain on-hand for the single product
    con = sqlite3.connect(str(db))
    con.execute("UPDATE fact_inventory_snapshot SET on_hand=1, available=1")
    con.commit()
    con.close()
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(dbmod, "WAREHOUSE_DB", db)
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("mgr", hash_password("pw"), "supply_manager"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": "mgr", "password": "pw"}).status_code == 200
    return c


def test_risks_have_full_explanation(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        r = c.get("/api/risks")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 1
        for item in body["items"]:
            assert REQUIRED <= set(item), item
        kinds = {i["kind"] for i in body["items"]}
        assert "stockout_risk" in kinds
        sev = c.get("/api/risks", params={"severity": "high"}).json()
        assert all(i["severity"] == "high" for i in sev["items"])
    finally:
        c.__exit__()
