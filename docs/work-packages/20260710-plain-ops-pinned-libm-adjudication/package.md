# Plain-Operations Pinned-Transcendental Adjudication

Status: `EXECUTED-HOLD-OPERATOR-DEFERRED` (closed 2026-07-10; see
[`artifacts/closeout.md`](artifacts/closeout.md))
Date: 2026-07-10
Evidence mode: Static

## Objective

This package was scoped to determine whether the explicit `f64::mul_add`
operations in the faithful pinned f32 `logf`/`cosf` implementations are
necessary for bit identity on a non-FMA CPU. On 2026-07-10, the operator
deferred that non-FMA optimization path in favor of refining a fast-batch
profile and its stochastic-parity assessment. No candidate was implemented
or adjudicated.

## Scope

Originally included:

- Candidate plain-operation variants at each current `mul_add` call site in
  `libm_pinned`'s faithful log/cos paths.
- Bit-for-bit comparison against the existing captured transcendental corpus
  and all 12 golden CLI outputs on the Xeon E5-2697 v2 host.
- A reproducible before/after seed-17 runtime measurement only after a
  candidate passes every fidelity gate.

Excluded throughout:

- Fast math, fused-operation disabling flags, width changes, or any
  acceptance tolerance.
- Changing the fast-batch profile or beginning a stochastic-parity campaign.

## Authority

- ADR-0001 and the Rust Scientific Coding Standard §1.3: faithful
  transcendentals require empirical adjudication against reference captures.
- `crates/cligen/src/libm_pinned.rs`: current pinned f32 log/cos
  transcriptions and explicit `mul_add` sites.
- `20260710-cli-runtime-profile/artifacts/profile-report.md`: non-FMA
  `fma_fallback` attribution motivating the candidate.

## Plan

1. Record the operator deferral and close without source changes or generated
   evidence.
2. Retain this package as the scoped record if the operator later explicitly
   reopens faithful plain-operation adjudication.
3. First follow-on action: refine and ratify
   `SPEC-FAST-BATCH-V1` before dispatching another implementation or
   benchmark package.

## Gates

Not run: this closeout makes no production or candidate change. The listed
candidate and package gates remain the required gates if the package is
explicitly reopened.

## Exit criteria

`EXECUTED-HOLD-OPERATOR-DEFERRED`: the operator chose not to pursue the
non-FMA optimization path. The named first follow-on action is refinement of
the fast-batch-v1 specification; no inference is made about whether plain
operations would preserve the faithful contract.

## Artifacts

- [`artifacts/closeout.md`](artifacts/closeout.md)
