"""H10/H12 gate: dev-secret warnings, body cap, trusted hosts; no secrets tracked."""

import logging

from fastapi.testclient import TestClient

from api.main import create_app


def test_dev_secret_warning_and_silence(caplog):
    with caplog.at_level(logging.WARNING, logger="supplychainiq"):
        create_app()
    assert "SCI_SECRET_KEY" in caplog.text and "SCI_ADMIN_PASSWORD" in caplog.text
    assert "change-me" not in caplog.text  # names only, never values


def test_no_secret_files_tracked():
    import subprocess
    from pathlib import Path
    tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                             cwd=str(Path(__file__).resolve().parents[1])).stdout.splitlines()
    bad = [f for f in tracked if f.endswith((".env", ".pem", ".key"))
           or f.endswith(("app.db", "warehouse.db")) or "secret" in f.lower()]
    assert bad == []


def test_body_cap_with_upload_exempt(tmp_path, monkeypatch):
    from api.auth import hash_password, init_auth_schema
    from api.db import app_db
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.chdir(tmp_path)
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("sup", hash_password("pw"), "supply_manager"))
    con.commit()
    con.close()
    with TestClient(create_app()) as c:
        assert c.post("/api/auth/login", json={"username": "sup", "password": "pw"}).status_code == 200
        c.headers.update({"X-CSRF-Token": c.cookies.get("sci_csrf")})
        big = {"username": "x", "password": "y", "role": "analyst", "pad": "z" * (2 * 1024 * 1024)}
        r = c.post("/api/users", json=big)
        assert r.status_code == 413
        assert r.json() == {"error": {"code": 413, "message": "Request body too large"}}
        ok = c.post("/api/data-sources/products/upload",
                    files={"file": ("p.csv", b"product_id,sku,name,category,standard_cost\nP1,S,A,C,1\n",
                                     "text/csv")})
        assert ok.status_code == 200  # upload path exempt from the JSON cap


def test_trusted_hosts_off_by_default_on_when_set(tmp_path, monkeypatch):
    import api.main as mainmod
    monkeypatch.delenv("SCI_TRUSTED_HOSTS", raising=False)
    with TestClient(mainmod.create_app()) as c:
        assert c.get("/api/health").status_code == 200
    monkeypatch.setenv("SCI_TRUSTED_HOSTS", "app.example.com")
    with TestClient(mainmod.create_app()) as c:
        assert c.get("/api/health", headers={"Host": "evil.example"}).status_code == 400
        assert c.get("/api/health", headers={"Host": "app.example.com"}).status_code == 200
