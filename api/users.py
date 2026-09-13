"""User store + audit log (app.db). Least privilege: admin-only management."""

from __future__ import annotations

from datetime import datetime, timezone

from .auth import ROLES, hash_password
from .db import app_db
from .rbac import PERMISSIONS


def init_admin_schema() -> None:
    con = app_db()
    con.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY, ts TEXT NOT NULL, actor TEXT NOT NULL,
        action TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '')""")
    con.commit()
    con.close()


def audit(actor: str, action: str, detail: str = "") -> None:
    con = app_db()
    con.execute("INSERT INTO audit_log (ts, actor, action, detail) VALUES (?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), actor, action, detail))
    con.commit()
    con.close()


def list_users() -> list[dict]:
    con = app_db()
    rows = con.execute("SELECT id, username, role, created_at FROM users ORDER BY username").fetchall()
    con.close()
    return [dict(r) for r in rows]


def create_user(username: str, password: str, role: str) -> dict:
    username = username.strip()
    if not username or len(password) < 8:
        raise ValueError("username required, password min 8 chars")
    if role not in ROLES:
        raise ValueError(f"role must be one of {sorted(ROLES)}")
    con = app_db()
    try:
        cur = con.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                          (username, hash_password(password), role))
        con.commit()
    except Exception as e:  # noqa: BLE001 - uniqueness violation surfaces as 409
        con.close()
        raise ValueError(f"username '{username}' already exists") from e
    uid = cur.lastrowid
    con.close()
    return {"id": uid, "username": username, "role": role}


def update_user(uid: int, role: str = "", password: str = "") -> dict | None:
    if role and role not in ROLES:
        raise ValueError(f"role must be one of {sorted(ROLES)}")
    con = app_db()
    row = con.execute("SELECT id FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        con.close()
        return None
    if role:
        con.execute("UPDATE users SET role=? WHERE id=?", (role, uid))
    if password:
        if len(password) < 8:
            con.close()
            raise ValueError("password min 8 chars")
        con.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(password), uid))
    con.commit()
    row = con.execute("SELECT id, username, role, created_at FROM users WHERE id=?", (uid,)).fetchone()
    con.close()
    return dict(row)


def delete_user(uid: int, actor_id: int) -> str:
    """Returns 'ok', 'self', 'missing', or 'last-admin' — caller maps to status codes."""
    if uid == actor_id:
        return "self"
    con = app_db()
    row = con.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        con.close()
        return "missing"
    if row["role"] == "administrator":
        n = con.execute("SELECT COUNT(*) FROM users WHERE role='administrator'").fetchone()[0]
        if n <= 1:
            con.close()
            return "last-admin"
    con.execute("DELETE FROM users WHERE id=?", (uid,))
    con.commit()
    con.close()
    return "ok"


def read_audit(limit: int = 100) -> list[dict]:
    con = app_db()
    rows = con.execute("SELECT id, ts, actor, action, detail FROM audit_log "
                       "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


def role_matrix() -> list[dict]:
    return [{"role": r, "permissions": sorted(p for p, rs in PERMISSIONS.items() if r in rs)}
            for r in sorted(ROLES)]
