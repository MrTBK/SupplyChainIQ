"""14.14 gate: history matches runs; trigger loads allowlisted src; traversal blocked; RBAC."""

import shutil

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app


def _client(tmp_path, monkeypatch, role="supply_manager", user="sup"):
    from tests.api_fixtures import build_warehouse
    db = build_warehouse(tmp_path)
    import api.config as cfg
    import api.db as dbmod
    monkeypatch.setattr(cfg, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(cfg, "WAREHOUSE_DB", db)
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(dbmod, "WAREHOUSE_DB", db)
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                (user, hash_password("pw"), role))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": user, "password": "pw"}).status_code == 200
    return c, db


def test_run_history_and_trigger(tmp_path, monkeypatch):
    c, db = _client(tmp_path, monkeypatch)
    try:
        hist = c.get("/api/etl-runs").json()
        assert hist["total"] >= 12  # fixture load logs one row per source
        first = hist["items"][0]
        assert set(first) >= {"run_id", "source", "rows_read", "rows_accepted",
                              "rows_rejected", "status", "duration_s"}
        r = c.post("/api/etl-runs/trigger", json={"src": "tests-do-not-exist"}).status_code
        assert r == 422
        trav = c.post("/api/etl-runs/trigger", json={"src": "../../etc"}).status_code
        assert trav == 422
    finally:
        c.__exit__()


def test_trigger_success_loads_allowlisted_src(tmp_path, monkeypatch):
    from tests.api_fixtures import build_warehouse  # noqa (ensures fixture module importable)
    from test_etl_dq import _mini_src
    from api.config import REPO
    staged = REPO / "data" / "_test_trigger_tmp"
    staged.mkdir(parents=True, exist_ok=True)
    mini = tmp_path / "minisrc"
    mini.mkdir(exist_ok=True)
    for f in _mini_src(mini).glob("*.csv"):
        shutil.copy(f, staged / f.name)
    c, db = _client(tmp_path, monkeypatch)
    try:
        before = c.get("/api/etl-runs").json()["total"]
        r = c.post("/api/etl-runs/trigger", json={"src": "data/_test_trigger_tmp", "batch": "TESTAPI"})
        assert r.status_code == 200
        assert r.json()["run_id"].startswith("TESTAPI-")
        assert c.get("/api/etl-runs").json()["total"] > before
    finally:
        c.__exit__()
        shutil.rmtree(staged, ignore_errors=True)


def test_trigger_forbidden_for_analyst(tmp_path, monkeypatch):
    c, db = _client(tmp_path, monkeypatch, role="analyst", user="an")
    try:
        assert c.get("/api/etl-runs").status_code == 200
        assert c.post("/api/etl-runs/trigger", json={"src": "data"}).status_code == 403
    finally:
        c.__exit__()
