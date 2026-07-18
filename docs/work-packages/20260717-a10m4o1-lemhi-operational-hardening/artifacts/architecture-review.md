# Independent architecture review — round 1

Reviewer: `toolkit_arch_review`
Verdict on initial scaffold: `HOLD`

The ownership boundary and application-owned disposition of L09--L12 were
sound, but the initial transition and failure contracts were not yet safe to
implement.

| ID | Severity | Finding | Required disposition |
|---|---:|---|---|
| AR-01 | P1 | The proposed candidate embedded promotion/smoke status in its hashed configuration, so promotion could not be both immutable and truthful. | Split immutable semantic candidate, immutable smoke attestation, and versioned designation index; interpret v1 status as status at issuance and test failed-smoke immutability. |
| AR-02 | P1 | Exact textual replacement was unsafe for overlapping/prefix paths and pre-existing token text. | Reject reserved token syntax; use typed, descending-length, boundary-aware replacements; transform JSON structurally; reject invalid UTF-8; scan after projection; add overlap/prefix/stability fixtures. |
| AR-03 | P2 | `derive-run` could not safely change the currently authority-bound source commit. | Add immutable authority revisions preserving identity, budget, class, branch, and push target; authorize only published lineage; bind runs to revision and predecessor hashes. |
| AR-04 | P2 | Stage-once matrix reuse already existed and would not remedy A10M4's cross-run retransfers. | Keep telemetry and within-run behavior; defer cross-run reuse rather than claiming a fix. |
| AR-05 | P2 | A shell trap was not a sufficient child/signal/exit-status contract, especially with `srun`. | Specify a process supervisor, child process group, signal forwarding, wait semantics, atomic status, cleanup order, and terminal precedence. |
| AR-06 | P2 | “Next version” did not freeze exact provider, record, and configuration compatibility axes. | Name provider API v2, provider classes, record/producer v2, semantic configuration v2, and the dual-reader/no-mixed-stack rules. |
| AR-07 | P2 | Float telemetry and a cached skip could be nondeterministic or accept changed remote state. | Use integer canonical telemetry with overflow checks and immediately revalidate remote identity before a skip. |
| AR-08 | P2 | The roadmap did not distinguish candidate publication, smoke evidence, and designation. | Freeze hardening → semantic candidate → bounded smoke → attestation → index revision → A10M5; failed smoke holds without v1 fallback. |

No production or remote action was reviewed. The hold applies to the initial
prospective design only and is eligible for resolution by scaffold revision.
