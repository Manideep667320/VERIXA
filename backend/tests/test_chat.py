"""Behavioral coverage for the tenant-scoped help and audit chatbot."""

from __future__ import annotations

import re

import pytest

from app.audit.logger import get_run_audits, log_run
from app.audit.verify_chain import verify_chain
from app.api.router import api_router
from app.chat.agent import run_chat_turn
from app.chat.help import HelpEvidence, render_help_documents, retrieve_help
from app.chat.validator import ChatAnswerOutput, ChatIntent, validate_chat_answer
from app.core import database
from app.core.constants import AutonomyDecision
from app.llm.provider import LLMProvider
from app.models.schemas import EvidenceItem


class MockLLM(LLMProvider):
    def __init__(self, *outputs):
        self.outputs = list(outputs)

    async def generate(self, prompt: str, system: str = "") -> str:
        raise AssertionError("chat uses structured model output")

    async def structured_output(self, prompt: str, schema: dict, system: str = "") -> dict:
        return self.outputs.pop(0)


@pytest.fixture(autouse=True)
def use_chat_database(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "chat.sqlite")


def _help(help_id: str, confidence: float = 0.91, text: str = "Audit row hash information") -> HelpEvidence:
    return HelpEvidence(
        help_id=help_id,
        title=help_id,
        content=text,
        confidence=confidence,
        tenant_id="public",
    )


async def test_row_hash_concept_cites_retrieved_help_and_is_audited():
    llm = MockLLM(
        {"intent": "CONCEPT", "search_query": "row_hash", "run_id": None},
        {"answer": "row_hash is the SHA-256 digest of a canonical audit row.",
         "help_ids": ["HELP-HASH-CHAIN"], "run_ids": []},
    )
    response = await run_chat_turn(
        "What does row_hash mean?", tenant_id="tenant-a", llm=llm,
        help_retriever=lambda *_args, **_kwargs: [_help("HELP-HASH-CHAIN")],
    )

    assert response.intent == ChatIntent.CONCEPT
    assert response.sources.help_ids == ["HELP-HASH-CHAIN"]
    assert verify_chain().valid
    assert len(get_run_audits()) == 1
    assert get_run_audits()[0].snapshot["tenant_id"] == "tenant-a"


async def test_concept_can_answer_from_enterprise_policy_documents():
    llm = MockLLM(
        {"intent": "CONCEPT", "search_query": "warranty coverage PX-100", "run_id": None},
        {
            "answer": "The PX-100 warranty terms are defined by POL-WTY-001.",
            "help_ids": [],
            "knowledge_ids": ["POL-WTY-001"],
            "run_ids": [],
        },
    )
    response = await run_chat_turn(
        "What does the warranty policy say about the PX-100?",
        tenant_id="tenant-a",
        llm=llm,
        help_retriever=lambda *_args, **_kwargs: [],
        knowledge_retriever=lambda *_args, **_kwargs: [
            EvidenceItem(
                id="POL-WTY-001",
                source="policies/POL-WTY-001-warranty.md",
                text="PX-100 coverage terms.",
                relevance_score=0.91,
            )
        ],
    )

    assert response.intent == ChatIntent.CONCEPT
    assert response.sources.knowledge_ids == ["POL-WTY-001"]


async def test_mixed_audit_question_uses_tenant_run_and_help_sources():
    log_run(
        run_id="RUN-42", prompt="A service request", evidence_ids=[], policy_rule="test",
        decision=AutonomyDecision.EXECUTE.value, actions=[], verification=[],
        snapshot={"tenant_id": "tenant-a", "request": "A service request"},
    )
    llm = MockLLM(
        {"intent": "MIXED", "search_query": "audit row fields", "run_id": "RUN-42"},
        {"answer": "RUN-42 records an EXECUTE decision.",
         "help_ids": ["HELP-AUDIT-FIELDS"], "run_ids": ["RUN-42"]},
    )
    response = await run_chat_turn(
        "Explain RUN-42's audit row.", tenant_id="tenant-a", llm=llm,
        help_retriever=lambda *_args, **_kwargs: [_help("HELP-AUDIT-FIELDS")],
    )

    assert response.intent == ChatIntent.MIXED
    assert response.sources.run_ids == ["RUN-42"]
    assert response.sources.help_ids == ["HELP-AUDIT-FIELDS"]
    assert verify_chain().valid
    assert len(get_run_audits()) == 2


