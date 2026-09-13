"""API foundation: error envelope, pagination/sort/filter helpers."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

MAX_LIMIT = 500
DEFAULT_LIMIT = 50


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code,
                        content={"error": {"code": exc.status_code, "message": exc.detail}})


async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500,
                        content={"error": {"code": 500, "message": "Internal error"}})


def parse_paging(limit: int = DEFAULT_LIMIT, offset: int = 0) -> dict:
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be >= 0")
    return {"limit": max(1, min(limit, MAX_LIMIT)), "offset": offset}


def order_clause(order_by: str, allowed: frozenset[str], default: str) -> str:
    """Allowlisted ORDER BY only. Prefix '-' for DESC. Never interpolates raw input."""
    desc = order_by.startswith("-")
    col = order_by[1:] if desc else order_by
    if col not in allowed:
        col = default
    return f'"{col}" {"DESC" if desc else "ASC"}'


def like_param(value: str) -> str:
    """Escape LIKE wildcards for safe substring search."""
    return "%" + value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
