"""Tenant-scoped help and audit chat service."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.audit.logger import RunAuditRecord, get_run_audit, log_run
from app.chat.help import HelpEvidence, retrieve_help
from app.chat.validator import ChatAnswerOutput, ChatIntent, NO_DOCUMENTATION_RESPONSE, validate_chat_answer
from app.llm.provider import LLMProvider, get_llm
from app.knowledge.retrieval import retrieve as retrieve_knowledge

_RUN_ID = re.compile(r"\bRUN-[A-Z0-9-]+\b", re.IGNORECASE)
_HELP_ID = re.compile(r"\bHELP-[A-Z0-9-]+\b")


class ChatIntentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: ChatIntent
    search_query: str = ""
    run_id: str | None = None


class ChatSources(BaseModel):
    model_config = ConfigDict(extra="forbid")

    help_ids: list[str] = Field(default_factory=list)
    knowledge_ids: list[str] = Field(default_factory=list)
    run_ids: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_id: str
    thread_id: str
    tenant_id: str
    intent: ChatIntent
    answer: str
    sources: ChatSources


HelpRetriever = Callable[..., list[HelpEvidence]]
KnowledgeRetriever = Callable[..., list[Any]]
AuditLookup = Callable[[str], RunAuditRecord | None]


def _knowledge_id(source: Any) -> str:
    return str(source.id if hasattr(source, "id") else source.get("id", ""))

_INTENT_PROMPT = """Classify the user message into exactly one chat intent.
DATA: answer from a tenant-owned audit/run record only.
CONCEPT: answer a documented business or project question using retrieved documents.
MIXED: the user needs both a tenant-owned run/audit lookup and help documentation.
ACTION: asks the system to perform an action or change data.
OUT_OF_SCOPE: unrelated or unsupported by project help and audit records.
If a run ID such as RUN-ABC is present and the request asks about it, return it in run_id.
Return schema-valid JSON only.

User message:
{message}"""

_ANSWER_PROMPT = """Answer the user using only the supplied sources. Do not infer facts that are absent.
For each cited help page, include its exact HELP-ID in help_ids. For each enterprise document,
include its exact document ID in knowledge_ids. For each audit record used,
include its exact run_id in run_ids. A concept response must cite at least one retrieved source.
Return schema-valid JSON only.

User message:
{message}

Help sources:
{help_sources}

Enterprise knowledge sources:
{knowledge_sources}

