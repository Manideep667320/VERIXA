# HELP-AUDIT-FIELDS — Audit record fields

Each audit row records one agent run. These fields are generated from the live SQLite `run_audit` table, including their declared SQLite types:

{{AUDIT_FIELDS}}

The `snapshot` field retains the input and agent outputs needed to understand the run. The chain hashes the complete row, including `prev_hash`.