async def test_concept_without_relevant_document_returns_fixed_no_documentation_reply():
    llm = MockLLM({"intent": "CONCEPT", "search_query": "weather tomorrow", "run_id": None})
    response = await run_chat_turn(
        "What will the weather be tomorrow?", tenant_id="tenant-a", llm=llm,
        help_retriever=lambda *_args, **_kwargs: [_help("HELP-GLOSSARY", confidence=0.41)],
    )

    assert response.answer == "I don't have documentation on that"
    assert response.sources.help_ids == []
    assert verify_chain().valid
    assert len(get_run_audits()) == 1


async def test_fabricated_help_id_is_rejected_and_failed_turn_is_audited():
    llm = MockLLM(
        {"intent": "CONCEPT", "search_query": "row_hash", "run_id": None},
        {"answer": "The value is documented in HELP-FAKE.", "help_ids": ["HELP-FAKE"], "run_ids": []},
    )
    with pytest.raises(ValueError, match="not retrieved"):
        await run_chat_turn(
            "What does row_hash mean?", tenant_id="tenant-a", llm=llm,
            help_retriever=lambda *_args, **_kwargs: [_help("HELP-HASH-CHAIN")],
        )

    records = get_run_audits()
    assert len(records) == 1
    assert records[0].decision == "CONCEPT:FAILED"
    assert verify_chain().valid


async def test_run_audit_from_another_tenant_is_not_returned():
    log_run(
        run_id="RUN-PRIVATE", prompt="Private request", evidence_ids=[], policy_rule="test",
        decision=AutonomyDecision.EXECUTE.value, actions=[], verification=[],
        snapshot={"tenant_id": "tenant-b"},
    )
    llm = MockLLM({"intent": "DATA", "search_query": "audit row", "run_id": "RUN-PRIVATE"})
    response = await run_chat_turn(
        "Show RUN-PRIVATE", tenant_id="tenant-a", llm=llm,
    )

    assert response.answer == "I can't access that run in this tenant."
    assert response.sources.run_ids == []
    assert verify_chain().valid


def test_help_audit_field_list_matches_live_audit_table_columns():
    document = next(item for item in render_help_documents() if item.id == "HELP-AUDIT-FIELDS")
    documented = re.findall(r"^- `([^`]+)` \(", document.content, flags=re.MULTILINE)
    with database.get_db() as conn:
        actual = [row["name"] for row in conn.execute("PRAGMA table_info(run_audit)")]

    assert documented == actual


def test_help_retrieval_filters_to_public_and_requesting_tenant(monkeypatch):
    class FakeCollection:
        def count(self):
            return 8

        def query(self, **kwargs):
            assert kwargs["n_results"] == 3
            assert kwargs["where"] == {"$or": [{"tenant_id": "public"}, {"tenant_id": "tenant-a"}]}
            return {"ids": [["HELP-AUDIT-FIELDS"]], "documents": [["Audit fields"]],
                    "metadatas": [[{"help_id": "HELP-AUDIT-FIELDS", "title": "Audit fields",
                                    "tenant_id": "public"}]], "distances": [[0.1]]}

    monkeypatch.setattr("app.chat.help._collection", lambda *_args, **_kwargs: FakeCollection())
    results = retrieve_help("audit columns", tenant_id="tenant-a")
    assert len(results) == 1
    assert results[0].help_id == "HELP-AUDIT-FIELDS"


def test_help_retrieval_boosts_clear_lexical_matches_above_concept_threshold(monkeypatch):
    class FakeCollection:
        def count(self):
            return 8

        def query(self, **kwargs):
            return {
                "ids": [["HELP-HASH-CHAIN"]],
                "documents": [["Audit-chain tamper detection recomputes each row hash and checks links."]],
                "metadatas": [[{"help_id": "HELP-HASH-CHAIN", "title": "Hash chain", "tenant_id": "public"}]],
                "distances": [[0.339]],
            }

    monkeypatch.setattr("app.chat.help._collection", lambda *_args, **_kwargs: FakeCollection())
    results = retrieve_help("audit-chain tamper detection", tenant_id="tenant-a")

    assert results[0].confidence >= 0.70


def test_data_and_mixed_answers_reject_unbacked_numbers():
    with pytest.raises(ValueError, match="numbers absent"):
        validate_chat_answer(
            ChatAnswerOutput(answer="RUN-42 processed 999 tickets", run_ids=["RUN-42"]),
            intent=ChatIntent.DATA,
            help_sources=[],
            data_sources=[{"run_id": "RUN-42", "decision": "EXECUTE", "ticket_count": 2}],
        )


def test_chat_turn_route_is_registered_with_tenant_header():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(api_router)
    operation = app.openapi()["paths"]["/api/chat/turn"]["post"]
    assert any(parameter["name"] == "X-Tenant-ID" and parameter["in"] == "header"
               for parameter in operation["parameters"])
