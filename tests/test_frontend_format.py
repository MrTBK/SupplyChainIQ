"""Productization gate: shared format layer exists and pages use it (no raw decimals/enums)."""

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"

REQUIRED_FORMATS = [
    "formatPercent", "formatNumber", "formatCompact", "formatCurrency",
    "formatDate", "formatDateTime", "formatStatus", "formatRiskType",
    "formatEntity", "humanize",
]


def test_format_lib_exports():
    text = (SRC / "lib" / "format.js").read_text()
    for name in REQUIRED_FORMATS:
        assert re.search(rf"export function {name}\b", text), name


def test_pages_use_format_layer():
    text = (SRC / "pages.jsx").read_text()
    assert "from './lib/format.js'" in text
    for name in ["formatPercent", "formatEntity", "formatStatus", "formatRiskType"]:
        assert name in text, name
    # no raw OTIF decimals rendered directly
    assert "v.toFixed(2)" not in text
    assert "k.procurement_otif}" not in text or "formatPercent(k.procurement_otif" in text


def test_charts_never_undefined_title():
    text = (SRC / "charts.jsx").read_text()
    assert "title = 'Series'" in text or 'title ||' in text
    assert 'aria-label={`${title}: line chart`}' not in text or "title = " in text


def test_severity_status_tones_exist():
    text = (SRC / "components.jsx").read_text()
    assert "severityTone" in text
    assert "statusTone" in text
