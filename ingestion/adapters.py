"""Source adapters: CSV/Excel/API-stub → staging contract (Phase 3 interface).

v1 implements CsvAdapter (used by generator output). ExcelAdapter/APIStubAdapter
share the interface so future ERP/WMS/TMS sources plug in without warehouse rebuild.
"""

from __future__ import annotations

import csv
from pathlib import Path


class CsvAdapter:
    source_system = "csv"

    def discover(self, root: Path) -> list[Path]:
        return sorted(root.glob("*.csv"))

    def read(self, f: Path) -> list[dict]:
        with f.open() as fh:
            return list(csv.DictReader(fh))

    def to_staging(self, rows: list[dict], batch_id: str) -> tuple[list[dict], list[dict]]:
        accepted, rejected = [], []
        for r in rows:
            if any(v is None or v == "" for v in r.values()):
                rejected.append({"rule_id": "R01", "row": r})
            else:
                accepted.append({**r, "_batch_id": batch_id, "_source": self.source_system})
        return accepted, rejected
