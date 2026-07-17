# Convergence review disposition — round 2

Disposition date: 2026-07-17
Frozen input specification SHA-256:
`17806c0f5e33c60d40430587af47f80a271d12e9da4c7527555608f9ea6c50b7`

Both independent reviewers initially returned `NOT CONVERGED`. Every finding,
including the optional P3 clarifications, is accepted below.

| Finding | Disposition | Normative result |
|---|---|---|
| R2-AR-01 | ACCEPTED / MERGED R2-HS-01 | §§2, 5, 6, and 10 define `authority_id`, `resource_budget_id`, authority-wide locking, and an append-only shared ledger that survives runs and revisions. |
| R2-AR-02 | ACCEPTED | §5 separates run state from repeatable job-attempt state and §15 tests sequential, parallel, retry, cancellation, and expected-nonzero matrices. |
| R2-AR-03 | ACCEPTED | §6.3 defines immutable plan-revision lineage, retained evidence, unstarted-only scope, and nonresetting resource use. |
| R2-AR-04 | ACCEPTED | §§5 and 15 define exact registered-ID cancellation, terminal observation/accounting, and prohibit broad selectors. |
| R2-AR-05 | ACCEPTED | §6 requires exact-path deletion and verified absence and disclaims physical secure-erasure claims. |
| R2-HS-01 | ACCEPTED / MERGED R2-AR-01 | Submission intent charges the shared authority budget; ambiguity remains charged until non-submission is proven. |
| R2-HS-02 | ACCEPTED | §6 defines shell-facing grammars, safe positional arguments/quoting, `--`, and prohibitions on `eval` and interpolation; §15 adds adverse fixtures. |
| R2-HS-03 | ACCEPTED | §9 requires scheduler-purged or toolkit-recoverable job-local storage and holds closure at `CLEANUP_INCOMPLETE` without purge/recovery proof. |
| R2-HS-04 | ACCEPTED | §9 requires nonfinal quarantine download, remote/local size/hash comparison, and atomic promotion before extraction. |

## Final convergence verification

Revised specification SHA-256:
`a81c3ed2aa54dff2bd322de8aabc1b1482983c5c06f0ebd066803c7731865a74`

- Architecture reviewer: `CONVERGED`. R2-AR-01 through R2-AR-05 are fully
  incorporated; no remaining or newly introduced P1/P2 finding.
- HPC safety reviewer: `CONVERGED`. R2-HS-01 through R2-HS-04 are fully
  incorporated; no remaining or newly introduced P1/P2 finding.

Round-2 terminal: `SPEC-CONVERGED`
