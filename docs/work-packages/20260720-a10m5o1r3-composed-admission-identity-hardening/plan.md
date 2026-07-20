# Execution plan

1. Add a helper that resolves the `checker_assets` object under protocol
   `ordered-plan-assets-v1` from the
   semantic plan into ordered `{logical_name, bytes, sha256}` records.
2. Extend `_validate_admission_materialization` additively: accept the exact
   historical shape or that shape plus the additive object; reject unknown fields,
   protocols, empty/duplicate rosters, unsafe names, missing assets, and
   non-executable members.
3. At `_submission_admission_hash`, reconstruct the ordered checker projection
   from the current plan. Require exact equality with private prepared assets,
   promoted transfer receipts, and
   `receipt.input_identities.checker_assets` before accepting the
   receipt.
4. Make `admission_materialization` immutable across plan amendments, matching
   the already-immutable asset roster and preventing checker-chain mutation
   after verification.
5. Extend hardening fixtures for historical omission, a two-checker positive
   path, order sensitivity, stale/fresh identity rejection, tamper, duplicate,
   missing, non-executable, and receipt mismatch cases. Assert every failure
   occurs before ledger reservation and adapter submission.
6. Run the complete toolkit suite, shell syntax, repository gates, and an
   independent review. Record disposition and only then unblock R14R2R1.
