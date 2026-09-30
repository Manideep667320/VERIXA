"""Configurable ticket-system connector adapters."""

from app.connectors.base import Connector, ConnectorError, TicketCreate, TicketRecord, get_connector

__all__ = ["Connector", "ConnectorError", "TicketCreate", "TicketRecord", "get_connector"]
