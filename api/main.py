"""SupplyChainIQ operational API. Frontend -> this API -> services -> warehouse/marts."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .alerts import init_alerts_schema
from .auth import seed_admin
from .config import trusted_hosts, using_dev_secrets
from .cors import apply_cors
from .db import app_db, warehouse_ro
from .foundation import http_exception_handler, unhandled_handler
from .guards import BodyLimitMiddleware
from .headers import SecurityHeadersMiddleware
from .observability import REQUEST_ID_HEADER, ObservabilityMiddleware
from .routes.admin import router as admin_router
from .routes.alerts import router as alerts_router
from .routes.auth import router as auth_router
from .routes.demand import router as demand_router
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
    from .recs import init_rec_schema
    init_rec_schema()
    from .sessions import init_sessions_schema
    init_sessions_schema()
    from .users import init_admin_schema
    init_admin_schema()
    weak = using_dev_secrets()
    if weak:
        logging.getLogger("supplychainiq").warning(
            "insecure dev defaults in use for: %s (override via environment in production)",
            ", ".join(weak))
    app = FastAPI(title="SupplyChainIQ API", version="0.1.0")
    app.add_middleware(ObservabilityMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(BodyLimitMiddleware)
    hosts = trusted_hosts()
    if hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
    apply_cors(app)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_handler)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/ready")
    def ready() -> dict:
        """Readiness: app DB + warehouse reachable. Liveness stays on /api/health."""
        checks: dict[str, str] = {}
        try:
            con = app_db()
            con.execute("SELECT 1").fetchone()
            con.close()
            checks["app_db"] = "ok"
        except Exception as e:  # noqa: BLE001 - surfaced as status, never raised
            checks["app_db"] = f"fail: {type(e).__name__}"
        try:
            con = warehouse_ro()
            con.execute("SELECT 1").fetchone()
            con.close()
            checks["warehouse"] = "ok"
        except Exception as e:  # noqa: BLE001
            checks["warehouse"] = f"fail: {type(e).__name__}"
        status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
        return {"status": status, "checks": checks}

    app.include_router(admin_router)
    app.include_router(alerts_router)
    app.include_router(auth_router)
    app.include_router(demand_router)
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