Tenant-authorized audit sources:
{data_sources}"""


def _tenant_audit_lookup(run_id: str, tenant_id: str) -> RunAuditRecord | None:
    """Read an audit row only when its immutable input snapshot names this tenant."""
    record = get_run_audit(run_id)
    if record is None or record.snapshot.get("tenant_id") != tenant_id:
        return None
    return record


async def run_chat_turn(
    message: str,
    *,
    tenant_id: str,
    thread_id: str | None = None,
    llm: LLMProvider | None = None,
    help_retriever: HelpRetriever = retrieve_help,
    knowledge_retriever: KnowledgeRetriever = retrieve_knowledge,
    audit_lookup: AuditLookup | None = None,
) -> ChatResponse:
    """Classify, retrieve tenant-scoped data/help, validate the answer, and append an audit turn."""
    normalized_tenant = tenant_id.strip()
    if not normalized_tenant:
        raise ValueError("tenant_id is required")
    if not message.strip():
        raise ValueError("message is required")

    turn_id = f"CHAT-{uuid4().hex.upper()}"
    conversation_id = thread_id or turn_id
    lookup = audit_lookup or (lambda run_id: _tenant_audit_lookup(run_id, normalized_tenant))
    intent = ChatIntent.OUT_OF_SCOPE
    help_sources: list[HelpEvidence] = []
    knowledge_sources: list[Any] = []
    data_sources: list[dict] = []
    tool_trace: list[dict] = []

    try:
        provider = llm or get_llm()
        parsed_intent = await provider.structured_model(
            _INTENT_PROMPT.format(message=message), ChatIntentOutput,
            system="You classify requests for a read-only, tenant-scoped enterprise help chatbot.",
        )
        intent = parsed_intent.intent
        requested_run_ids = {run_id.upper() for run_id in _RUN_ID.findall(message)}
        selected_run_id = parsed_intent.run_id.upper() if parsed_intent.run_id else (
            next(iter(requested_run_ids)) if requested_run_ids else None
        )
        if selected_run_id and selected_run_id not in requested_run_ids:
            raise ValueError("Classifier selected a run ID that was not present in the user message")

        if intent in {ChatIntent.ACTION, ChatIntent.OUT_OF_SCOPE}:
            answer = (
                "I can explain project documentation and tenant-authorized audit records, "
                "but I can't perform actions or answer unrelated requests."
            )
            response = ChatResponse(
                turn_id=turn_id, thread_id=conversation_id, tenant_id=normalized_tenant,
                intent=intent, answer=answer, sources=ChatSources(),
            )
            _log_turn(response, message, help_sources, knowledge_sources, data_sources, tool_trace)
            return response

        if intent in {ChatIntent.DATA, ChatIntent.MIXED}:
            if selected_run_id is None:
                answer = "I can't access an audit run unless you provide its RUN-ID."
                response = ChatResponse(
                    turn_id=turn_id, thread_id=conversation_id, tenant_id=normalized_tenant,
                    intent=intent, answer=answer, sources=ChatSources(),
                )
                _log_turn(response, message, help_sources, knowledge_sources, data_sources, tool_trace)
                return response
            record = lookup(selected_run_id)
            if record is None:
                tool_trace.append({"tool": "get_run_audit", "run_id": selected_run_id, "result": "not_found_or_not_owned"})
                answer = "I can't access that run in this tenant."
                response = ChatResponse(
                    turn_id=turn_id, thread_id=conversation_id, tenant_id=normalized_tenant,
                    intent=intent, answer=answer, sources=ChatSources(),
                )
                _log_turn(response, message, help_sources, knowledge_sources, data_sources, tool_trace)
                return response
            data_sources = [record.model_dump(mode="json")]
            tool_trace.append({"tool": "get_run_audit", "run_id": record.run_id, "result": "found"})

        if intent in {ChatIntent.CONCEPT, ChatIntent.MIXED}:
            query = parsed_intent.search_query.strip() or message
            help_sources = help_retriever(query, tenant_id=normalized_tenant, top_k=3)
            try:
                knowledge_sources = knowledge_retriever(query, top_k=5)
            except (FileNotFoundError, ValueError):
                knowledge_sources = []
            if intent == ChatIntent.CONCEPT and (
                not help_sources and not knowledge_sources
            ):
                response = ChatResponse(
                    turn_id=turn_id, thread_id=conversation_id, tenant_id=normalized_tenant,
                    intent=intent, answer=NO_DOCUMENTATION_RESPONSE, sources=ChatSources(),
                )
                _log_turn(response, message, help_sources, knowledge_sources, data_sources, tool_trace)
                return response
            relevant_scores = [
                source.confidence for source in help_sources
            ] + [
                source.relevance_score for source in knowledge_sources
            ]
            if intent == ChatIntent.CONCEPT and (
                not relevant_scores or max(relevant_scores) < 0.70
            ):
                response = ChatResponse(
                    turn_id=turn_id, thread_id=conversation_id, tenant_id=normalized_tenant,
                    intent=intent, answer=NO_DOCUMENTATION_RESPONSE, sources=ChatSources(),
                )
                _log_turn(response, message, help_sources, knowledge_sources, data_sources, tool_trace)
                return response

        generated = await provider.structured_model(
            _ANSWER_PROMPT.format(
                message=message,
                help_sources=json.dumps([source.model_dump(mode="json") for source in help_sources], ensure_ascii=False),
                knowledge_sources=json.dumps(
                    [source.model_dump(mode="json") for source in knowledge_sources],
                    ensure_ascii=False,
                ),
                data_sources=json.dumps(data_sources, ensure_ascii=False),
            ),
            ChatAnswerOutput,
            system="Answer only from provided sources. Never invent citations, numeric facts, or run IDs.",
        )
        valid_answer = validate_chat_answer(
            generated, intent=intent, help_sources=help_sources,
            knowledge_sources=[source.model_dump(mode="json") for source in knowledge_sources],
            data_sources=data_sources,
        )
        help_ids = sorted(set(valid_answer.help_ids) | set(_HELP_ID.findall(valid_answer.answer)))
        knowledge_ids = sorted(
            set(valid_answer.knowledge_ids)
            | {item.upper() for item in re.findall(r"\b(?:POL|SOP|MAN|INC)-[A-Z0-9-]+\b", valid_answer.answer, re.IGNORECASE)}
        )
        run_ids = sorted(set(valid_answer.run_ids) | set(_RUN_ID.findall(valid_answer.answer)))
        response = ChatResponse(
            turn_id=turn_id, thread_id=conversation_id, tenant_id=normalized_tenant,
            intent=intent, answer=valid_answer.answer,
            sources=ChatSources(help_ids=help_ids, knowledge_ids=knowledge_ids, run_ids=run_ids),
        )
        _log_turn(response, message, help_sources, knowledge_sources, data_sources, tool_trace)
        return response
    except Exception as exc:
        _log_failed_turn(
            turn_id=turn_id, thread_id=conversation_id, tenant_id=normalized_tenant,
            message=message, intent=intent, error=str(exc), help_sources=help_sources,
            knowledge_sources=knowledge_sources, data_sources=data_sources, tool_trace=tool_trace,
        )
        raise


def _log_turn(
    response: ChatResponse,
    message: str,
    help_sources: list[HelpEvidence],
    knowledge_sources: list[Any],
    data_sources: list[dict],
    tool_trace: list[dict],
) -> None:
    evidence_ids = sorted(set(
        response.sources.help_ids + response.sources.knowledge_ids + response.sources.run_ids
    ))
    log_run(
        run_id=response.turn_id,
        prompt=message,
        evidence_ids=evidence_ids,
        policy_rule="CHAT_READ_ONLY",
        decision=response.intent.value,
        actions=tool_trace,
        verification=[],
        snapshot={
            "tenant_id": response.tenant_id,
            "thread_id": response.thread_id,
            "intent": response.intent.value,
            "answer": response.answer,
            "help_ids": [source.help_id for source in help_sources],
            "knowledge_ids": [_knowledge_id(source) for source in knowledge_sources],
            "data_run_ids": [source.get("run_id") for source in data_sources],
            "sources": response.sources.model_dump(),
        },
    )


def _log_failed_turn(
    *, turn_id: str, thread_id: str, tenant_id: str, message: str, intent: ChatIntent,
    error: str, help_sources: list[HelpEvidence], knowledge_sources: list[Any],
    data_sources: list[dict], tool_trace: list[dict],
) -> None:
    log_run(
        run_id=turn_id,
        prompt=message,
        evidence_ids=sorted({source.help_id for source in help_sources} |
                            {_knowledge_id(source) for source in knowledge_sources} |
                            {str(source.get("run_id")) for source in data_sources if source.get("run_id")}),
        policy_rule="CHAT_READ_ONLY",
        decision=f"{intent.value}:FAILED",
        actions=tool_trace,
        verification=[],
        snapshot={
            "tenant_id": tenant_id,
            "thread_id": thread_id,
            "intent": intent.value,
            "error": error,
            "help_ids": [source.help_id for source in help_sources],
            "knowledge_ids": [_knowledge_id(source) for source in knowledge_sources],
            "data_run_ids": [source.get("run_id") for source in data_sources],
        },
    )
