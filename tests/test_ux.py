"""14.22 gate: static UX contract for operational UI (hierarchy, labels, tables)."""

from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"


def test_every_page_has_heading_and_purpose():
    pages = (SRC / "pages.jsx").read_text()
    for name in ["Overview", "Inventory", "Suppliers", "Logistics", "Forecasts", "Risks",
                 "Recommendations", "Sources", "Etl", "Quality", "Alerts", "Admin"]:
        assert f"export function {name}" in pages, name
    assert pages.count("<h1>") >= 12


def test_tables_accessible_and_scrollable():
    hooks = (SRC / "hooks.jsx").read_text()
    assert 'scope="col"' in hooks
    assert "overflowX" in hooks


def test_inputs_labelled():
    for f in ["Login.jsx", "pages.jsx"]:
        text = (SRC / f).read_text()
        for line in text.splitlines():
            if "<input" in line:
                assert "aria-label" in line, (f, line.strip()[:60])


def test_no_decorative_excess():
    for f in ["main.jsx", "pages.jsx", "Login.jsx", "hooks.jsx", "App.jsx"]:
        p = SRC / f
        if not p.exists():
            continue
        text = p.read_text().lower()
        for bad in ["linear-gradient", "box-shadow", "animation", "keyframes"]:
            assert bad not in text, (f, bad)


def test_security_ux_contract():
    api = (SRC / "api.js").read_text()
    assert "body.error" in api and "ApiError" in api  # envelope parsed, status typed
    assert "localStorage" not in api and "sessionStorage" not in api  # no token storage
    assert "X-CSRF-Token" in api
    hooks = (SRC / "hooks.jsx").read_text()
    assert "ErrorBoundary" in hooks and "NotFound" in hooks and "403" in hooks
    main = (SRC / "main.jsx").read_text()
    assert 'path="*"' in main  # unknown routes render 404, never blank
    login = (SRC / "Login.jsx").read_text()
    assert "disabled={busy}" in login and "Show" in login  # loading + visibility toggle
    for f in ["api.js", "hooks.jsx", "pages.jsx", "Login.jsx", "main.jsx"]:
        assert "console.log" not in (SRC / f).read_text(), f  # no response leakage to console
