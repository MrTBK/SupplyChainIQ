"""Task 0.1 smoke test: repo scaffold is importable and plan file exists."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_plan_file_exists():
    assert (REPO / "docs" / "PROJECT_PLAN.md").exists()


def test_config_example_exists():
    assert (REPO / "config" / ".env.example").exists()


def test_no_real_env_committed():
    assert not (REPO / "config" / ".env").exists()
