"""Read-only verification of the SQLite audit hash chain."""

from __future__ import annotations

from pydantic import BaseModel

from app.audit.logger import GENESIS_HASH, _ensure_audit_schema, _hash_payload, _payload_from_row
from app.core.database import get_db


class ChainVerification(BaseModel):
    valid: bool
    first_broken_row_id: str | None = None
    checked_rows: int


def verify_chain() -> ChainVerification:
    """Verify sequence, previous hashes, row hashes, and the anchored chain head."""
    _ensure_audit_schema()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM run_audit ORDER BY sequence").fetchall()
        head = conn.execute("SELECT * FROM audit_chain_head WHERE singleton = 1").fetchone()

    expected_previous = GENESIS_HASH
    for expected_sequence, row in enumerate(rows, start=1):
        if row["sequence"] != expected_sequence:
            return ChainVerification(valid=False, first_broken_row_id=row["run_id"], checked_rows=expected_sequence - 1)
        if row["prev_hash"] != expected_previous:
            return ChainVerification(valid=False, first_broken_row_id=row["run_id"], checked_rows=expected_sequence - 1)
        if _hash_payload(_payload_from_row(row)) != row["row_hash"]:
            return ChainVerification(valid=False, first_broken_row_id=row["run_id"], checked_rows=expected_sequence - 1)
        expected_previous = row["row_hash"]

    if len(rows) != head["row_count"]:
        present_ids = {row["run_id"] for row in rows}
        missing_terminal = head["last_run_id"] if head["last_run_id"] not in present_ids else None
        broken_id = missing_terminal or (rows[-1]["run_id"] if rows else head["last_run_id"])
        return ChainVerification(valid=False, first_broken_row_id=broken_id, checked_rows=len(rows))
    if rows and (head["last_sequence"] != rows[-1]["sequence"] or head["last_hash"] != rows[-1]["row_hash"]):
        return ChainVerification(valid=False, first_broken_row_id=head["last_run_id"], checked_rows=len(rows))
    if not rows and head["last_hash"] != GENESIS_HASH:
        return ChainVerification(valid=False, first_broken_row_id=head["last_run_id"], checked_rows=0)
    return ChainVerification(valid=True, checked_rows=len(rows))
