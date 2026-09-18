"""Risk <-> recommendation linkage: stable IDs + bidirectional navigation keys.

IDs are derived from kind+entity only (never quantities/dates), so they are
stable across evaluations and double as lifecycle keys (Phase 19).
"""

from __future__ import annotations


def risk_id(r: dict) -> str:
    slug = r["entity_id"].replace("@", "-").replace("->", "-").replace(":", "-")
    return f"RSK-{r['kind']}-{slug}"


def rec_id(r: dict) -> str:
    slug = r["entity_id"].replace("@", "-").replace("->", "-").replace(":", "-")
    return f"REC-{r['kind']}-{slug}"


def _transfer_endpoints(entity_id: str) -> tuple[str, str]:
    """'P:A->B' -> (product, deficit_warehouse)."""
    pid, lanes = entity_id.split(":", 1)
    _, deficit = lanes.split("->", 1)
    return pid, deficit


def link(risks: list[dict], recs: list[dict]) -> tuple[list[dict], list[dict]]:
    by_entity: dict[str, list[dict]] = {}
    for rec in recs:
        rec["id"] = rec_id(rec)
        by_entity.setdefault(rec["entity_id"], []).append(rec)
    # transfer recs also index under the deficit product-warehouse risk entity
    for rec in recs:
        if rec["kind"] == "transfer":
            try:
                pid, deficit = _transfer_endpoints(rec["entity_id"])
            except ValueError:
                continue
            by_entity.setdefault(f"{pid}@{deficit}", []).append(rec)
    # supplier recs (entity 'P@S') also index under their supplier risk entity
    for rec in recs:
        if rec["kind"] == "supplier" and "@" in rec["entity_id"]:
            sid = rec["entity_id"].split("@", 1)[1]
            by_entity.setdefault(sid, []).append(rec)

    for risk in risks:
        risk["id"] = risk_id(risk)
        matched = by_entity.get(risk["entity_id"], [])
        # supplier degradation risks match supplier recs indexed above
        risk["rec_ids"] = [m["id"] for m in matched]
        for m in matched:
            m.setdefault("risk_ids", [])
            if risk["id"] not in m["risk_ids"]:
                m["risk_ids"].append(risk["id"])
    for rec in recs:
        rec.setdefault("risk_ids", [])
    return risks, recs
