"""SupplyChainIQ operational API. Frontend -> this API -> services -> warehouse/marts."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from starlette.middleware.sessions import SessionMiddleware

from .auth import seed_admin
from .config import SECRET_KEY
from .foundation import http_exception_handler, unhandled_handler
from .routes.auth import router as auth_router
from .routes.overview import router as overview_router


def create_app() -> FastAPI:
    seed_admin()
    app = FastAPI(title="SupplyChainIQ API", version="0.1.0")
    app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, session_cookie="sci_session",
                       max_age=8 * 3600, same_site="lax", https_only=False)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_handler)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    app.include_router(auth_router)
    app.include_router(overview_router)
    return app


app = create_app()
