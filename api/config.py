"""Central config from environment. No secrets in code."""

from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SECRET_KEY = os.environ.get("SCI_SECRET_KEY", "dev-only-insecure-change-in-prod")
WAREHOUSE_DB = Path(os.environ.get("SCI_WAREHOUSE_DB", str(REPO / "data" / "warehouse.db")))
APP_DB = Path(os.environ.get("SCI_APP_DB", str(REPO / "data" / "app.db")))
SESSION_COOKIE = "sci_session"
# Local demo runs plain HTTP; set SCI_COOKIE_SECURE=1 behind HTTPS in production.
COOKIE_SECURE = os.environ.get("SCI_COOKIE_SECURE", "0") == "1"
# JSON body cap (uploads have their own 10MB rule in services/sources.py).
MAX_BODY_BYTES = int(os.environ.get("SCI_MAX_BODY_BYTES", str(1024 * 1024)))


def trusted_hosts() -> list[str]:
    return [h.strip() for h in os.environ.get("SCI_TRUSTED_HOSTS", "").split(",") if h.strip()]


def using_dev_secrets() -> list[str]:
    """Names of security settings still on insecure dev defaults (warn, never log values)."""
    weak = []
    if os.environ.get("SCI_SECRET_KEY", "") == "":
        weak.append("SCI_SECRET_KEY")
    if os.environ.get("SCI_ADMIN_PASSWORD", "change-me") == "change-me":
        weak.append("SCI_ADMIN_PASSWORD")
    return weak
