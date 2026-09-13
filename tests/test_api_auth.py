"""14.3 gate: login/logout/session handling, password security (hash, no plaintext)."""

import os

import pytest
from fastapi.testclient import TestClient

from api.auth import hash_password, verify_password
from api.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SCI_APP_DB", str(tmp_path / "app.db"))
    monkeypatch.setenv("SCI_ADMIN_USER", "admin")
    monkeypatch.setenv("SCI_ADMIN_PASSWORD", "s3cret-test")
    import api.config as cfg
    monkeypatch.setattr(cfg, "APP_DB", tmp_path / "app.db")
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_password_hashing_roundtrip():
    h = hash_password("s3cret-test")
    assert "s3cret" not in h
    assert verify_password("s3cret-test", h)
    assert not verify_password("wrong", h)
    assert not verify_password("x", "garbage")


def test_login_me_logout(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "s3cret-test"})
    assert r.status_code == 200 and r.json()["role"] == "administrator"
    me = client.get("/api/auth/me").json()
    assert me["username"] == "admin" and me["role"] == "administrator"  # shell needs username on reload
    token = client.cookies.get("sci_csrf")
    client.headers.update({"X-CSRF-Token": token})
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_login_rejects_bad_credentials(client):
    assert client.post("/api/auth/login", json={"username": "admin", "password": "nope"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "ghost", "password": "x"}).status_code == 401
    assert client.get("/api/auth/me").status_code == 401
