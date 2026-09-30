"""Typed ticket connector boundary and configured provider factory."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class ConnectorError(RuntimeError):
    """Clear, provider-neutral connector failure suitable for tool results."""


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action_id: str
    customer_id: str
    product_id: str
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"


class TicketRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticket_id: str
    action_id: str = ""
    customer_id: str = ""
    product_id: str = ""
    summary: str = ""
    description: str = ""
    severity: str = "MEDIUM"
    status: str
    assignee_id: str | None = None
    assignment_action_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class Connector(ABC):
    """Ticket and assignment operations used by tools and independent verification."""

    @abstractmethod
    async def create_ticket(self, ticket: TicketCreate) -> TicketRecord: ...

    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> TicketRecord | None: ...

    @abstractmethod
    async def cancel_ticket(self, ticket_id: str) -> TicketRecord: ...

    @abstractmethod
    async def assign(self, ticket_id: str, technician_id: str, *, action_id: str) -> TicketRecord: ...

    async def unassign(self, ticket_id: str, *, action_id: str) -> TicketRecord:
        raise ConnectorError(f"Connector {type(self).__name__} does not support unassignment")


def get_connector() -> Connector:
    """Build the configured ticket connector (mock by default)."""
    provider = settings.connector_provider
    if provider == "mock":
        from app.connectors.mock import MockConnector

        return MockConnector()
    if provider == "jira":
        from app.connectors.jira import JiraConnector

        return JiraConnector.from_settings()
    raise ConnectorError(f"Unsupported ticket connector provider: {provider}")
