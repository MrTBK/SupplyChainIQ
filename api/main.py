"""SupplyChainIQ operational API. Frontend -> this API -> services -> warehouse/marts."""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from .config import SECRET_KEY


def create_app() -> FastAPI:
    app = FastAPI(title="SupplyChainIQ API", version="0.1.0")
    app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, session_cookie="sci_session",
                       max_age=8 * 3600, same_site="lax", https_only=False)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
