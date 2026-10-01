# HELP-HASH-CHAIN — Tamper-evident audit hash chain

Each audit row has a `prev_hash` pointing to the preceding row's SHA-256 `row_hash`. The first row points to a fixed genesis hash. The hash is calculated from canonical JSON for the row, including its previous hash.

Verification recomputes each hash and checks row order and the saved chain head. Editing, deleting, or reordering a row breaks a link or the head count; verification reports the first broken run ID. The chain makes tampering detectable, but does not prevent a database administrator from changing the database.
