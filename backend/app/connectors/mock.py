"""SQLite-backed local connector used for tests and offline demos."""
from __future__ import annotations

from app.connectors.base import Connector, ConnectorError, TicketCreate, TicketRecord
from app.core.database import get_db


class MockConnector(Connector):
    """Keep the existing internal SQLite ticket tables behind the connector contract."""

    @staticmethod
    def _ensure_tables() -> None:
        with get_db() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS service_tickets (
                    ticket_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE,
                    customer_id TEXT NOT NULL, product_id TEXT NOT NULL,
                    description TEXT NOT NULL, severity TEXT NOT NULL, status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS technician_assignments (
                    assignment_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE,
                    ticket_id TEXT NOT NULL, technician_id TEXT NOT NULL, status TEXT NOT NULL
                );
                """
            )

    async def create_ticket(self, ticket: TicketCreate) -> TicketRecord:
        self._ensure_tables()
        ticket_id = f"TKT-{ticket.action_id}"
        with get_db() as conn:
            conn.execute(
                "INSERT INTO service_tickets VALUES (?, ?, ?, ?, ?, ?, 'CREATED')",
                (ticket_id, ticket.action_id, ticket.customer_id, ticket.product_id,
                 ticket.description, ticket.severity),
            )
        record = await self.get_ticket(ticket_id)
        if record is None:
            raise ConnectorError("SQLite connector created a ticket but could not read it back")
        return record

    async def get_ticket(self, ticket_id: str) -> TicketRecord | None:
        self._ensure_tables()
        with get_db() as conn:
            row = conn.execute(
                """SELECT t.*, a.technician_id AS assignee_id, a.action_id AS assignment_action_id
                   FROM service_tickets AS t
                   LEFT JOIN technician_assignments AS a
                     ON a.ticket_id = t.ticket_id AND a.status = 'ASSIGNED'
                   WHERE t.ticket_id = ? OR t.action_id = ?""",
                (ticket_id, ticket_id),
            ).fetchone()
        if row is None:
            return None
        return TicketRecord(
            ticket_id=row["ticket_id"], action_id=row["action_id"],
            customer_id=row["customer_id"], product_id=row["product_id"],
            summary=row["description"][:120], description=row["description"],
            severity=row["severity"], status=row["status"],
            assignee_id=row["assignee_id"], assignment_action_id=row["assignment_action_id"],
        )

    async def cancel_ticket(self, ticket_id: str) -> TicketRecord:
        self._ensure_tables()
        with get_db() as conn:
            conn.execute(
                "UPDATE service_tickets SET status = 'CANCELLED' "
                "WHERE (ticket_id = ? OR action_id = ?) AND status = 'CREATED'",
                (ticket_id, ticket_id),
            )
        record = await self.get_ticket(ticket_id)
        if record is None or record.status != "CANCELLED":
            raise ConnectorError(f"Ticket could not be cancelled: {ticket_id}")
        return record

    async def assign(self, ticket_id: str, technician_id: str, *, action_id: str) -> TicketRecord:
        self._ensure_tables()
        ticket = await self.get_ticket(ticket_id)
        if ticket is None or ticket.status != "CREATED":
            raise ConnectorError(f"Cannot assign technician; active ticket not found: {ticket_id}")
        with get_db() as conn:
            conn.execute(
                "INSERT INTO technician_assignments VALUES (?, ?, ?, ?, 'ASSIGNED')",
                (f"ASN-{action_id}", action_id, ticket.ticket_id, technician_id),
            )
        record = await self.get_ticket(ticket.ticket_id)
        if record is None or record.assignee_id != technician_id:
            raise ConnectorError(f"Technician assignment could not be verified for: {ticket_id}")
        return record

    async def unassign(self, ticket_id: str, *, action_id: str) -> TicketRecord:
        self._ensure_tables()
        ticket = await self.get_ticket(ticket_id)
        if ticket is None:
            raise ConnectorError(f"Cannot unassign technician; ticket not found: {ticket_id}")
        with get_db() as conn:
            conn.execute(
                "UPDATE technician_assignments SET status = 'UNASSIGNED' "
                "WHERE ticket_id = ? AND action_id = ? AND status = 'ASSIGNED'",
                (ticket.ticket_id, action_id),
            )
        record = await self.get_ticket(ticket.ticket_id)
        if record is None or record.assignee_id is not None:
            raise ConnectorError(f"Technician assignment could not be cleared for: {ticket_id}")
        return record
