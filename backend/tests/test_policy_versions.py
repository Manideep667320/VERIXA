"""Versioned policy validation, API, and offline replay tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.policy import (
    PolicySimulationRequest,
    PolicyWriteRequest,
    create_policy_version,
    get_policy_versions,
    run_policy_simulation,
)
from app.main import app
from app.core import database
from app.models.schemas import ActionContract
from app.policy import loader
from app.policy.engine import evaluate_actions


@pytest.fixture
def policy_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "DEFAULT_RULES_PATH", Path(__file__).resolve().parents[1] / "app" / "policy" / "rules.yaml")
    monkeypatch.setattr(loader, "VERSIONS_DIR", tmp_path / "policy-versions")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "policy-runs.sqlite")
    database.init_db()
    return tmp_path


def _candidate_rules(amount_threshold: int):
    rules = loader.load_active_rules().model_dump(mode="json")
    rules["approval_amount_threshold"] = amount_threshold
    return rules


async def test_policy_api_validates_and_saves_new_immutable_version(policy_storage):
    source_path = loader.DEFAULT_RULES_PATH
    original = source_path.read_text(encoding="utf-8")
    saved = await create_policy_version(PolicyWriteRequest(candidate_rules=_candidate_rules(3000)))
    assert saved["version"] == 2
    assert loader.load_active_rules().version == 2
    assert source_path.read_text(encoding="utf-8") == original
    versions = await get_policy_versions()
    assert versions["active_version"] == 2
    assert [version["version"] for version in versions["versions"]] == [1, 2]


async def test_invalid_yaml_is_rejected_without_creating_a_version(policy_storage):
    with pytest.raises(HTTPException) as raised:
        await create_policy_version(PolicyWriteRequest(candidate_rules="version: [broken"))
    assert raised.value.status_code == 422
    assert not loader.VERSIONS_DIR.exists()


async def test_candidate_threshold_replay_returns_only_changed_runs(policy_storage):
    with database.get_db() as conn:
        for run_id, amount in (("RUN-3500", 3500), ("RUN-2500", 2500)):
            action = {
                "id": f"ACT-{amount}",
                "action_type": "create_service_ticket",
                "arguments": {"amount": amount},
                "evidence_ids": ["SOP-042"],
            }
            conn.execute(
                """INSERT INTO runs(id, request, reasoning, evidence, proposed_actions, autonomy_decision)
                   VALUES (?, ?, ?, ?, ?, 'EXECUTE')""",
                (run_id, "Create a service ticket", json.dumps({"confidence": 0.9,
                 "conflicting_evidence": False}), json.dumps([{"id": "SOP-042", "text": "Evidence"}]),
                 json.dumps([action])),
            )
    result = await run_policy_simulation(PolicySimulationRequest(
        candidate_rules=_candidate_rules(3000), last_n=10))
    assert result["policy_version"] == 1
    assert result["checked_runs"] == 2
    assert result["changed_decisions"] == [{"run_id": "RUN-3500", "old": "EXECUTE",
                                             "new": "APPROVAL_REQUIRED", "policy_version": 1}]


def test_default_rules_preserve_scenario_decisions(policy_storage):
    rules = loader.load_active_rules()
    low_risk = evaluate_actions(
        [_action("create_service_ticket")], 0.91, has_evidence=True, rules=rules)
    approval = evaluate_actions(
        [_action("replace_product", amount=6000)], 0.88, has_evidence=True, rules=rules)
    uncertain = evaluate_actions(
        [_action("replace_product")], 0.95, has_evidence=False, conflicting_evidence=True, rules=rules)
    assert low_risk.decision == "EXECUTE"
    assert approval.decision == "APPROVAL_REQUIRED"
    assert uncertain.decision == "ESCALATE"
    assert low_risk.policy_version == rules.version


def _action(action_type: str, amount: int | None = None):
    arguments = {"amount": amount} if amount is not None else {}
    return ActionContract(action_type=action_type, arguments=arguments)


def test_policy_routes_are_registered_on_api_router():
    paths = set(app.openapi()["paths"])
    assert "/api/policy" in paths
    assert "/api/policy/versions" in paths
    assert "/api/policy/simulate" in paths
