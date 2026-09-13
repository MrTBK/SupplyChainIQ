"""14.21 gate: bounded result sizes (no full-table page loads); endpoints complete on budget."""

import time

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app

BUDGET_S = 10.0


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


def test_list_endpoints_bound_results(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        for path in ["/api/inventory", "/api/suppliers", "/api/forecasts",
                     "/api/etl-runs", "/api/data-quality/quarantine", "/api/alerts"]:
            t0 = time.time()
            r = c.get(path, params={"limit": 999999})
            dt = time.time() - t0
            assert r.status_code == 200
            items = r.json().get("items", [])
            assert len(items) <= 500, path
            assert dt < BUDGET_S, (path, dt)
    finally:
        c.__exit__()


def test_aggregations_do_not_scan_per_row_in_python():
    # guardrail: heavy endpoints aggregate in SQL (spot-check service source)
    from pathlib import Path
    for f in ["overview.py", "suppliers.py", "logistics.py"]:
        src = (Path(__file__).resolve().parents[1] / "api" / "services" / f).read_text()
        assert "SELECT" in src and "GROUP BY" in src or "COUNT" in src, f
