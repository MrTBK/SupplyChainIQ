"""F3 gate: component/chart library contract — exports exist, tokens only, no new deps."""

import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"

COMPONENTS = ["Button", "Input", "Select", "Badge", "Card", "KpiCard", "PageHeader",
              "EmptyState", "Skeleton", "TableSkeleton", "Alert", "Pagination",
              "DataTable", "Modal", "Toasts", "toneFor"]
CHARTS = ["LineChart", "BarChart", "Sparkline"]


def test_components_exported():
    text = (SRC / "components.jsx").read_text()
    for name in COMPONENTS:
        assert re.search(rf"(export function {name}|export (const|let|var) {name})", text), name


def test_charts_exported_with_a11y():
    text = (SRC / "charts.jsx").read_text()
    for name in CHARTS:
        assert f"export function {name}" in text, name
    assert text.count('role="img"') >= 3
    assert "<title>" in text


def test_no_hardcoded_colors_outside_tokens():
    theme = (SRC / "theme.css").read_text()
    assert ":root" in theme
    # pages.jsx migrates in F5/F6; everything else must already be token-clean
    for f in ["components.jsx", "charts.jsx", "icons.jsx", "Shell.jsx", "Login.jsx",
              "hooks.jsx", "main.jsx", "tokens.js"]:
        text = (SRC / f).read_text()
        if f == "tokens.js":
            continue  # the single sanctioned JS mirror (parity enforced below)
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", text), f
    for f in ["shell.css", "components.css"]:
        text = (SRC / f).read_text()
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", text), f
    assert "rgb(" in (SRC / "shell.css").read_text()  # scrims only, documented exception


def test_token_mirror_parity():
    css = (SRC / "theme.css").read_text()
    js = (SRC / "tokens.js").read_text()
    pairs = {
        "--primary": "primary", "--primary-hover": "primaryHover",
        "--primary-muted": "primaryMuted", "--secondary": "secondary",
        "--accent": "accent", "--success": "success", "--warning": "warning",
        "--danger": "danger", "--info": "info", "--background": "background",
        "--border": "grid", "--text-muted": "textMuted",
    }
    for css_var, js_key in pairs.items():
        css_val = re.search(rf"{re.escape(css_var)}\s*:\s*(#[0-9a-fA-F]{{6}})", css).group(1).lower()
        js_val = re.search(rf"{js_key}\s*:\s*'(#[0-9a-fA-F]{{6}})'", js).group(1).lower()
        assert css_val == js_val, (css_var, css_val, js_val)


def test_no_new_dependencies():
    pkg = json.loads((SRC.parent / "package.json").read_text())
    assert set(pkg["dependencies"]) == {"react", "react-dom", "react-router-dom"}, pkg["dependencies"]
