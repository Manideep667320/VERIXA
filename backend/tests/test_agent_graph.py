from app.agent.graph import run_agent
from app.core.constants import AutonomyDecision
from app.llm.provider import LLMProvider
from app.models.schemas import EvidenceItem


class MockLLM(LLMProvider):
    def __init__(self, intent, reasoning, plan):
        self.responses = [intent, reasoning, plan]

    async def generate(self, prompt, system=""):
        raise NotImplementedError

    async def structured_output(self, prompt, schema, system=""):
        return self.responses.pop(0)


async def _run(request, evidence, reasoning, actions):
    llm = MockLLM(
        {"request_type": "service_request", "entities": {}, "desired_outcome": "resolve", "urgency": "HIGH"},
        reasoning,
        {"actions": actions},
    )
    return await run_agent(request, llm=llm, retriever=lambda _: evidence)


async def test_scenario_a_executes_supported_low_risk_actions():
    evidence = [EvidenceItem(id="SOP-042", source="SOP-042.md", text="Overheating response")]
    state = await _run(
        "PX-100 is overheating under warranty; create a ticket and assign a technician",
        evidence,
        {"summary": "SOP supports a service ticket.", "confidence": 0.91,
         "cited_evidence_ids": ["SOP-042"], "conflicting_evidence": False, "severity": "HIGH"},
        [{"action_type": "create_service_ticket", "arguments": {}, "reason": "Document overheating",
          "evidence_ids": ["SOP-042"]},
         {"action_type": "assign_technician", "arguments": {}, "reason": "Dispatch field support",
          "evidence_ids": ["SOP-042"]}],
    )
    assert state.autonomy_decision == AutonomyDecision.EXECUTE
    assert state.stage_statuses["understanding_request"] == "complete"
    assert state.stage_statuses["retrieving_evidence"] == "complete"
    assert state.stage_statuses["reasoning"] == "complete"
    assert state.stage_statuses["preparing_action_plan"] == "complete"
    assert state.stage_statuses["evaluating_policy"] == "complete"


async def test_scenario_b_requires_approval_for_replacement_over_5000():
    evidence = [EvidenceItem(id="POL-EQP-002", source="replacement.md", text="Replacement policy")]
    state = await _run(
        "Replace the failed machine for $6000", evidence,
        {"summary": "Replacement requires approval.", "confidence": 0.88,
         "cited_evidence_ids": ["POL-EQP-002"], "conflicting_evidence": False, "severity": "HIGH"},
        [{"action_type": "replace_product", "arguments": {"amount": 6000}, "reason": "Replace failed unit",
          "evidence_ids": ["POL-EQP-002"]}],
    )
    assert state.autonomy_decision == AutonomyDecision.APPROVAL_REQUIRED


async def test_scenario_c_escalates_when_evidence_is_missing_or_conflicting():
    state = await _run(
        "Immediately replace Product Y because it is overheating", [],
        {"summary": "No matching Product Y policy was found.", "confidence": 0.95,
         "cited_evidence_ids": [], "conflicting_evidence": True, "severity": "HIGH"},
        [{"action_type": "replace_product", "arguments": {}, "reason": "Requested replacement",
          "evidence_ids": []}],
    )
    assert state.autonomy_decision == AutonomyDecision.ESCALATE
    assert state.stage_statuses["preparing_action_plan"] == "complete"
    assert state.stage_statuses["evaluating_policy"] == "complete"


async def test_llm_cannot_cite_evidence_not_returned_by_retrieval():
    evidence = [EvidenceItem(id="SOP-042", source="SOP-042.md", text="Overheating response")]
    state = await _run(
        "PX-100 is overheating", evidence,
        {"summary": "Supported.", "confidence": 0.95, "cited_evidence_ids": ["MADE-UP"],
         "conflicting_evidence": False, "severity": "MEDIUM"}, [],
    )
    assert state.autonomy_decision == AutonomyDecision.ESCALATE
    assert "not retrieved" in state.error
    assert state.stage_statuses["reasoning"] == "failed"
    assert state.stage_statuses["preparing_action_plan"] == "queued"


async def test_provider_failure_marks_only_the_stage_that_failed():
    class BrokenLLM(MockLLM):
        async def structured_output(self, prompt, schema, system=""):
            raise RuntimeError("provider unavailable")

    state = await run_agent(
        "Investigate overheating",
        llm=BrokenLLM([], {}, {}),
        retriever=lambda _: [],
    )

    assert state.failed_stage == "understanding_request"
    assert state.stage_statuses["understanding_request"] == "failed"
    assert state.stage_statuses["retrieving_evidence"] == "queued"
    assert state.stage_statuses["executing_actions"] == "queued"
    assert state.policy_result is None
    assert state.error == "provider unavailable"


async def test_provider_rate_limit_is_reported_without_upstream_payload():
    class RateLimitedError(RuntimeError):
        status_code = 429

    class BrokenLLM(MockLLM):
        async def structured_output(self, prompt, schema, system=""):
            raise RateLimitedError("provider shared-pool payload")

    state = await run_agent(
        "Investigate overheating",
        llm=BrokenLLM([], {}, {}),
        retriever=lambda _: [],
    )

    assert state.failed_stage == "understanding_request"
    assert state.error == (
        "The AI provider is temporarily rate-limited. "
        "Please retry shortly or configure a dedicated provider API key."
    )
    assert "shared-pool payload" not in state.error
