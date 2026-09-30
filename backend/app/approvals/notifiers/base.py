"""Typed notifier interface and configuration-based provider factory."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from app.core.config import settings


class NotifierError(RuntimeError):
    """A notification could not be delivered through its configured channel."""


class ApprovalNotice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    run_id: str
    role: str
    request: str
    action_type: str
    action_reason: str
    amount: float
    risk_level: str
    expires_at: datetime | None


class ApprovalNotifier(Protocol):
    channel: Literal["mock", "slack", "email"]

    async def send_approval(self, notice: ApprovalNotice) -> None: ...


def get_notifier() -> ApprovalNotifier:
    """Create the selected notifier; external services are constructed only on demand."""
    if settings.approval_notifier == "mock":
        from app.approvals.notifiers.mock import MockNotifier

        return MockNotifier()
    if settings.approval_notifier == "slack":
        from app.approvals.notifiers.slack import SlackNotifier

        return SlackNotifier()
    if settings.approval_notifier == "email":
        from app.approvals.notifiers.email import EmailNotifier

        return EmailNotifier()
    raise NotifierError(f"Unsupported approval notifier: {settings.approval_notifier}")
