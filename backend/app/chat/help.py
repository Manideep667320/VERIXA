"""Help-document ingestion and retrieval in a tenant-filtered Chroma collection."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import chromadb
from pydantic import BaseModel, ConfigDict, Field

from app.agent.shadow import RunMode
from app.audit.logger import get_run_audits
from app.core import database
from app.core.constants import AutonomyDecision
from app.core.database import get_db
from app.knowledge.embedding import get_embedding_function
from app.policy.loader import load_active_rules

HELP_COLLECTION = "help"
HELP_DOCS_DIR = Path(__file__).resolve().parent / "help_docs"
_TOKEN = re.compile(r"[a-z0-9_]+", re.IGNORECASE)
_STOP_WORDS = {
    "a", "an", "and", "does", "explain", "how", "is", "mean", "of", "the",
    "to", "what", "work",
}


class HelpDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    content: str
    tenant_id: str = "public"


class HelpEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    help_id: str
    title: str
    content: str
    confidence: float = Field(ge=0, le=1)
    tenant_id: str


def _audit_field_lines() -> str:
    # Ensure the Phase 7 migration has run before reading the live table shape.
    get_run_audits()
    with get_db() as conn:
        columns = conn.execute("PRAGMA table_info(run_audit)").fetchall()
    if not columns:
        raise RuntimeError("The audit table has no columns")
    descriptions = {
        "run_id": "Unique identifier for the audited run.",
        "prompt": "Original request that started the run.",
        "evidence_ids": "Identifiers of the evidence retrieved for the decision.",
        "policy_rule": "Policy rule or rules evaluated for the run.",
        "decision": "Final deterministic autonomy decision.",
        "actions": "Actions attempted, their results, and any compensations.",
        "verification": "Independent read-back results for actions and rollback.",
        "timestamp": "UTC time when the row was appended.",
        "sequence": "Append order used to verify chain continuity.",
        "snapshot": "Input and agent-state snapshot retained for review or replay.",
        "prev_hash": "Previous row's hash, or the fixed genesis hash for the first row.",
        "row_hash": "SHA-256 of canonical JSON for this row, including prev_hash.",
    }
    unknown = [column["name"] for column in columns if column["name"] not in descriptions]
    if unknown:
        raise RuntimeError(f"Add help text for new audit fields: {', '.join(unknown)}")
    return "\n".join(
        f"- `{column['name']}` ({column['type'] or 'unspecified'}): {descriptions[column['name']]}"
        for column in columns
    )


def _decision_lines() -> str:
    descriptions = {
        AutonomyDecision.EXECUTE: "Policy and evidence permit the action to execute.",
        AutonomyDecision.APPROVAL_REQUIRED: "A human must approve before execution.",
        AutonomyDecision.ESCALATE: "Evidence or policy requires human handling; no autonomous action proceeds.",
    }
    return "\n".join(f"- **{decision.value}** — {descriptions[decision]}" for decision in AutonomyDecision)


def _policy_action_lines() -> str:
    rules = load_active_rules()
    lines = [
        f"- Confidence threshold: {rules.confidence_threshold:g}.",
        f"- Approval amount threshold: {rules.approval_amount_threshold:g}.",
        "- Approval risk levels: " + ", ".join(sorted(level.value for level in rules.approval_risk_levels)) + ".",
        "- Action rules:",
    ]
    for name, rule in sorted(rules.actions.items()):
        approval = "approval required" if rule.requires_approval else "no fixed approval requirement"
        if rule.requires_approval_above is not None:
            approval += f"; approval above {rule.requires_approval_above:g}"
        lines.append(
            f"- `{name}`: {'allowed' if rule.allowed else 'denied'}, "
            f"{rule.risk_level.value} risk, {approval}."
        )
    return "\n".join(lines)


def _mode_lines() -> str:
    descriptions = {
        RunMode.SHADOW: "Runs the pipeline and saves recommendations, while blocking tool writes.",
        RunMode.SUPERVISED: "Requires a human decision before gated actions execute.",
        RunMode.AUTONOMOUS: "Executes actions only when evidence and policy permit them.",
    }
    return "\n".join(f"- **{mode.value}** — {descriptions[mode]}" for mode in RunMode)


def render_help_documents(docs_dir: Path | None = None) -> list[HelpDocument]:
    """Render markdown help pages, deriving volatile lists from application state."""
    source_dir = docs_dir or HELP_DOCS_DIR
    replacements = {
        "{{AUDIT_FIELDS}}": _audit_field_lines(),
        "{{DECISION_TYPES}}": _decision_lines(),
        "{{POLICY_ACTIONS}}": _policy_action_lines(),
        "{{WORKFLOW_MODES}}": _mode_lines(),
    }
    rendered: list[HelpDocument] = []
    for path in sorted(source_dir.glob("HELP-*.md")):
        document_id = path.stem
        if not document_id.startswith("HELP-"):
            continue
        content = path.read_text(encoding="utf-8")
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        if "{{" in content:
            raise ValueError(f"Unresolved generated content marker in {path.name}")
        title = content.splitlines()[0].removeprefix("# ").strip()
        rendered.append(HelpDocument(id=document_id, title=title, content=content))
    return rendered


def _collection(persist_dir: Path | None = None) -> Any:
    path = persist_dir or database.DB_PATH.parent / "chroma_db"
    client = chromadb.PersistentClient(path=str(path))
    return client.get_or_create_collection(
        name=HELP_COLLECTION,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def ingest_help_docs(*, persist_dir: Path | None = None, docs_dir: Path | None = None) -> int:
    """Upsert generated help pages into the separate `help` collection."""
    documents = render_help_documents(docs_dir)
    collection = _collection(persist_dir)
    if documents:
        collection.upsert(
            ids=[item.id for item in documents],
            documents=[item.content for item in documents],
            metadatas=[{"help_id": item.id, "title": item.title, "tenant_id": item.tenant_id}
                       for item in documents],
        )
    return len(documents)


def retrieve_help(
    query: str,
    *,
    tenant_id: str,
    top_k: int = 3,
    persist_dir: Path | None = None,
) -> list[HelpEvidence]:
    """Return up to three relevant public or tenant-owned help pages."""
    if not tenant_id.strip():
        raise ValueError("tenant_id is required for help retrieval")
    if top_k < 1:
        return []
    collection = _collection(persist_dir)
    if collection.count() == 0:
        ingest_help_docs(persist_dir=persist_dir)
        collection = _collection(persist_dir)
    result = collection.query(
        query_texts=[query],
        n_results=min(top_k, 3, collection.count()),
        where={"$or": [{"tenant_id": "public"}, {"tenant_id": tenant_id}]},
        include=["documents", "metadatas", "distances"],
    )
    if not result.get("ids") or not result["ids"][0]:
        return []
    evidence = []
    documents = result.get("documents", [[]])[0] or []
    metadatas = result.get("metadatas", [[]])[0] or []
    distances = result.get("distances", [[]])[0] or []
    for index, identifier in enumerate(result["ids"][0]):
        metadata = metadatas[index] or {}
        distance = float(distances[index]) if index < len(distances) else 1.0
        content = documents[index] if index < len(documents) else ""
        confidence = max(0.0, min(1.0, 1.0 - distance))
        query_terms = {
            token.lower() for token in _TOKEN.findall(query)
            if token.lower() not in _STOP_WORDS
        }
        content_terms = {token.lower() for token in _TOKEN.findall(content)}
        if query_terms:
            lexical_match = len(query_terms & content_terms) / len(query_terms)
            if len(query_terms) <= 4 and len(query_terms & content_terms) >= 2:
                confidence = max(confidence, 0.70 + (0.20 * lexical_match))
        evidence.append(HelpEvidence(
            help_id=metadata.get("help_id", identifier),
            title=metadata.get("title", identifier),
            content=content,
            confidence=confidence,
            tenant_id=metadata.get("tenant_id", "public"),
        ))
    return evidence
