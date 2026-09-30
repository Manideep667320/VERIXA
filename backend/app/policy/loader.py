"""Pydantic-validated, append-only versioned YAML policy loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.core.constants import RiskLevel

POLICY_DIR = Path(__file__).resolve().parent
DEFAULT_RULES_PATH = POLICY_DIR / "rules.yaml"
VERSIONS_DIR = POLICY_DIR / "versions"


class ActionRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    risk_level: RiskLevel
    requires_approval: bool = False
    requires_approval_above: float | None = Field(default=None, ge=0)


class ApprovalRouteRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    min_amount: float = Field(default=0, ge=0)
    max_amount: float | None = Field(default=None, gt=0)
    risk_levels: set[RiskLevel] = Field(default_factory=lambda: set(RiskLevel))
    approver_roles: list[str] = Field(min_length=1)
    priority: int = 0

    @field_validator("approver_roles")
    @classmethod
    def validate_roles(cls, roles: list[str]) -> list[str]:
        normalized = [role.strip() for role in roles]
        if any(not role for role in normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("approver_roles must contain distinct, non-empty role names")
        return normalized

    def matches(self, amount: float, risk_level: RiskLevel) -> bool:
        return (amount >= self.min_amount and (self.max_amount is None or amount < self.max_amount)
                and risk_level in self.risk_levels)


class ApprovalRoutingRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeout_seconds: int = Field(default=900, ge=1)
    human_queue: str = "human_queue"
    default_roles: list[str] = Field(default_factory=lambda: ["service_manager", "operations_director"], min_length=1)
    routes: list[ApprovalRouteRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_route_names(self):
        if not self.human_queue.strip():
            raise ValueError("human_queue cannot be empty")
        names = [route.name for route in self.routes]
        if len(set(names)) != len(names):
            raise ValueError("approval route names must be unique")
        if any(not role.strip() for role in self.default_roles):
            raise ValueError("default_roles cannot contain empty values")
        return self

    def roles_for(self, amount: float, risk_level: RiskLevel) -> list[str]:
        matches = [route for route in self.routes if route.matches(amount, risk_level)]
        if matches:
            return max(matches, key=lambda route: (route.priority, route.min_amount)).approver_roles
        return self.default_roles


class PolicyRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    confidence_threshold: float = Field(ge=0, le=1)
    approval_amount_threshold: float = Field(ge=0)
    approval_risk_levels: set[RiskLevel]
    risk_levels: dict[RiskLevel, int]
    actions: dict[str, ActionRule]
    approval_routing: ApprovalRoutingRules = Field(default_factory=ApprovalRoutingRules)

    @model_validator(mode="after")
    def validate_risk_order(self):
        required = set(RiskLevel)
        if set(self.risk_levels) != required:
            raise ValueError(f"risk_levels must define exactly: {', '.join(sorted(level.value for level in required))}")
        if not self.actions:
            raise ValueError("actions cannot be empty")
        if any(not name.strip() for name in self.actions):
            raise ValueError("action names cannot be empty")
        return self


class PolicyVersionInfo(BaseModel):
    version: int
    active: bool
    confidence_threshold: float
    approval_amount_threshold: float
    path: str


def parse_policy_rules(source: str | dict[str, Any] | PolicyRules) -> PolicyRules:
    """Parse YAML or a mapping and validate every policy field."""
    if isinstance(source, PolicyRules):
        return source
    if isinstance(source, str):
        data = yaml.safe_load(source)
    else:
        data = source
    if not isinstance(data, dict):
        raise ValueError("Policy YAML must contain a mapping at its root")
    return PolicyRules.model_validate(data)


def _version_files() -> list[tuple[int, Path]]:
    files: list[tuple[int, Path]] = []
    if DEFAULT_RULES_PATH.exists():
        default = parse_policy_rules(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))
        files.append((default.version, DEFAULT_RULES_PATH))
    if VERSIONS_DIR.exists():
        for path in VERSIONS_DIR.glob("policy-v*.yaml"):
            try:
                rules = parse_policy_rules(path.read_text(encoding="utf-8"))
            except (ValidationError, ValueError, yaml.YAMLError):
                continue
            files.append((rules.version, path))
    return sorted(files, key=lambda item: item[0])


def load_active_rules() -> PolicyRules:
    """Load the highest saved policy version; the checked-in file is the v1 default."""
    versions = _version_files()
    if not versions:
        raise FileNotFoundError(f"No policy rules found at {DEFAULT_RULES_PATH}")
    return parse_policy_rules(versions[-1][1].read_text(encoding="utf-8"))


def list_policy_versions() -> list[PolicyVersionInfo]:
    active_version = load_active_rules().version
    infos = []
    for version, path in _version_files():
        rules = parse_policy_rules(path.read_text(encoding="utf-8"))
        infos.append(PolicyVersionInfo(
            version=version,
            active=version == active_version,
            confidence_threshold=rules.confidence_threshold,
            approval_amount_threshold=rules.approval_amount_threshold,
            path=path.name,
        ))
    return infos


def save_new_policy_version(source: str | dict[str, Any] | PolicyRules) -> PolicyRules:
    """Validate first, then create a new immutable version without replacing prior files."""
    candidate = parse_policy_rules(source)
    next_version = max((version for version, _ in _version_files()), default=0) + 1
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    while True:
        versioned = PolicyRules.model_validate({**candidate.model_dump(mode="json"), "version": next_version})
        destination = VERSIONS_DIR / f"policy-v{next_version:04}.yaml"
        try:
            with destination.open("x", encoding="utf-8", newline="\n") as policy_file:
                yaml.safe_dump(versioned.model_dump(mode="json"), policy_file, sort_keys=False, allow_unicode=True)
            return versioned
        except FileExistsError:
            next_version += 1
