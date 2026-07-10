# Disposition — Performance Arc Review

Date: 2026-07-10
Review: [`review-claude.md`](review-claude.md), commit `27d532c`.
Executor: Codex

## F1 — Operator-deferred and closed

The operator explicitly chose not to pursue the non-FMA optimization path on
2026-07-10. The separate
`20260710-plain-ops-pinned-libm-adjudication` package is closed
`EXECUTED-HOLD-OPERATOR-DEFERRED`; it contains no candidate result and must
not be reopened implicitly. Its outcome is no longer a prerequisite for
fast-batch refinement or for deciding whether to assess its stochastic
behavior.

## F2 — Accepted and remediated as far as the current baseline permits

The full fast-batch matrix now ran on FMA-capable `wepp1`. The composite is
2.301 s faithful versus 0.349 s fast (6.59x), with all runner acceptance
checks passing. This materially narrows, but does not erase, the original
non-FMA-host result. It is sufficient motivation to refine a v1 design; it
is not itself a stochastic-parity result.

## F3 — Accepted and remediated

SPEC-GENERATION-PROFILES now explicitly declares that `fast_batch_v0` removes
the parameter-5 and parameter-9 conditional zero masks, including observed
mode's all-zero parameter-9 behavior and the `bk7.v7 == 0.0` recovery path.
These become pre-registered attention cells rather than an implicit
QC-bypass side effect.

## F4 — Accepted; deferred to a scoped workload characterization

The golden matrix is an edge-coverage matrix, not a claim about production
burn distributions. Inspecting production WEPPpy invocations and retaining a
burn sweep need their own data-source, retention, and corpus decisions. No
production workload probe is performed in this package. Any parity package
must declare its burn distribution and sweep before treating a composite as
representative.

## F5 — Accepted as methodology requirements

Future marginal-speedup work will pin a core, increase samples, and report
precision consistent with sample counts. Single-storm process timings remain
startup measurements, not generator-throughput claims. A future fast profile
must widen the v0 seed derivation before making quality claims. The operator's
performance-arc reprioritization is recorded here; it does not silently
supersede the A-series roadmap.

## Updated operator sequencing

The review's proposed equivalence design remains useful direction, with the
following operator-directed order:

1. Refine and ratify `SPEC-FAST-BATCH-V1`, including the parity-assessment
   design and the runtime `inp.yaml` profile contract.
2. Dispatch a bounded v1 implementation/benchmark package and measure it on
   FMA-capable `wepp1` before committing to a broad parity campaign.
3. If its performance remains material, dispatch a separate bounded,
   pre-registered stochastic-parity package.
4. Keep F1 deferred unless the operator explicitly reopens the faithful
   non-FMA path.

The current `fast_batch_v0` result remains an experimental performance
measurement, not a candidate parity claim.
