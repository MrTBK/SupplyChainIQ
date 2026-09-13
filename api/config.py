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
