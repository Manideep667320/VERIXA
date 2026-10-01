"""Cross-cutting backend regression audit for Phase 3 control behavior."""

from __future__ import annotations

import inspect

import pytest

from app.agent.graph import run_agent
from app.audit import logger as audit_logger
from app.core.constants import AutonomyDecision
from app.llm.provider import LLMProvider
from app.models.schemas import ActionContract, PolicyResult
from app.policy.engine import decide_autonomy, evaluate_policy


from app.policy.loader import DEFAULT_RULES_PATH, parse_policy_rules


@pytest.mark.parametrize(
    ("confidence", "amount", "action_type", "has_evidence", "conflicting", "expected"),
    [
        (0.69, 0, "create_service_ticket", True, False, AutonomyDecision.ESCALATE),
        (0.70, 0, "create_service_ticket", True, False, AutonomyDecision.EXECUTE),
        (0.90, 4999, "create_service_ticket", True, False, AutonomyDecision.EXECUTE),
        (0.90, 5000, "create_service_ticket", True, False, AutonomyDecision.EXECUTE),
        (0.90, 5001, "create_service_ticket", True, False, AutonomyDecision.APPROVAL_REQUIRED),
        (0.90, 0, "replace_product", True, False, AutonomyDecision.APPROVAL_REQUIRED),
        (0.90, 0, "create_service_ticket", False, False, AutonomyDecision.ESCALATE),
        (0.90, 0, "create_service_ticket", True, True, AutonomyDecision.ESCALATE),
    ],
)
def test_policy_decision_boundaries(confidence, amount, action_type, has_evidence, conflicting, expected):
    rules = parse_policy_rules(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))
    action = ActionContract(action_type=action_type)
    policy = evaluate_policy(action, rules=rules)
    decision = decide_autonomy(
        policy,
        confidence,
        has_evidence=has_evidence,
        conflicting_evidence=conflicting,
        amount=amount,
        rules=rules,
    )
    assert decision == expected


class InvalidJsonLLM(LLMProvider):
    def __init__(self):
        self.calls = 0

    async def generate(self, prompt: str, system: str = "") -> str:
        raise NotImplementedError

    async def structured_output(self, prompt: str, schema: dict, system: str = "") -> dict:
        self.calls += 1
        return "{invalid json"


async def test_agent_retries_invalid_json_once_then_fails_safely():
    llm = InvalidJsonLLM()
    state = await run_agent("Open a service ticket", llm=llm, retriever=lambda _: [])
    assert llm.calls == 2
    assert state.autonomy_decision == AutonomyDecision.ESCALATE
    assert state.error


def test_audit_logger_exposes_no_update_or_delete_method():
    public_functions = {
        name for name, value in inspect.getmembers(audit_logger, inspect.isfunction)
        if not name.startswith("_")
    }
    assert not any(name.startswith(("update", "delete")) for name in public_functions)
    assert "log_run" in public_functions
    assert "get_run_audit" in public_functions
