"""Validation gates for citation-grounded chatbot responses."""

from __future__ import annotations

import json
import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.chat.help import HelpEvidence

NO_DOCUMENTATION_RESPONSE = "I don't have documentation on that"
_HELP_ID = re.compile(r"\bHELP-[A-Z0-9-]+\b")
_KNOWLEDGE_ID = re.compile(r"\b(?:POL|SOP|MAN|INC)-[A-Z0-9-]+\b", re.IGNORECASE)
_RUN_ID = re.compile(r"\bRUN-[A-Z0-9-]+\b", re.IGNORECASE)
_NUMBER = re.compile(r"(?<![A-Za-z0-9])\$?\d[\d,]*(?:\.\d+)?%?")


class ChatIntent(StrEnum):
    DATA = "DATA"
    CONCEPT = "CONCEPT"
    MIXED = "MIXED"
    ACTION = "ACTION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class ChatAnswerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    help_ids: list[str] = Field(default_factory=list)
    knowledge_ids: list[str] = Field(default_factory=list)
    run_ids: list[str] = Field(default_factory=list)


def _numbers(text: str) -> set[str]:
    return {match.group().replace("$", "").replace(",", "").replace("%", "") for match in _NUMBER.finditer(text)}


def validate_chat_answer(
    output: ChatAnswerOutput,
    *,
    intent: ChatIntent,
    help_sources: list[HelpEvidence],
    knowledge_sources: list[dict[str, Any]] | None = None,
    data_sources: list[dict[str, Any]],
) -> ChatAnswerOutput:
    """Reject fabricated citations and unsupported numeric/data claims."""
    allowed_help_ids = {source.help_id for source in help_sources}
    knowledge_sources = knowledge_sources or []
    allowed_knowledge_ids = {str(source.get("id", "")) for source in knowledge_sources}
    cited_help_ids = set(output.help_ids) | set(_HELP_ID.findall(output.answer))
    cited_knowledge_ids = {
        item.upper() for item in output.knowledge_ids
    } | {item.upper() for item in _KNOWLEDGE_ID.findall(output.answer)}
    invalid_help_ids = cited_help_ids - allowed_help_ids
    invalid_knowledge_ids = cited_knowledge_ids - {item.upper() for item in allowed_knowledge_ids}
    if invalid_help_ids:
        raise ValueError(f"Chat response cited help IDs that were not retrieved: {', '.join(sorted(invalid_help_ids))}")
    if invalid_knowledge_ids:
        raise ValueError(
            "Chat response cited knowledge IDs that were not retrieved: "
            + ", ".join(sorted(invalid_knowledge_ids))
        )

    actual_run_ids = {str(source.get("run_id", "")) for source in data_sources if source.get("run_id")}
    cited_run_ids = set(output.run_ids) | set(_RUN_ID.findall(output.answer))
    invalid_run_ids = cited_run_ids - actual_run_ids
    if invalid_run_ids:
        raise ValueError(f"Chat response cited run IDs that were not retrieved for this tenant: {', '.join(sorted(invalid_run_ids))}")

    if intent == ChatIntent.CONCEPT:
        relevant_sources = [
            source.confidence for source in help_sources
        ] + [
            float(source.get("relevance_score", 0))
            for source in knowledge_sources
        ]
        if not relevant_sources or max(relevant_sources) < 0.70:
            return ChatAnswerOutput(answer=NO_DOCUMENTATION_RESPONSE)
        if not cited_help_ids and not cited_knowledge_ids:
            raise ValueError("Concept answers must cite at least one retrieved source")
        if cited_run_ids:
            raise ValueError("Concept answers cannot cite audit run IDs")

    if intent in {ChatIntent.DATA, ChatIntent.MIXED}:
        source_text = json.dumps(data_sources, ensure_ascii=False, sort_keys=True)
        if intent == ChatIntent.MIXED:
            source_text += " " + " ".join(source.content for source in help_sources)
        unsupported_numbers = _numbers(output.answer) - _numbers(source_text)
        if unsupported_numbers:
            raise ValueError(f"Chat response contains numbers absent from retrieved sources: {', '.join(sorted(unsupported_numbers))}")
        if not cited_run_ids:
            raise ValueError(f"{intent.value} answers must cite at least one retrieved run ID")
        if intent == ChatIntent.MIXED and help_sources and max(source.confidence for source in help_sources) >= 0.70:
            if not cited_help_ids:
                raise ValueError("Mixed answers with relevant help must cite at least one retrieved HELP-ID")

    return output
