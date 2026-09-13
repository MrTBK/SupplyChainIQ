"""Phase 1 gate: requirements doc exists, trace complete, no orphans."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "business_requirements.md"


def test_requirements_doc_exists():
    assert DOC.exists()


def test_functional_requirements_present():
    t = DOC.read_text()
    for fr in ["FR-01", "FR-02", "FR-03", "FR-04", "FR-05", "FR-06", "FR-07"]:
        assert fr in t


def test_trace_has_no_orphans():
    t = DOC.read_text()
    assert "Zero orphan questions" in t
    # every domain represented
    for kw in ["Inventory Value", "Supplier OTIF", "On-Time Delivery", "Reorder Qty"]:
        assert kw in t


def test_nfr_explicit():
    t = DOC.read_text()
    assert "Idempotency" in t and "Reproducibility" in t
