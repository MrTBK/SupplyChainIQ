"""Server-side sessions: random IDs in app.db. Revocable, expiring, rotation-safe."""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone

from .db import app_db

IDLE_MINUTES = int(os.environ.get("SCI_SESSION_IDLE_MINUTES", "30"))
ABSOLUTE_HOURS = int(os.environ.get("SCI_SESSION_ABSOLUTE_HOURS", "8"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def init_sessions_schema() -> None:
    con = app_db()
    con.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        last_seen TEXT NOT NULL,
        expires_at TEXT NOT NULL)""")
    con.execute("CREATE INDEX IF NOT EXISTS ix_sessions_user ON sessions(user_id)")
    # users.disabled may predate this migration on existing app.db files
    cols = [r[1] for r in con.execute("PRAGMA table_info(users)").fetchall()]
    if "disabled" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN disabled INTEGER NOT NULL DEFAULT 0")
    con.commit()
    con.close()


def create_session(user_id: int) -> str:
    """Fresh random ID per login (rotation/fixation-safe). Multi-device allowed."""
    sid = secrets.token_urlsafe(32)
    now = _now()
    con = app_db()
    con.execute("INSERT INTO sessions (id, user_id, created_at, last_seen, expires_at)"
                " VALUES (?,?,?,?,?)",
                (sid, user_id, now.isoformat(), now.isoformat(),
                 (now + timedelta(hours=ABSOLUTE_HOURS)).isoformat()))
    con.commit()
    con.close()
    return sid


def get_session(sid: str) -> dict | None:
    """Validate: exists, not expired, idle within limit, user live and enabled."""
    con = app_db()
    row = con.execute("SELECT user_id, last_seen, expires_at FROM sessions WHERE id=?", (sid,)).fetchone()
    now = _now()
    if row is None:
        con.close()
        return None
    if now.isoformat() >= row["expires_at"] or \
            (now - datetime.fromisoformat(row["last_seen"])) > timedelta(minutes=IDLE_MINUTES):
        con.execute("DELETE FROM sessions WHERE id=?", (sid,))
        con.commit()
        con.close()
        return None
    user = con.execute("SELECT id, role, disabled FROM users WHERE id=?", (row["user_id"],)).fetchone()
    if user is None or user["disabled"]:
        con.execute("DELETE FROM sessions WHERE id=?", (sid,))
        con.commit()
        con.close()
        return None
    con.execute("UPDATE sessions SET last_seen=? WHERE id=?", (now.isoformat(), sid))
    con.commit()
    con.close()
    return {"uid": user["id"], "role": user["role"]}


def destroy_session(sid: str) -> None:
    con = app_db()
    con.execute("DELETE FROM sessions WHERE id=?", (sid,))
    con.commit()
    con.close()


def destroy_user_sessions(user_id: int) -> None:
    con = app_db()
    con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    con.commit()
    con.close()
