# Disposition — Performance Arc Review

Date: 2026-07-10
Review: [`review-claude.md`](review-claude.md), commit `27d532c`.
Executor: Codex

## F1 — Accepted; separate faithful-mode package scaffolded

The finding is decision-critical. The new
`20260710-plain-ops-pinned-libm-adjudication` package owns a candidate that
replaces only explicit `mul_add` calls in the pinned f32 log/cos paths with
plain operations, then adjudicates it against the captured transcendental
corpus and all faithful goldens. No faithful numeric change is made here.
Its pass/fail result determines whether the fast-profile path remains worth a
stochastic-parity campaign.

## F2 — Accepted and remediated as far as the current baseline permits

The full fast-batch matrix now ran on FMA-capable `wepp1`. The composite is
2.301 s faithful versus 0.349 s fast (6.59x), with all runner acceptance
checks passing. This materially narrows, but does not erase, the original
non-FMA-host result. A rerun against a hypothetical F1-passing faithful
baseline remains required before any go/no-go parity decision.

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

## Guidance

The review's recommended order is accepted:

1. F1 plain-operations adjudication.
2. F2 rerun against an F1-passing baseline if one exists.
3. Only if a material gap remains, consider a batchwise-QC `fast_batch_v1`.
4. Then conduct a bounded, pre-registered stochastic-equivalence study.

The current `fast_batch_v0` result remains an experimental performance
measurement, not a candidate parity claim.
