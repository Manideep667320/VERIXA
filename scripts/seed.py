"""Seed script — populates the knowledge base and mock enterprise data.

Generates seed markdown documents to data/knowledge/, writes customer and
technician JSON to data/, and runs the ingestion pipeline to populate ChromaDB.
Idempotent: safe to run multiple times.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.knowledge.ingestion import ingest_all  # noqa: E402


def verify_seed_data() -> bool:
    """Check that all expected seed files exist."""
    data_dir = PROJECT_ROOT / "data"
    knowledge_dir = data_dir / "knowledge"

    expected_sops = [
        "SOP-042-overheating-response.md",
        "SOP-018-equipment-failure.md",
        "SOP-055-technician-dispatch.md",
        "SOP-071-critical-escalation.md",
        "SOP-089-sensor-calibration.md",
    ]
    expected_manuals = [
        "MAN-PX100-industrial-chiller.md",
        "MAN-PY200-hvac-unit.md",
    ]
    expected_policies = [
        "POL-WTY-001-warranty.md",
        "POL-EQP-002-equipment-replacement.md",
        "POL-SLA-003-dispatch-sla.md",
        "POL-RFD-004-refunds.md",
        "POL-NTF-005-notifications.md",
    ]
    expected_incidents = ["historical-incidents.md"]

    all_ok = True
    for fname in expected_sops:
        p = knowledge_dir / "sops" / fname
        if not p.exists():
            print(f"  MISSING: {p}")
            all_ok = False
    for fname in expected_manuals:
        p = knowledge_dir / "manuals" / fname
        if not p.exists():
            print(f"  MISSING: {p}")
            all_ok = False
    for fname in expected_policies:
        p = knowledge_dir / "policies" / fname
        if not p.exists():
            print(f"  MISSING: {p}")
            all_ok = False
    for fname in expected_incidents:
        p = knowledge_dir / "incidents" / fname
        if not p.exists():
            print(f"  MISSING: {p}")
            all_ok = False

    # JSON data
    for jf in ["customers.json", "technicians.json"]:
        p = data_dir / jf
        if not p.exists():
            print(f"  MISSING: {p}")
            all_ok = False
        else:
            with open(p) as f:
                records = json.load(f)
            print(f"  {jf}: {len(records)} records")

    return all_ok


def main() -> None:
    print("=" * 60)
    print("VERIXA — Phase 2 Seed & Ingest")
    print("=" * 60)

    # Step 1: Verify static seed files are present
    print("\n[1/3] Verifying seed data files...")
    if not verify_seed_data():
        print("\n[ERROR] Seed data files missing. Ensure data/knowledge/ is populated.")
        sys.exit(1)
    print("[OK] All seed data files present.")

    # Step 2: Run the ingestion pipeline
    print("\n[2/3] Running ingestion pipeline...")
    stats = ingest_all()
    print(f"[OK] Ingested {stats['total_chunks']} chunks from {stats['total_documents']} documents.")

    # Step 3: Quick retrieval sanity check
    print("\n[3/3] Running retrieval sanity check...")
    from app.knowledge.retrieval import retrieve  # noqa: E402

    results = retrieve("Product X overheating error E-401", top_k=5)
    doc_ids_found = [r.id for r in results]
    print(f"  Query: 'Product X overheating error E-401'")
    print(f"  Top results: {doc_ids_found}")
    for r in results:
        print(f"    {r.id} | score={r.relevance_score:.3f} | {r.source}")

    has_sop042 = any("SOP-042" in r.id for r in results[:3])
    has_man_px100 = any("MAN-PX100" in r.id for r in results[:3])

    if has_sop042 and has_man_px100:
        print("[OK] Retrieval test PASSED: SOP-042 and MAN-PX100 in top 3.")
    else:
        print("[WARN] Retrieval test WARNING: Expected SOP-042 and MAN-PX100 in top 3.")
        print(f"    Got: {[r.id for r in results[:3]]}")

    print("\n" + "=" * 60)
    print("Seed & ingest complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
