"""Audit API routes — retrieve, verify, and export the append-only audit chain."""

import csv
import io
import json
from typing import Literal

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response

from app.audit.logger import get_run_audits
from app.audit.verify_chain import verify_chain
from app.models import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/verify")
async def verify_audit_chain():
    """Return chain validity and the first row that fails verification."""
    return verify_chain().model_dump(mode="json")


@router.get("/export")
async def export_audit(format: Literal["json", "csv"] = Query(default="json")):
    """Export all audit rows with their replay snapshots and chain hashes."""
    records = get_run_audits()
    rows = [record.model_dump(mode="json") for record in records]
    if format == "json":
        return JSONResponse(content=rows)

    output = io.StringIO(newline="")
    fields = list(rows[0]) if rows else [
        "run_id", "prompt", "evidence_ids", "policy_rule", "decision", "actions",
        "verification", "timestamp", "sequence", "snapshot", "prev_hash", "row_hash",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: value if isinstance(value, str) else json.dumps(value)
                         for key, value in row.items()})
    return Response(content=output.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=audit.csv"})


@router.get("/{run_id}")
async def get_audit_trail(run_id: str) -> list[AuditEvent]:
    """Retrieve the full audit trail for a given run."""
    # TODO: Fetch from database
    return []
