"""H6 gate: hostile uploads rejected; legit CSV unaffected; staged files never served."""

from pathlib import Path

from fastapi.testclient import TestClient

from api.auth import hash_password, init_auth_schema
from api.db import app_db
from api.main import create_app
from api.services import sources as svc

GOOD = b"product_id,sku,name,category,standard_cost\nP1,SKU-1,A,Snacks,10\n"


def _client(tmp_path, monkeypatch):
    import api.db as dbmod
    monkeypatch.setattr(dbmod, "APP_DB", tmp_path / "app.db")
    monkeypatch.chdir(tmp_path)
    init_auth_schema()
    con = app_db()
    con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("sup", hash_password("pw"), "supply_manager"))
    con.commit()
    con.close()
    c = TestClient(create_app())
    c.__enter__()
    assert c.post("/api/auth/login", json={"username": "sup", "password": "pw"}).status_code == 200
    c.headers.update({"X-CSRF-Token": c.cookies.get("sci_csrf")})
    return c


def _up(c, name, content, filename="f.csv", ctype="text/csv"):
    return c.post(f"/api/data-sources/{name}/upload",
                  files={"file": (filename, content, ctype)})


def test_traversal_and_evil_filenames_neutered(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        assert _up(c, "..%2F..%2Fetc%2Fpasswd", GOOD).status_code in (404, 422)
        r = _up(c, "products", GOOD, filename="../../../tmp/evil.csv")
        assert r.status_code == 200
        assert (tmp_path / "data" / "raw").resolve() in Path(r.json()["staged_at"]).resolve().parents
        assert not (tmp_path / "tmp" / "evil.csv").exists()
    finally:
        c.__exit__()


def test_mime_empty_garbage_rejected(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        assert _up(c, "products", GOOD, ctype="application/x-sh").status_code == 422
        assert _up(c, "products", b"   ").status_code == 422
        assert _up(c, "products", b"\x00\x01\x02\xff" * 100).status_code == 422
        assert _up(c, "products", GOOD, ctype="application/octet-stream").status_code in (200, 409)
    finally:
        c.__exit__()


def test_shape_caps(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        wide = ("c," * 101 + "\n" + "1," * 101 + "\n").encode()
        assert _up(c, "products", wide).status_code == 422
        big = b"product_id,sku,name,category,standard_cost\n" + b"P1,SKU-1," + b"A" * 20001 + b",Snacks,10\n"
        assert _up(c, "products", big).status_code == 422
        monkeypatch.setattr(svc, "MAX_ROWS", 2)
        three = b"product_id,sku,name,category,standard_cost\n" + b"P1,S,A,C,1\n" * 3
        assert _up(c, "products", three).status_code == 422
    finally:
        c.__exit__()


def test_duplicate_detected(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    try:
        assert _up(c, "products", GOOD).status_code == 200
        dup = _up(c, "products", GOOD)
        assert dup.status_code == 409 and "already staged" in dup.json()["error"]["message"]
    finally:
        c.__exit__()


def test_staged_files_never_served_and_guard():
    import api.routes as routes
    import pathlib
    for f in pathlib.Path(routes.__path__[0]).glob("*.py"):
        text = f.read_text()
        assert "FileResponse" not in text and "send_file" not in text, f.name
    import pytest
    with pytest.raises(ValueError):
        svc.stage_upload("data/raw", "../../etc/x", b"a", "b")
