"""Auth: PBKDF2 password hashing (stdlib), session helpers, user store in app.db."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

from .db import app_db

ITERATIONS = 200_000

ROLES = ("executive", "supply_manager", "procurement_manager", "inventory_manager",
         "logistics_manager", "analyst", "administrator")


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2-sha256${ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt_hex, dk_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except (ValueError, TypeError):
        return False


def init_auth_schema() -> None:
    con = app_db()
    con.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        disabled INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')))""")
    con.commit()
    con.close()


def seed_admin() -> str:
    """Create admin from env if missing. Returns username, or '' if skipped."""
    from datetime import datetime, timezone
    username = os.environ.get("SCI_ADMIN_USER", "admin")
    password = os.environ.get("SCI_ADMIN_PASSWORD", "change-me")
    init_auth_schema()
    con = app_db()
    exists = con.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
    if not exists:
        con.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)",
                    (username, hash_password(password), "administrator",
                     datetime.now(timezone.utc).isoformat()))
        con.commit()
    con.close()
    return username


def authenticate(username: str, password: str) -> dict | None:
    con = app_db()
    row = con.execute("SELECT id, username, password_hash, role, disabled FROM users WHERE username=?",
                      (username,)).fetchone()
    con.close()
    if row is None:
        # timing-neutral: unknown accounts cost the same PBKDF2 work (no oracle)
        verify_password(password, hash_password("dummy"))
        return None
    if row["disabled"] or not verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "username": row["username"], "role": row["role"]}
