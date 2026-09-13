"""SupplyChainIQ operational API. Frontend -> this API -> services -> warehouse/marts."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from starlette.middleware.sessions import SessionMiddleware

from .alerts import init_alerts_schema
from .auth import seed_admin
from .config import SECRET_KEY
from .foundation import http_exception_handler, unhandled_handler
from .routes.alerts import router as alerts_router
from .routes.auth import router as auth_router
from .routes.etl_runs import router as etl_runs_router
from .routes.forecasts import router as forecasts_router
from .routes.inventory import router as inventory_router
from .routes.logistics import router as logistics_router
from .routes.overview import router as overview_router
from .routes.quality import router as quality_router
from .routes.recommendations import router as recommendations_router
from .routes.risks import router as risks_router
from .routes.sources import router as sources_router
from .routes.suppliers import router as suppliers_router


def create_app() -> FastAPI:
    seed_admin()
    init_alerts_schema()
    app = FastAPI(title="SupplyChainIQ API", version="0.1.0")
    app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, session_cookie="sci_session",
                       max_age=8 * 3600, same_site="lax", https_only=False)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_handler)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    app.include_router(alerts_router)
    app.include_router(auth_router)
    app.include_router(etl_runs_router)
    app.include_router(forecasts_router)
    app.include_router(inventory_router)
    app.include_router(logistics_router)
    app.include_router(overview_router)
    app.include_router(quality_router)
    app.include_router(recommendations_router)
    app.include_router(risks_router)
    app.include_router(sources_router)
    app.include_router(suppliers_router)
    return app


app = create_app()
