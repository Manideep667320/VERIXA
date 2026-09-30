"""Detect contradictory versioned document facts and documents past review age."""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


_DOCUMENT_HEADER = re.compile(r"(?m)(?=^# (?:SOP|MAN|POL|INC)-)")
_ID = re.compile(r"\*\*(?:Document ID|Incident ID):\*\*\s*(\S+)", re.IGNORECASE)
_HEADER_ID = re.compile(r"(?m)^#\s+((?:SOP|MAN|POL|INC)-[A-Z0-9-]+)")
_VERSION = re.compile(r"\*\*Version:\*\*\s*v?([\w.-]+)", re.IGNORECASE)
_EFFECTIVE_DATE = re.compile(r"\*\*(?:Effective Date|Published|Date):\*\*\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
_FACT = re.compile(r"\*\*Fact:\*\*\s*([\w.-]+)\s*=\s*([^\r\n]+)", re.IGNORECASE)


class DocumentFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str
    value: str


class KnowledgeDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    source: str
    version: str | None = None
    effective_date: date | None = None
    facts: list[DocumentFact] = Field(default_factory=list)


class DocumentConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    topic: str
    document_a: str
    value_a: str
    version_a: str | None
    document_b: str
    value_b: str
    version_b: str | None
    sources: list[str]


class StaleDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    source: str
    version: str | None
    effective_date: date
    age_days: int


class KnowledgeConflictReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conflicts: list[DocumentConflict] = Field(default_factory=list)
    stale_documents: list[StaleDocument] = Field(default_factory=list)


def scan_knowledge_conflicts(
    data_dir: Path | None = None,
    *,
    as_of: date | datetime | None = None,
    stale_after_days: int = 730,
) -> KnowledgeConflictReport:
    """Scan seed knowledge for different values on a shared fact topic and stale dates."""
    root = data_dir or Path(__file__).resolve().parents[3] / "data"
    knowledge_dir = root / "knowledge"
    today = _as_date(as_of)
    documents: list[KnowledgeDocument] = []
    for path in sorted(knowledge_dir.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        for section in _document_sections(raw):
            doc = _parse_document(section, path.relative_to(root).as_posix())
            if doc is not None:
                documents.append(doc)

    facts: dict[str, list[tuple[KnowledgeDocument, str]]] = {}
    stale: list[StaleDocument] = []
    for doc in documents:
        for fact in doc.facts:
            facts.setdefault(fact.topic.casefold(), []).append((doc, _normalize_value(fact.value)))
        if doc.effective_date is not None:
            age_days = (today - doc.effective_date).days
            if age_days > stale_after_days:
                stale.append(StaleDocument(
                    document_id=doc.document_id, source=doc.source, version=doc.version,
                    effective_date=doc.effective_date, age_days=age_days,
                ))

    conflicts: list[DocumentConflict] = []
    for topic, entries in sorted(facts.items()):
        for index, (left, left_value) in enumerate(entries):
            for right, right_value in entries[index + 1:]:
                if left.document_id == right.document_id or left_value == right_value:
                    continue
                pair_key = "|".join(sorted((left.document_id, right.document_id))) + f"|{topic}"
                conflict_id = "CON-" + hashlib.sha256(pair_key.encode()).hexdigest()[:12]
                conflicts.append(DocumentConflict(
                    id=conflict_id, topic=topic,
                    document_a=left.document_id, value_a=left_value, version_a=left.version,
                    document_b=right.document_id, value_b=right_value, version_b=right.version,
                    sources=sorted({left.source, right.source}),
                ))
    conflicts.sort(key=lambda item: (item.topic, item.document_a, item.document_b))
    stale.sort(key=lambda item: (item.effective_date, item.document_id))
    return KnowledgeConflictReport(conflicts=conflicts, stale_documents=stale)


def _as_date(value: date | datetime | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    return value.date() if isinstance(value, datetime) else value


def _document_sections(raw: str) -> list[str]:
    sections = [section.strip() for section in _DOCUMENT_HEADER.split(raw) if section.strip()]
    return sections or [raw]


def _parse_document(text: str, source: str) -> KnowledgeDocument | None:
    id_match = _ID.search(text) or _HEADER_ID.search(text)
    if not id_match:
        return None
    version_match = _VERSION.search(text)
    date_match = _EFFECTIVE_DATE.search(text)
    effective_date = date.fromisoformat(date_match.group(1)) if date_match else None
    facts = [DocumentFact(topic=match.group(1).strip().casefold(), value=match.group(2).strip())
             for match in _FACT.finditer(text)]
    return KnowledgeDocument(
        document_id=id_match.group(1).strip(), source=source,
        version=version_match.group(1) if version_match else None,
        effective_date=effective_date, facts=facts,
    )


def _normalize_value(value: str) -> str:
    return " ".join(value.strip().casefold().split())
