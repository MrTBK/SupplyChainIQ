"""Warehouse bootstrap + connection (SQLite demo; Postgres canonical via same ANSI SQL)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SQL_DIR = REPO / "warehouse" / "sql"


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    return con


def init_schema(con: sqlite3.Connection) -> None:
    for name in ["001_dims.sql", "002_facts.sql", "003_constraints.sql", "005_infra.sql"]:
        con.executescript((SQL_DIR / name).read_text())
    # unknown members
    con.execute("INSERT OR IGNORE INTO dim_product VALUES (0,'UNKNOWN','UNKNOWN','Unknown','Unknown',0,'1900-01-01',NULL,1)")
    con.execute("INSERT OR IGNORE INTO dim_supplier VALUES (0,'UNKNOWN','Unknown','U','1900-01-01',NULL,1)")
    con.execute("INSERT OR IGNORE INTO dim_warehouse VALUES (0,'UNKNOWN','Unknown','Unknown')")
    con.execute("INSERT OR IGNORE INTO dim_customer VALUES (0,'UNKNOWN','Unknown','Unknown')")
    con.execute("INSERT OR IGNORE INTO dim_carrier VALUES (0,'UNKNOWN','Unknown')")
    con.execute("INSERT OR IGNORE INTO dim_date VALUES ('1900-01-01','1900-01-01',1900,1,1,1,0,'January')")
    con.commit()
