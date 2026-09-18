"""Serve the built SPA + live API behind one origin (foreground).

Usage: .venv/bin/python scripts/serve_web.py [--web-port 8766 --api-port 8001]
Open http://localhost:8766 and sign in (default admin/change-me, DataCo historical).
Ctrl+C stops both servers. Reuses the proxy Handler from web_e2e.py.
"""

from __future__ import annotations

import argparse
import http.server
import os
import subprocess
import sys
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from web_e2e import Handler, wait  # noqa: E402  (single-source proxy handler)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--web-port", type=int, default=8766)
    ap.add_argument("--api-port", type=int, default=8001)
    a = ap.parse_args()

    dist = REPO / "frontend" / "dist" / "index.html"
    if not dist.exists():
        raise SystemExit("frontend/dist missing — run: cd frontend && npm install && npm run build")

    env = dict(os.environ)
    env.setdefault("SCI_ADMIN_USER", "admin")
    env.setdefault("SCI_ADMIN_PASSWORD", "change-me")
    if env.get("SCI_ADMIN_PASSWORD") == "change-me":
        print("WARNING: default admin credentials in use (DataCo historical only).")

    # point the shared proxy Handler at our API port
    import web_e2e
    web_e2e.API_PORT = a.api_port

    api = subprocess.Popen([str(REPO / ".venv" / "bin" / "uvicorn"), "api.main:app",
                            "--port", str(a.api_port)], cwd=str(REPO), env=env)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", a.web_port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        wait(f"http://127.0.0.1:{a.api_port}/api/health")
        print(f"SupplyChainIQ web live at http://localhost:{a.web_port}  (admin/change-me, DataCo historical)")
        srv.serve_forever()  # foreground until Ctrl+C
    except KeyboardInterrupt:
        print("\nstopping...")
    finally:
        srv.shutdown()
        api.terminate()


if __name__ == "__main__":
    main()
