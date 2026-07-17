# Architecture and extensibility convergence review — round 2

Reviewer: subagent `/root/toolkit_arch_review`
Mode: fresh end-to-end, read-only; no file edits or remote operations
Frozen specification SHA-256:
`17806c0f5e33c60d40430587af47f80a271d12e9da4c7527555608f9ea6c50b7`
Initial verdict: `NOT CONVERGED`

| ID | Priority | New or residual finding | Required correction |
|---|---|---|---|
| R2-AR-01 | P1 | Locks and resource ledgers were per run although the ceiling belongs to one package dispatch. Distinct runs could each reserve the full budget. | Add immutable dispatch/authority and budget identities plus one atomic ledger/lock shared by all runs, revisions, attempts, and retries. |
| R2-AR-02 | P2 | One linear run state could not represent sequential, parallel, retry, or expected-nonzero job matrices. | Separate the run lifecycle from repeatable `(job_role, attempt_index)` lifecycles and settle the matrix before collection. |
| R2-AR-03 | P2 | Prospective amendments had no lineage, field, evidence, or resource carry-forward semantics. | Add immutable plan revisions with predecessor hash, authorized unstarted scope, retained receipts, and authority-wide accounting. |
| R2-AR-04 | P3 | Exact registered job cancellation was absent from the command surface. | Add narrowly scoped exact-ID cancellation and terminal accounting; prohibit username/name/glob cancellation. |
| R2-AR-05 | P3 | “Securely removed” overstated what APFS, Ceph, snapshots, and SSD storage can prove. | Require exact-path deletion and verified absence while expressly disclaiming physical secure erasure. |

The reviewer otherwise found the declarative-provider, toolkit-owned-operation,
injected-fake, and SCP-only minimum slice appropriately lightweight.
