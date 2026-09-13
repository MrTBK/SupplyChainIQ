"""CORS: same-origin by default (no middleware). Opt-in exact origins via env.

Deployment model serves SPA + API from one origin, so browsers never need CORS.
Split-origin deployments set SCI_CORS_ORIGINS to a comma-separated list of exact
origins (e.g. https://app.example.com). Wildcards are refused with credentials.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_METHODS = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
ALLOWED_HEADERS = ["Content-Type", "X-CSRF-Token"]


def cors_origins() -> list[str]:
    raw = os.environ.get("SCI_CORS_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if "*" in origins:
        raise ValueError("SCI_CORS_ORIGINS must list exact origins; '*' is forbidden with credentials")
    return origins


def apply_cors(app: FastAPI) -> None:
    origins = cors_origins()
    if not origins:
        return  # same-origin only: tightest possible posture
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS,
        max_age=600,
    )
