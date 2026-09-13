"""14.5 gate: envelope shape, paging caps, allowlisted sort, warehouse read-only."""

import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.foundation import like_param, order_clause, parse_paging
from warehouse.db import init_schema


def test_error_envelope():
    from api.foundation import http_exception_handler, unhandled_handler
    from fastapi import HTTPException
    import asyncio

    async def go():
        r404 = await http_exception_handler(None, HTTPException(status_code=404, detail="Nope"))
        assert r404.status_code == 404
        assert r404.body and b'"code":404' in r404.body
        r500 = await unhandled_handler(None, ValueError("x"))
        assert r500.status_code == 500
        assert b"Internal error" in r500.body
        assert b"x" not in r500.body  # internals never leak
    asyncio.run(go())


def test_paging_caps_and_order_allowlist():
    assert parse_paging(100000, 0)["limit"] == 500
    assert parse_paging(0, 0)["limit"] == 1
    with pytest.raises(Exception):
        parse_paging(10, -1)
    allowed = frozenset({"name", "qty"})
    assert order_clause("-qty", allowed, "name") == '"qty" DESC'
    assert order_clause("evil; DROP TABLE x", allowed, "name") == '"name" ASC'
    assert like_param("100%_x") == "%100\\%\\_x%"


def test_warehouse_connection_is_read_only(tmp_path):
    db = tmp_path / "wh.db"
    con = sqlite3.connect(str(db))
    init_schema(con)
    con.close()
    from api.db import warehouse_ro
    import api.db as dbmod
    orig = dbmod.WAREHOUSE_DB
    dbmod.WAREHOUSE_DB = db
    try:
        con = warehouse_ro()
        with pytest.raises(sqlite3.OperationalError):
            con.execute("CREATE TABLE hack (id INTEGER)")
        con.close()
    finally:
        dbmod.WAREHOUSE_DB = orig


def test_app_serves_envelope_on_404():
    from api.main import create_app
    with TestClient(create_app()) as c:
        r = c.get("/api/nope")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == 404
