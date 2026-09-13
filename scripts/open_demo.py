"""Serve reports/demo.html and verify it in a real browser via agent-browser (one foreground process)."""

from __future__ import annotations

import functools
import http.server
import subprocess
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PORT = 8765


def main() -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(REPO))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    url = f"http://127.0.0.1:{PORT}/reports/demo.html"
    try:
        subprocess.run(["agent-browser", "open", url], check=True)
        subprocess.run(["agent-browser", "snapshot", "-i", "-c"], check=True)
        out = REPO / "reports" / "demo-screenshot.png"
        subprocess.run(["agent-browser", "screenshot", str(out)], check=True)
        print(f"served {url} -> screenshot {out}")
    finally:
        srv.shutdown()


if __name__ == "__main__":
    main()
