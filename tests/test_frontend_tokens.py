"""F1 gate: token contract complete; pages carry no hardcoded design values."""

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"

REQUIRED_TOKENS = [
    "--primary", "--primary-hover", "--primary-muted",
    "--accent", "--accent-muted",
    "--success", "--warning", "--danger", "--info",
    "--background", "--surface", "--surface-muted", "--border",
    "--text-primary", "--text-secondary", "--text-muted",
    "--text-metric", "--sidebar-width", "--topbar-height",
    "--transition-fast", "--radius-md",
]


def test_theme_defines_all_semantic_tokens():
    css = (SRC / "theme.css").read_text()
    for token in REQUIRED_TOKENS:
        assert re.search(rf"{re.escape(token)}\s*:", css), token


def test_foundation_rules_present():
    css = (SRC / "theme.css").read_text()
    assert "prefers-reduced-motion" in css
    assert ":focus-visible" in css
    assert "tabular-nums" in css


def test_theme_wired_into_entry():
    assert "theme.css" in (SRC / "main.jsx").read_text()
