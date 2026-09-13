"""H4 gate: default same-origin (no ACAO); opt-in origin reflected tightly; wildcard refused."""

import pytest
from fastapi.testclient import TestClient

from api.cors import ALLOWED_HEADERS, ALLOWED_METHODS, apply_cors, cors_origins
from api.main import create_app


def test_default_no_cors_headers():
    with TestClient(create_app()) as c:
        r = c.options("/api/kpis/overview",
                      headers={"Origin": "https://evil.example",
                               "Access-Control-Request-Method": "GET"})
        assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_opt_in_origin_reflected_tightly(tmp_path, monkeypatch):
    monkeypatch.setenv("SCI_CORS_ORIGINS", "https://app.example.com")
    assert cors_origins() == ["https://app.example.com"]
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI()

    @app.get("/x")
    def x():
        return JSONResponse({})
    apply_cors(app)
    with TestClient(app) as c:
        r = c.options("/x", headers={"Origin": "https://app.example.com",
                                     "Access-Control-Request-Method": "POST"})
        assert r.headers.get("access-control-allow-origin") == "https://app.example.com"
        allow_methods = r.headers.get("access-control-allow-methods", "")
        assert "POST" in allow_methods and "TRACE" not in allow_methods
        r2 = c.options("/x", headers={"Origin": "https://evil.example",
                                      "Access-Control-Request-Method": "POST"})
        assert "access-control-allow-origin" not in {k.lower() for k in r2.headers}
    assert set(ALLOWED_METHODS) <= {"GET", "POST", "PATCH", "DELETE", "OPTIONS"}
    assert set(ALLOWED_HEADERS) == {"Content-Type", "X-CSRF-Token"}


def test_wildcard_refused(monkeypatch):
    monkeypatch.setenv("SCI_CORS_ORIGINS", "*")
    with pytest.raises(ValueError):
        cors_origins()
