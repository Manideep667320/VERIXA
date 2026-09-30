"""Constants, enums, and literal types used across the application."""

from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class AutonomyDecision(StrEnum):
    EXECUTE = "EXECUTE"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    ESCALATE = "ESCALATE"


class ActionStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    VERIFIED = "VERIFIED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentType(StrEnum):
    SOP = "SOP"
    MANUAL = "MANUAL"
    POLICY = "POLICY"
    INCIDENT = "INCIDENT"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Tool names — registry keys
TOOL_CREATE_TICKET = "create_service_ticket"
TOOL_ASSIGN_TECHNICIAN = "assign_technician"
TOOL_LOOKUP_CUSTOMER = "lookup_customer"
TOOL_SEND_NOTIFICATION = "send_notification"

# Maximum agent reasoning iterations to prevent runaway loops
MAX_AGENT_ITERATIONS = 10
