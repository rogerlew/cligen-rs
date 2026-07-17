# HPC safety and reproducibility convergence review — round 2

Reviewer: subagent `/root/toolkit_hpc_safety_review`
Mode: fresh end-to-end, read-only; no file edits or remote operations
Frozen specification SHA-256:
`17806c0f5e33c60d40430587af47f80a271d12e9da4c7527555608f9ea6c50b7`
Initial verdict: `NOT CONVERGED`

| ID | Priority | New or residual finding | Required correction |
|---|---|---|---|
| R2-HS-01 | P1 | Per-run locking could oversubscribe one authority ceiling; amendments could reset accounting. | Use immutable authority/budget identity and one append-only atomically locked ledger; hold ambiguous intents until non-submission is proven. |
| R2-HS-02 | P2 | Shell-facing fields other than run/package IDs lacked injection-safe grammars and argument semantics. | Reject unsafe characters/options/paths; use positional quoted arguments and `--`; prohibit `eval` and source interpolation. |
| R2-HS-03 | P2 | Hard termination can bypass job-local cleanup, especially with persistent `/tmp` fallback. | Require scheduler-purged or toolkit-recoverable storage, in-allocation absence evidence, and `CLEANUP_INCOMPLETE` when recovery cannot be proved. |
| R2-HS-04 | P3 | Download promotion was less exact than upload promotion. | Download into a nonfinal quarantine name, compare frozen remote/local size and hash, then promote atomically before extraction. |

The reviewer found the exact Python 3.11 runtime and test claim boundary
sufficiently bounded.
