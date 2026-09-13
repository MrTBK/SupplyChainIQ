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
