"""14.15 gate: gate math, quarantine drill-down, rule catalog parity with yml."""

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
                ("an", hash_password("pw"), "analyst"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": "an", "password": "pw"}).status_code == 200
    return c


def test_dq_score_quarantine_rules(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        score = c.get("/api/data-quality/score").json()
        assert score["threshold"] == 0.98 and score["overall"] is not None
        by_src = {s["source"]: s for s in score["sources"]}
        assert by_src["so_lines"]["gate"] in ("pass", "BLOCKED")
        q = c.get("/api/data-quality/quarantine").json()
        assert q["total"] >= 2
        assert set(q["items"][0]) >= {"rule_id", "reason", "payload", "business_key"}
        assert c.get("/api/data-quality/quarantine", params={"rule": "R02"}).json()["total"] >= 1
        rules = c.get("/api/data-quality/rules").json()
        assert rules["total"] >= 8 and {r["id"] for r in rules["items"]} >= {"R01", "R08"}
    finally:
        c.__exit__()
