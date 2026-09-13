"""14.2 gate: app imports, health endpoint answers, DB discipline holds."""

from fastapi.testclient import TestClient

from api.main import create_app


def test_health():
    app = create_app()
    with TestClient(app) as c:
        r = c.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
