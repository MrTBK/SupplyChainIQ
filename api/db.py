"""DB access discipline: warehouse is READ-ONLY for the API; ops state lives in app.db."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import APP_DB, WAREHOUSE_DB


def warehouse_ro() -> sqlite3.Connection:
    """Read-only warehouse connection. Frontend never touches the DB directly."""
    con = sqlite3.connect(f"file:{WAREHOUSE_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def app_db() -> sqlite3.Connection:
    APP_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(APP_DB))
    con.row_factory = sqlite3.Row
    return con
