"""14.4 gate: permission matrix explicit; 401 unauthenticated; 403 role violation."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.rbac import ALL_ROLES, PERMISSIONS, require_perm


@pytest.fixture()
def app(tmp_path, monkeypatch):
    import api.config as cfg
    import api.db as dbmod
    monkeypatch.setattr(cfg, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("exec", hash_password("pw"), "executive"))
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("admin", hash_password("pw"), "administrator"))
    con.commit()
    con.close()
    from api.routes.auth import router as auth_router
    from api.sessions import init_sessions_schema
    from api.users import init_admin_schema
    init_sessions_schema()
    init_admin_schema()
    app = FastAPI()
    app.include_router(auth_router)

    @app.get("/probe-ops", dependencies=[Depends(require_perm("ops:read"))])
    def probe_ops():
        return {"ok": True}

    @app.get("/probe-admin", dependencies=[Depends(require_perm("admin:users"))])
    def probe_admin():
        return {"ok": True}

    with TestClient(app) as c:
        yield c


def login(c, user):
    assert c.post("/api/auth/login", json={"username": user, "password": "pw"}).status_code == 200


def test_matrix_covers_all_roles():
    # every role can read ops; only administrator holds admin:users
    for role in ALL_ROLES:
        assert role in PERMISSIONS["ops:read"], role
    assert PERMISSIONS["admin:users"] == frozenset({"administrator"})
    # no non-admin role has everything
    for role in ALL_ROLES - {"administrator"}:
        assert set(PERMISSIONS) - {p for p, rs in PERMISSIONS.items() if role in rs}, role


def test_executive_reads_ops_but_not_admin(app):
    login(app, "exec")
    assert app.get("/probe-ops").status_code == 200
    assert app.get("/probe-admin").status_code == 403


def test_admin_has_all(app):
    login(app, "admin")
    assert app.get("/probe-ops").status_code == 200
    assert app.get("/probe-admin").status_code == 200


def test_unauthenticated_is_401(app):
    assert app.get("/probe-ops").status_code == 401
    assert app.get("/probe-admin").status_code == 401
