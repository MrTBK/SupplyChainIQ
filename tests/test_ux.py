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
