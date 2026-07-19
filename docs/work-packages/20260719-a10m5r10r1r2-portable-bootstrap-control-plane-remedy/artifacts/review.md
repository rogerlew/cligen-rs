# Independent execution review

Disposition: `ACCEPT`.

The reviewer independently authenticated source `c63ab18…`, authority
`f08dd107…`, plan `a0fa878e…`, all seven provider definitions, the 935-minute
ceiling, control admission `922eb582…`, setup `b0babe44…`, job receipt
`ce594097…`, and live Slurm accounting for job `1014054` (failed 1:0 after 80
seconds on node03). The protected toolkit diff from `0ddffd9…` is empty.

The portable runtime, pip installation/check, payload deletion, admission,
identity, ready setup, and job-local cleanup gates passed. Only
`control_evidence_published` failed. The reviewer reproduced the corpus-root
cause from archive SHA-256 `8770e127…` and confirmed that the payload failed on
its first manifest read before calendar preflight, Daymet loading, control
reconstruction/training, candidate work, or selection.

Matrix-stop record `0462d55b…` stopped exactly ten never-submitted roles.
Sparse collection was disjoint and exhaustive at 13 present plus 140 absent;
all collected identities match record `950dd0f1…` and archive `de0feb79…`.
Ledger `ce8bc0e9…` validates through head `64164d46…`: 30 requested control
minutes settled at two actual GPU-minutes, and the unused five-minute recovery
reserve was released. Cleanup `44434a40…`, terminal `73feea03…`, and a fresh
remote check prove exact absence and normal toolkit closure.

The reviewer accepted
`HOLD-A10M5R10R1R2-CORPUS-ROOT-NESTING`, found the package, roadmap, and
ExecPlan records consistent, and agreed that restoring `-C "$job_local"` in
both wrappers is the least-complex successor correction. No findings remain.
