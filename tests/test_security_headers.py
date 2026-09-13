"""H5 gate: header matrix incl. conditional HSTS."""

from fastapi.testclient import TestClient

from api.main import create_app


def test_base_headers_always():
    with TestClient(create_app()) as c:
        r = c.get("/api/health")
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-content-type-options") == "nosniff"
        assert h.get("referrer-policy") == "same-origin"
        assert "camera=()" in h.get("permissions-policy", "")
        assert "frame-ancestors 'none'" in h.get("content-security-policy", "")


def test_hsts_only_with_secure_flag(monkeypatch):
    import api.config as cfg
    import api.headers as hmod
    monkeypatch.setattr(cfg, "COOKIE_SECURE", False)
    monkeypatch.setattr(hmod, "COOKIE_SECURE", False)
    with TestClient(create_app()) as c:
        assert "strict-transport-security" not in {k.lower() for k in c.get("/api/health").headers}
    monkeypatch.setattr(cfg, "COOKIE_SECURE", True)
    monkeypatch.setattr(hmod, "COOKIE_SECURE", True)
    with TestClient(create_app()) as c:
        h = {k.lower(): v for k, v in c.get("/api/health").headers.items()}
        assert "max-age=31536000" in h.get("strict-transport-security", "")
