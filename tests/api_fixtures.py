"""Shared mini-warehouse fixture for API tests (SYNTHETIC, hermetic tmp DB)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from etl.load import load_batch


def build_warehouse(tmp_path: Path, batch: str = "T") -> Path:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    from test_etl_dq import _mini_src
    src = _mini_src(tmp_path)
    db = tmp_path / "wh.db"
    load_batch(src, db, batch)
    return db


def open_ro(db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def login_with_csrf(client, username: str, password: str) -> str:
    """Log in and attach the CSRF header, mirroring frontend/src/api.js behavior."""
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = client.cookies.get("sci_csrf")
    assert token, "login must issue a CSRF cookie"
    client.headers.update({"X-CSRF-Token": token})
    return token
