# Independent HPC safety and reproducibility review

Reviewer: subagent `/root/toolkit_hpc_safety_review`
Mode: read-only; no file edits or remote operations
Draft reviewed: initial revision-1 specification scaffold of 2026-07-17

## Findings

| ID | Priority | Finding | Proposed correction |
|---|---|---|---|
| HS-01 | P1 | Submission is neither atomic nor retry-safe under response loss or concurrent controllers. | Single-writer lock, durable intent/reservation, unique Slurm token, reconciliation, and no blind retry. |
| HS-02 | P1 | Confirmation enforcement begins after `prepare` can enumerate or hash protected data. | Default-deny logical allowlisting before every filesystem observation, including core commands, links, globs, and archives. |
| HS-03 | P1 | Exact paths required for cleanup conflict with sanitized publishable receipts. | Separate private operational state from sanitized publication receipts and retain private state through cleanup. |
| HS-04 | P2 | Compute probing before planning would require an unplanned allocation. | Keep discovery nonallocating; require a frozen plan and registered bounded job for compute validation. |
| HS-05 | P2 | Marker creation and cleanup are not failure-atomic and admit replacement races. | Create/mark exclusively before other objects; hold a run lock; validate and delete in one bounded script; test interruptions. |
| HS-06 | P2 | Raw evidence quarantine and hostile archive handling are unspecified. | Use a size-bounded private quarantine, reject unsafe members, sanitize separately, publish only after verification. |
| HS-07 | P2 | Requested/actual GPU accounting and requeue semantics are incomplete. | Define both ledgers, reserve requested use, default no-requeue, count every allowed restart, settle exact jobs. |
| HS-08 | P2 | SSH master checks do not cover expiry during long or later operations. | Check immediately before each operation and after long transfers; enforce batch mode and finite total timeouts. |
| HS-09 | P2 | Hashing a portable runtime does not make its archive safe or its native linkage compatible. | Inspect/extract safely, verify manifests, record compute loader/libc/CPU compatibility, and prohibit unplanned native builds. |
| HS-10 | P2 | The Python 3.11 handoff is resource-bounded but not claim-bounded. | Freeze exact runtime/ABI/assets and enumerate standard-library, native, NumPy, PyTorch, isolation, compute, and cleanup gates plus exclusions. |
| HS-11 | P2 | Record hashing lacks canonical JSON rules. | Adopt RFC 8785/JCS and golden fixtures. |
| HS-12 | P3 | “Post-cleanup queue state” could incorrectly require an empty user-wide queue. | Reconcile exact registered job identities; leave unrelated operator jobs alone. |

## Reviewer conclusion

The initial draft had three P1 and eight P2 findings. The reviewer stated that
no P1/P2 safety or reproducibility finding would remain after the proposed
corrections and adverse fixtures were incorporated.
