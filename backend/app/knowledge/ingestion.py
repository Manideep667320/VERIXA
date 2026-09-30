"""Knowledge ingestion — document loading, chunking, and embedding into ChromaDB.

Chunks markdown documents by header sections, preserves doc_id / section /
line-range metadata, and persists to a local ChromaDB collection. Idempotent:
deletes and re-creates the collection on each run.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import chromadb

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KNOWLEDGE_DIR_NAME = "knowledge"
_CHROMA_DIR_NAME = "chroma_db"
_COLLECTION_NAME = "enterprise_knowledge"

# Sub-folders inside data/knowledge/ and the doc-type tag for each
_SUBDIRS: dict[str, str] = {
    "sops": "SOP",
    "manuals": "MANUAL",
    "policies": "POLICY",
    "incidents": "INCIDENT",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DocumentChunk:
    """One section-level chunk of a markdown document."""

    chunk_id: str
    doc_id: str
    source_file: str
    doc_type: str
    section: str
    start_line: int
    end_line: int
    text: str
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DOC_ID_RE = re.compile(
    r"\*\*Document ID:\*\*\s*(\S+)"
    r"|"
    r"\*\*Incident ID:\*\*\s*(\S+)"
    r"|"
    r"\*\*Product:\*\*\s*(.+)"
)
_DOCUMENT_SECTION_RE = re.compile(r"(?m)(?=^# (?:SOP|MAN|POL|INC)-)")
_VERSION_RE = re.compile(r"\*\*Version:\*\*\s*v?([\w.-]+)", re.IGNORECASE)
_EFFECTIVE_DATE_RE = re.compile(
    r"\*\*(?:Effective Date|Published|Date):\*\*\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE
)


def _extract_doc_id(text: str, filename: str) -> str:
    """Pull the document / incident ID from the front-matter block."""
    for m in _DOC_ID_RE.finditer(text[:600]):
        for g in m.groups():
            if g:
                return g.strip()
    # Fallback: derive from filename  (e.g. SOP-042-overheating-response.md → SOP-042)
    stem = Path(filename).stem
    parts = stem.split("-", 2)
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return stem


def _stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _document_metadata(raw: str, fallback_id: str) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    sections = [section for section in _DOCUMENT_SECTION_RE.split(raw) if section.strip()]
    for section in sections:
        doc_id = _extract_doc_id(section, fallback_id)
        version = _VERSION_RE.search(section)
        effective_date = _EFFECTIVE_DATE_RE.search(section)
        metadata[doc_id] = {
            "version": version.group(1) if version else "",
            "effective_date": effective_date.group(1) if effective_date else "",
        }
    return metadata


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def _chunk_markdown(
    raw: str,
    source_file: str,
    doc_type: str,
) -> list[DocumentChunk]:
    """Split a markdown document into chunks by top-level ``#`` / ``##`` headers.

    Each chunk keeps:
    - The header hierarchy (section name)
    - The line range in the original file
    - The full document ID pulled from front-matter
    """
    lines = raw.splitlines()
    doc_id = _extract_doc_id(raw, source_file)
    metadata_by_id = _document_metadata(raw, doc_id)

    # For the incidents file we have multiple docs separated by `---` and `# INC-*`
    # We'll handle them as separate logical documents inside the same file.

    chunks: list[DocumentChunk] = []
    current_section = "Preamble"
    current_lines: list[str] = []
    section_start = 1
    active_doc_id = doc_id

    for idx, line in enumerate(lines, start=1):
        # Detect a new top-level incident header inside a combined file
        if line.startswith("# INC-") or line.startswith("# MAN-") or line.startswith("# SOP-") or line.startswith("# POL-"):
            # Flush previous chunk
            if current_lines:
                _flush_chunk(
                    chunks, current_lines, active_doc_id, source_file,
                    doc_type, current_section, section_start, idx - 1,
                )
            # Extract the new doc ID from the header line
            header_text = line.lstrip("# ").strip()
            # e.g. "INC-2024-0031: PX-100 Thermal …"
            colon_pos = header_text.find(":")
            if colon_pos > 0:
                active_doc_id = header_text[:colon_pos].strip()
            else:
                active_doc_id = header_text.split()[0] if header_text else doc_id
            current_section = header_text
            current_lines = [line]
            section_start = idx

        elif line.startswith("## "):
            # Flush previous chunk
            if current_lines:
                _flush_chunk(
                    chunks, current_lines, active_doc_id, source_file,
                    doc_type, current_section, section_start, idx - 1,
                )
            current_section = line.lstrip("# ").strip()
            current_lines = [line]
            section_start = idx

        else:
            current_lines.append(line)

    # Flush final chunk
    if current_lines:
        _flush_chunk(
            chunks, current_lines, active_doc_id, source_file,
            doc_type, current_section, section_start, len(lines),
        )

    for chunk in chunks:
        chunk.metadata = metadata_by_id.get(chunk.doc_id, metadata_by_id.get(doc_id, {}))
    return chunks


def _flush_chunk(
    out: list[DocumentChunk],
    lines: list[str],
    doc_id: str,
    source_file: str,
    doc_type: str,
    section: str,
    start_line: int,
    end_line: int,
) -> None:
    text = "\n".join(lines).strip()
    if not text:
        return
    chunk_id = f"{doc_id}::{section}::{start_line}-{end_line}"
    out.append(
        DocumentChunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            source_file=source_file,
            doc_type=doc_type,
            section=section,
            start_line=start_line,
            end_line=end_line,
            text=text,
        )
    )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_documents(data_dir: Path) -> list[DocumentChunk]:
    """Load and chunk all markdown documents from ``data_dir/knowledge/``."""
    knowledge_dir = data_dir / _KNOWLEDGE_DIR_NAME
    all_chunks: list[DocumentChunk] = []

    for subdir_name, doc_type in _SUBDIRS.items():
        subdir = knowledge_dir / subdir_name
        if not subdir.is_dir():
            continue
        for md_file in sorted(subdir.glob("*.md")):
            raw = md_file.read_text(encoding="utf-8")
            rel_path = str(md_file.relative_to(data_dir))
            chunks = _chunk_markdown(raw, rel_path, doc_type)
            all_chunks.extend(chunks)

    return all_chunks


# ---------------------------------------------------------------------------
# ChromaDB persistence
# ---------------------------------------------------------------------------


def _get_chroma_client(persist_dir: Path) -> chromadb.ClientAPI:
    persist_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_dir))


def embed_and_store(
    chunks: list[DocumentChunk],
    persist_dir: Path,
    collection_name: str = _COLLECTION_NAME,
) -> int:
    """Embed chunks and upsert into a ChromaDB collection.

    Uses ChromaDB's built-in default embedding function (all-MiniLM-L6-v2)
    so we don't need an API key for local dev.

    Returns the number of chunks stored.
    """
    client = _get_chroma_client(persist_dir)

    # Idempotent: delete existing, re-create
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    if not chunks:
        return 0

    # ChromaDB add() accepts batches — process in groups of 100
    batch_size = 100
    stored = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.add(
            ids=[c.chunk_id for c in batch],
            documents=[c.text for c in batch],
            metadatas=[
                {
                    "doc_id": c.doc_id,
                    "source_file": c.source_file,
                    "doc_type": c.doc_type,
                    "section": c.section,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    **{key: value for key, value in c.metadata.items() if value},
                }
                for c in batch
            ],
        )
        stored += len(batch)

    return stored


# ---------------------------------------------------------------------------
# Public orchestrator
# ---------------------------------------------------------------------------


def _resolve_data_dir() -> Path:
    """Return the project-level ``data/`` directory."""
    return Path(__file__).resolve().parent.parent.parent.parent / "data"


def ingest_all(
    data_dir: Path | None = None,
    persist_dir: Path | None = None,
) -> dict:
    """Run the full ingestion pipeline. Idempotent.

    Returns a dict with ``total_documents`` and ``total_chunks``.
    """
    if data_dir is None:
        data_dir = _resolve_data_dir()
    if persist_dir is None:
        persist_dir = Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db"

    chunks = load_documents(data_dir)

    # Deduplicate by chunk_id (handles re-runs)
    seen: set[str] = set()
    unique: list[DocumentChunk] = []
    for c in chunks:
        if c.chunk_id not in seen:
            seen.add(c.chunk_id)
            unique.append(c)

    stored = embed_and_store(unique, persist_dir)

    doc_ids = {c.doc_id for c in unique}
    return {
        "total_documents": len(doc_ids),
        "total_chunks": stored,
        "document_ids": sorted(doc_ids),
    }
