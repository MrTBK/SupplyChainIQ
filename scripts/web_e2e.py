"""Browser E2E: built SPA + live API behind one origin, real login flow via agent-browser.

Usage: .venv/bin/python scripts/web_e2e.py
Proxies /api/* to uvicorn, serves frontend/dist otherwise (SPA fallback).
Evidence: reports/web-login.png, reports/web-overview.png (git-ignored).
"""

from __future__ import annotations

import http.server
import os
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
API_PORT = 8001
WEB_PORT = 8766


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(REPO / "frontend" / "dist"), **kw)

    def _proxy(self):
        url = f"http://127.0.0.1:{API_PORT}{self.path}"
        data = None
        if self.command in ("POST", "PATCH", "PUT"):
            data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        req = urllib.request.Request(url, data=data, method=self.command,
                                     headers={"Content-Type": "application/json",
                                              "Cookie": self.headers.get("Cookie", "")})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                self.send_response(r.status)
                if r.headers.get("Set-Cookie"):
                    self.send_header("Set-Cookie", r.headers["Set-Cookie"])
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:  # noqa: BLE001 - surfaced to browser for diagnosis
            msg = f'{{"error": {str(e)!r}}}'.encode()
            self.send_response(502)
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            if self.path != "/" and not (REPO / "frontend" / "dist" / self.path.lstrip("/")).exists():
                self.path = "/"
            super().do_GET()

    def do_POST(self):
        self._proxy()

    def do_PATCH(self):
        self._proxy()

    def log_message(self, *a):
        pass


def wait(url: str, tries: int = 60) -> None:
    for _ in range(tries):
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"never came up: {url}")


def _refs(snapshot: str) -> dict:
    """Map textbox placeholder / button label to @eN ref from a compact snapshot."""
    import re
    out: dict[str, str] = {}
    for m in re.finditer(r'textbox "([^"]+)" \[ref=(e\d+)\]', snapshot):
        out[m.group(1)] = "@" + m.group(2)
    for m in re.finditer(r'button "([^"]+)" \[ref=(e\d+)\]', snapshot):
        out[m.group(1) + "_button"] = "@" + m.group(2)
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-port", type=int, default=8001)
    ap.add_argument("--signin", action="store_true",
                    help="complete the login flow in the browser and capture the overview")
    ap.add_argument("--walk", action="store_true",
                    help="after signin, visit every module route and verify its heading (full E2E)")
    a = ap.parse_args()
    global API_PORT
    API_PORT = a.api_port
    env = dict(os.environ)
    env.setdefault("SCI_ADMIN_USER", "admin")
    env.setdefault("SCI_ADMIN_PASSWORD", "change-me")
    api = subprocess.Popen([str(REPO / ".venv" / "bin" / "uvicorn"), "api.main:app",
                            "--port", str(API_PORT)], cwd=str(REPO), env=env)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", WEB_PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        wait(f"http://127.0.0.1:{API_PORT}/api/health")
        base = f"http://127.0.0.1:{WEB_PORT}"
        subprocess.run(["agent-browser", "open", base + "/"], check=True)
        snap = subprocess.run(["agent-browser", "snapshot", "-i", "-c"], check=True,
                              capture_output=True, text=True)
        print(snap.stdout[-2000:])
        subprocess.run(["agent-browser", "screenshot", str(REPO / "reports" / "web-login.png")], check=True)
        if a.signin:
            refs = _refs(snap.stdout)
            subprocess.run(["agent-browser", "fill", refs["Username"], "admin"], check=True)
            subprocess.run(["agent-browser", "fill", refs["Password"], "change-me"], check=True)
            subprocess.run(["agent-browser", "click", refs["Sign in_button"]], check=True)
            subprocess.run(["agent-browser", "wait", "--text", "Executive overview", "--timeout", "10000"],
                           check=True)
            subprocess.run(["agent-browser", "snapshot", "-i", "-c"], check=True)
            subprocess.run(["agent-browser", "screenshot", str(REPO / "reports" / "web-overview.png")],
                           check=True)
            print("signed in, overview captured")
        if a.walk:
            if not a.signin:
                raise SystemExit("--walk requires --signin")
            routes = ["/inventory", "/suppliers", "/logistics", "/forecasts", "/risks",
                      "/recommendations", "/sources", "/etl", "/quality", "/alerts", "/admin"]
            for route in routes:
                subprocess.run(["agent-browser", "open", base + route], check=True)
                subprocess.run(["agent-browser", "wait", "--load", "networkidle"], check=True)
                snap = subprocess.run(["agent-browser", "snapshot", "-i", "-c"], check=True,
                                      capture_output=True, text=True)
                assert "<h1>" in snap.stdout or "heading" in snap.stdout, route
                print(f"walk ok {route}")
            print(f"walked {len(routes)} module routes")
        print("done. Serve in your own browser at", base)
    finally:
        srv.shutdown()
        api.terminate()


if __name__ == "__main__":
    main()
