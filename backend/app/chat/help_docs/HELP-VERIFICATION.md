# HELP-VERIFICATION — Action verification

After a write action, the verifier reads the resulting state back from the configured connector. It does not trust the tool's success response. A failed read-back is recorded as `FAILED`; compensating actions run in reverse order when available, their rollback is verified, and the run escalates.
