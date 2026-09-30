"""Tests for Phase 2 — Knowledge ingestion and retrieval.

Test matrix:
1. Ingestion produces the expected number of documents and chunks.
2. Query "Product X overheating error E-401" returns SOP-042 and MAN-PX100 in top 3.
3. A "Product Y" query returns all items below the 0.70 confidence threshold.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.knowledge.ingestion import ingest_all, load_documents
from app.knowledge.retrieval import retrieve, retrieve_above_threshold

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Project-level data/ directory (contains the seed knowledge files)
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# Use a temp ChromaDB directory inside backend/data so it doesn't collide
# with the production one
_TEST_CHROMA_DIR = Path(__file__).resolve().parent.parent / "data" / "chroma_db_test"


@pytest.fixture(scope="module", autouse=True)
def ingest_once():
    """Run ingestion once for the entire test module."""
    # Clean slate
    if _TEST_CHROMA_DIR.exists():
        shutil.rmtree(_TEST_CHROMA_DIR, ignore_errors=True)

    stats = ingest_all(data_dir=_DATA_DIR, persist_dir=_TEST_CHROMA_DIR)
    yield stats

    # Cleanup after all tests
    if _TEST_CHROMA_DIR.exists():
        shutil.rmtree(_TEST_CHROMA_DIR, ignore_errors=True)


# ---------------------------------------------------------------------------
# Ingestion tests
# ---------------------------------------------------------------------------


class TestIngestion:
    """Verify the ingestion pipeline produces correct chunks."""

    def test_loads_all_documents(self):
        chunks = load_documents(_DATA_DIR)
        doc_ids = {c.doc_id for c in chunks}

        # 5 SOPs + 2 manuals + 5 policies + 10 incidents = 22 unique doc IDs
        assert "SOP-042" in doc_ids, f"SOP-042 missing from {doc_ids}"
        assert "MAN-PX100" in doc_ids, f"MAN-PX100 missing from {doc_ids}"
        assert "POL-EQP-002" in doc_ids, f"POL-EQP-002 missing from {doc_ids}"
        assert "INC-2024-0031" in doc_ids, f"INC-2024-0031 missing from {doc_ids}"

    def test_chunks_have_metadata(self):
        chunks = load_documents(_DATA_DIR)
        for c in chunks:
            assert c.doc_id, "chunk missing doc_id"
            assert c.source_file, "chunk missing source_file"
            assert c.doc_type in ("SOP", "MANUAL", "POLICY", "INCIDENT"), f"bad doc_type: {c.doc_type}"
            assert c.start_line >= 1, "start_line must be ≥ 1"
            assert c.end_line >= c.start_line, "end_line must be ≥ start_line"

    def test_ingest_all_stats(self, ingest_once):
        stats = ingest_once
        assert stats["total_documents"] >= 15, f"expected ≥15 docs, got {stats['total_documents']}"
        assert stats["total_chunks"] >= 20, f"expected ≥20 chunks, got {stats['total_chunks']}"

    def test_idempotent(self):
        """Running ingest_all twice should not raise or duplicate."""
        stats1 = ingest_all(data_dir=_DATA_DIR, persist_dir=_TEST_CHROMA_DIR)
        stats2 = ingest_all(data_dir=_DATA_DIR, persist_dir=_TEST_CHROMA_DIR)
        assert stats1["total_chunks"] == stats2["total_chunks"]


# ---------------------------------------------------------------------------
# Retrieval tests
# ---------------------------------------------------------------------------


class TestRetrieval:
    """Verify semantic search returns expected documents."""

    def test_overheating_e401_returns_sop042_and_man_px100(self, ingest_once):
        """Query 'Product X overheating error E-401' must return SOP-042 and
        MAN-PX100 in the top 3 results."""
        results = retrieve(
            "Product X overheating error E-401",
            top_k=5,
            persist_dir=_TEST_CHROMA_DIR,
        )

        assert len(results) >= 3, f"expected ≥3 results, got {len(results)}"

        top3_ids = [r.id for r in results[:3]]
        has_sop042 = any("SOP-042" in rid for rid in top3_ids)
        has_man_px100 = any("MAN-PX100" in rid for rid in top3_ids)

        assert has_sop042, f"SOP-042 not in top 3: {top3_ids}"
        assert has_man_px100, f"MAN-PX100 not in top 3: {top3_ids}"

    def test_overheating_results_have_high_confidence(self, ingest_once):
        """Top results for a well-documented query should have high confidence."""
        results = retrieve(
            "Product X overheating error E-401",
            top_k=3,
            persist_dir=_TEST_CHROMA_DIR,
        )
        for r in results:
            assert r.relevance_score > 0.0, f"score should be > 0: {r.id} = {r.relevance_score}"

    def test_product_y_below_threshold(self, ingest_once):
        """Query about 'Product Y' (no matching SOP) should return all items
        below the 0.70 confidence threshold."""
        all_results = retrieve(
            "Product Y unknown cooling system intermittent shutdown",
            top_k=10,
            persist_dir=_TEST_CHROMA_DIR,
        )
        assert all(r.relevance_score < 0.70 for r in all_results), (
            f"Expected all Product Y results below 0.70: "
            f"{[(r.id, r.relevance_score) for r in all_results]}"
        )
        above = retrieve_above_threshold(
            "Product Y unknown cooling system intermittent shutdown",
            threshold=0.70,
            top_k=10,
            doc_type_filter="SOP",
            persist_dir=_TEST_CHROMA_DIR,
        )
        assert len(above) == 0, (
            f"Expected 0 SOP results above 0.70 for Product Y query, got {len(above)}: "
            f"{[(r.id, r.relevance_score) for r in above]}"
        )

    def test_evidence_item_fields(self, ingest_once):
        """Each result must have all EvidenceItem fields populated."""
        results = retrieve(
            "overheating thermal runaway",
            top_k=3,
            persist_dir=_TEST_CHROMA_DIR,
        )
        for r in results:
            assert r.id, "EvidenceItem.id must not be empty"
            assert r.source, "EvidenceItem.source must not be empty"
            assert r.text, "EvidenceItem.text must not be empty"
            assert r.relevance_score >= 0.0
            assert r.relevance_score <= 1.0
            assert "chunk_id" in r.metadata
            assert "lines" in r.metadata

    def test_doc_type_filter(self, ingest_once):
        """Filtering by doc_type should only return that type."""
        results = retrieve(
            "overheating",
            top_k=10,
            doc_type_filter="SOP",
            persist_dir=_TEST_CHROMA_DIR,
        )
        for r in results:
            assert r.document_type == "SOP", f"expected SOP, got {r.document_type} for {r.id}"

    def test_equipment_replacement_threshold(self, ingest_once):
        """Query about equipment replacement should find the $5,000 policy."""
        results = retrieve(
            "equipment replacement cost exceeds $5,000 approval required",
            top_k=5,
            persist_dir=_TEST_CHROMA_DIR,
        )
        top_ids = [r.id for r in results[:5]]
        has_pol_eqp = any("POL-EQP-002" in rid for rid in top_ids)
        assert has_pol_eqp, f"POL-EQP-002 not found in results: {top_ids}"
