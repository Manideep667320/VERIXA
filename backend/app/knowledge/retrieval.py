"""Knowledge retrieval — vector search with metadata filtering.

Returns typed ``EvidenceItem`` objects with confidence scores, source files,
and line citations. Results are deduplicated by ``doc_id`` — only the
highest-scoring chunk per document is returned.
"""

from __future__ import annotations

from pathlib import Path

import chromadb

from app.core.constants import DocumentType
from app.knowledge.conflicts import scan_knowledge_conflicts
from app.models.schemas import EvidenceItem

# ---------------------------------------------------------------------------
# Constants (must match ingestion.py)
# ---------------------------------------------------------------------------

_COLLECTION_NAME = "enterprise_knowledge"

# How many raw candidates to fetch before deduplication
_CANDIDATES_MULTIPLIER = 6

# Map doc_type strings to DocumentType enum
_DOC_TYPE_MAP: dict[str, DocumentType] = {
    "SOP": DocumentType.SOP,
    "MANUAL": DocumentType.MANUAL,
    "POLICY": DocumentType.POLICY,
    "INCIDENT": DocumentType.INCIDENT,
}

# Document type boost factors for diagnostic/error queries
# Boost SOPs and MANUALs over INCIDENTS for technical queries
_DOC_TYPE_BOOST: dict[str, float] = {
    "SOP": 1.30,
    "MANUAL": 1.50,
    "POLICY": 1.10,
    # Historical cases provide context, but cannot establish authoritative
    # action guidance on their own. Keep their confidence below the 0.70 gate.
    "INCIDENT": 0.69,
}


# ---------------------------------------------------------------------------
# ChromaDB client helper
# ---------------------------------------------------------------------------


def _default_persist_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db"


def _get_collection(
    persist_dir: Path | None = None,
    collection_name: str = _COLLECTION_NAME,
) -> chromadb.Collection:
    if persist_dir is None:
        persist_dir = _default_persist_dir()
    client = chromadb.PersistentClient(path=str(persist_dir))
    return client.get_collection(name=collection_name)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def retrieve(
    query: str,
    top_k: int = 5,
    doc_type_filter: str | None = None,
    persist_dir: Path | None = None,
) -> list[EvidenceItem]:
    """Semantic similarity search against the knowledge base.

    Results are **deduplicated by doc_id** — when multiple chunks from the
    same document match, only the highest-scoring chunk is kept.  This
    ensures result diversity (e.g. an SOP and a manual both appear rather
    than five chunks from the same incident).

    Parameters
    ----------
    query:
        Natural-language search string.
    top_k:
        Maximum number of *unique-document* results to return.
    doc_type_filter:
        Optional — restrict to a specific ``DocumentType`` value
        (``"SOP"``, ``"MANUAL"``, ``"POLICY"``, ``"INCIDENT"``).
    persist_dir:
        Override for the ChromaDB persistence directory (mainly for tests).

    Returns
    -------
    list[EvidenceItem]
        Results ranked by relevance, each carrying a ``relevance_score``
        between 0.0 and 1.0 (1.0 = perfect match).
    """
    collection = _get_collection(persist_dir)

    where_filter = None
    if doc_type_filter:
        where_filter = {"doc_type": doc_type_filter}

    # Fetch extra candidates so deduplication still yields top_k results
    n_candidates = min(top_k * _CANDIDATES_MULTIPLIER, collection.count())
    n_candidates = max(n_candidates, top_k)

    results = collection.query(
        query_texts=[query],
        n_results=n_candidates,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    if not results or not results["ids"] or not results["ids"][0]:
        return []

    conflict_report = scan_knowledge_conflicts()
    conflicts_by_document: dict[str, list[dict]] = {}
    for conflict in conflict_report.conflicts:
        rendered = conflict.model_dump(mode="json")
        conflicts_by_document.setdefault(conflict.document_a, []).append(rendered)
        conflicts_by_document.setdefault(conflict.document_b, []).append(rendered)
    stale_by_document = {item.document_id: item.model_dump(mode="json")
                         for item in conflict_report.stale_documents}

    ids = results["ids"][0]
    documents = results["documents"][0] if results["documents"] else [""] * len(ids)
    metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
    distances = results["distances"][0] if results["distances"] else [1.0] * len(ids)

    # Build all items, then deduplicate by doc_id (keep highest score)
    all_items: list[EvidenceItem] = []
    for i, chunk_id in enumerate(ids):
        meta = metadatas[i] or {}
        distance = distances[i]

        # ChromaDB cosine distance is in [0, 2]; convert to similarity in [0, 1]
        similarity = max(0.0, 1.0 - distance)

        doc_type_str = meta.get("doc_type", "SOP")
        doc_type_enum = _DOC_TYPE_MAP.get(doc_type_str, DocumentType.SOP)

        # Apply document type boost for diagnostic queries
        boost = _DOC_TYPE_BOOST.get(doc_type_str, 1.0)
        boosted_similarity = min(1.0, similarity * boost)

        start_line = meta.get("start_line", 0)
        end_line = meta.get("end_line", 0)

        all_items.append(
            EvidenceItem(
                id=meta.get("doc_id", chunk_id),
                source=meta.get("source_file", ""),
                section=meta.get("section", ""),
                text=documents[i],
                relevance_score=round(boosted_similarity, 4),
                document_type=doc_type_enum,
                metadata={
                    "chunk_id": chunk_id,
                    "start_line": start_line,
                    "end_line": end_line,
                    "lines": f"L{start_line}-L{end_line}",
                    "raw_similarity": round(similarity, 4),
                    "boost_factor": boost,
                    "version": meta.get("version", ""),
                    "effective_date": meta.get("effective_date", ""),
                    "conflict_warning": bool(conflicts_by_document.get(meta.get("doc_id", chunk_id))),
                    "conflicts": conflicts_by_document.get(meta.get("doc_id", chunk_id), []),
                    "stale_warning": meta.get("doc_id", chunk_id) in stale_by_document,
                    "stale_document": stale_by_document.get(meta.get("doc_id", chunk_id)),
                },
            )
        )

    # Sort descending by relevance (highest first)
    all_items.sort(key=lambda e: e.relevance_score, reverse=True)

    # Deduplicate: keep only the first (highest-scoring) chunk per doc_id
    seen_doc_ids: set[str] = set()
    unique_items: list[EvidenceItem] = []
    for item in all_items:
        if item.id not in seen_doc_ids:
            seen_doc_ids.add(item.id)
            unique_items.append(item)
        if len(unique_items) >= top_k:
            break

    return unique_items


def retrieve_above_threshold(
    query: str,
    threshold: float = 0.70,
    top_k: int = 10,
    doc_type_filter: str | None = None,
    persist_dir: Path | None = None,
) -> list[EvidenceItem]:
    """Retrieve only results whose confidence meets or exceeds ``threshold``.

    Parameters
    ----------
    doc_type_filter:
        Optional — restrict to a specific document type before thresholding.
    """
    all_results = retrieve(
        query, top_k=top_k, doc_type_filter=doc_type_filter, persist_dir=persist_dir,
    )
    return [r for r in all_results if r.relevance_score >= threshold]
