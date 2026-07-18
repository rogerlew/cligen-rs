# A10M4O1 scaffold review disposition

Round 1 produced an architecture `HOLD` and an HPC safety
`ACCEPT-WITH-CHANGES`. Every finding is accepted prospectively; there are no
waivers. The revised `package.md`, lesson register, design freeze, roadmap,
and verifier are the disposition. This resolves the design-review hold for
scaffolding only; implementation and any remote action remain undispatched.

| Finding | Disposition | Revised contract |
|---|---|---|
| AR-01 | ACCEPT | Separate immutable semantic candidate, smoke attestation, and designation index; v1 remains status-at-issuance history. |
| AR-02 | ACCEPT | Typed boundary-aware projection, reserved-token and UTF-8 rejection, structural JSON, deterministic ordering, parent hashes, and post-projection leak scan. |
| AR-03 | ACCEPT | Immutable authority revisions preserve fixed authority fields and bind published source lineage plus predecessor hashes. |
| AR-04 | ACCEPT | Cross-run caching is explicitly deferred; only existing within-run, content-addressed matrix reuse is hardened. |
| AR-05 | ACCEPT | Toolkit process supervisor owns process groups, signal forwarding, waiting, atomic status, cleanup, and terminal precedence. |
| AR-06 | ACCEPT | Provider API/stack v2, record/producer v2, semantic configuration v2, smoke-attestation v1, and designation-index v1 are exact. |
| AR-07 | ACCEPT | Canonical telemetry is integer-only; skips revalidate remote identity; partial-transfer behavior is provider-specific and fail-closed. |
| AR-08 | ACCEPT | Roadmap now requires hardening → candidate → smoke → attestation → index → A10M5, with no failed-smoke fallback. |
| HS-01 | ACCEPT | Primary admission reserves a bounded recovery contingency and releases it only after proved cleanup. |
| HS-02 | ACCEPT | Recovery requires settled scheduler accounting, exact node/UID/marker/ancestors/filesystem/path validation twice, and bounded deletion. |
| HS-03 | ACCEPT | Live adapters use one absolute private ledger anchor with genesis and append-only hash chain; alternate or rolled-back state fails. |
| HS-04 | ACCEPT | Private `RAW_COLLECTED` precedes projection and preserves authenticated gate and cleanup data through publication failure. |
| HS-05 | ACCEPT | Supervisor semantics and `CLEANUP_INCOMPLETE` precedence are frozen and receive failure-injection fixtures. |
| HS-06 | ACCEPT | Capacity claims include expansion/products/checkpoints/margin/floor, serialize per base, recheck, and never select unrelated content. |
| HS-07 | ACCEPT | Attempt paths are content-addressed and immutable; run revision manifests are append-only; referenced identities cannot be overwritten. |
| HS-08 | ACCEPT | Slurm starts from `--export=NONE` or proved equivalent; the wrapper reconstructs only registered variables and sets CUBLAS before import. |
| HS-09 | ACCEPT | Layout/toolchain closure is checked both during controller preparation and compute preflight. |
| HS-10 | ACCEPT | Transfer telemetry uses integer nanoseconds; provider-proved resume, SCP partial replacement/removal, and master revalidation are mandatory. |

## Deferred without misclassification

- L08 cross-run caching remains separate design work; this package does not
  claim within-run stage-once behavior remedies A10M4 retransfers.
- L15 and the 5x/10x scientific timing criteria remain unchanged. Their
  reconsideration requires a separate prospective scientific-contract package.
- L09--L12 remain application-owned authoring requirements, not toolkit
  inference.

## Convergence criterion

Round 2 asks both reviewers whether the revised artifacts fully encode their
findings. Any remaining P1/P2 finding reopens disposition and must be resolved
before this scaffold is committed.

## Round-2 architecture correction

The architecture reviewer found `R2-AR-01` (P1): the first revision
overclaimed that a local hash chain could detect restoration of both a ledger
and its local head to an older valid prefix, and it omitted the authorized
genesis lifecycle. `ACCEPT`: the design now freezes an operator-authorized
exclusive genesis with absence/evidence checks, immutable published head
checkpoints, exact pre-spend scheduler reconciliation keyed by authority token,
and a hold when reconciliation is unavailable or ambiguous. It explicitly
states the remaining same-domain detection limit instead of claiming a
nonexistent monotonic store. Fixtures cover first/duplicate genesis, old
prefixes, ledger-plus-head restoration with scheduler evidence or unavailable
accounting, alternate paths, and reviewed recovery after mismatch.

Final convergence: the architecture reviewer returned `CONVERGED` with no
remaining P1/P2 gap. The HPC safety reviewer rechecked the narrowed trust
boundary and returned `CONVERGED` with no remaining P1/P2 safety regression.
