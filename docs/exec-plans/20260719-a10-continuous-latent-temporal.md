# A10 continuous latent temporal process ExecPlan

## Purpose / Big Picture

Test whether daily continuous-time latent climate dynamics reproduce monthly
and yearly stochastic weather statistics without imposing discontinuities at
calendar boundaries, and isolate the value of an additional slow process.

## Progress

- [x] 2026-07-19: audited the empty retained-adapter temporal result and prior
  month/year-stepped state-space implementations.
- [x] 2026-07-19: froze medium-only and medium-plus-slow daily OU candidates.
- [ ] Publish and independently validate the execution scaffold.
- [ ] Execute control and two candidate roles on typed L40 GPUs.
- [ ] Collect, score, replay, clean, review, and reconcile the package.

## Surprises & Discoveries

The earlier A10 state-space and residual families advanced latent state on
calendar-month and calendar-year cells. Monthly/yearly losses therefore did
not distinguish a useful aggregation scale from a potentially artificial
state clock. A10M5R12 removes that confounding mechanism.

## Decision Log

- 2026-07-19: use the exact daily transition of continuous-time OU processes;
  no calendar boundary resets.
- 2026-07-19: fix both candidates to the P2/K2 envelope and vary only the
  presence of the slow state.
- 2026-07-19: use 14--180-day medium and 180--1,460-day slow bounds; learn
  individual factor time scales inside those prospective supports.
- 2026-07-19: retain the ratified A10 temporal outcome gate and defer solar.
- 2026-07-19: distinguish continuous state semantics from scale invariance;
  require a random-origin rolling-window sensitivity successor before any
  qualifying candidate is promoted.
- 2026-07-19: exclude the binary leap-year flag from new loadings while
  retaining and disclosing it in the frozen matched P2 backbone.
- 2026-07-19: give the inherited conditional-member daily NLL zero training
  and checkpoint weight because it is not a marginal mixture score and would
  suppress unpaired latent spread; retain it as a diagnostic.
- 2026-07-19: preserve inherited eligibility but add non-gating actual-series
  annual-family member bootstraps and learned-time-scale reporting because the
  inherited iid observation-year bootstrap destroys annual lag ordering.

## Outcomes & Retrospective

Pending execution.

## Context and Orientation

The package lives at
`docs/work-packages/20260719-a10m5r12-continuous-latent-temporal-process/`.
Its science contract, temporal contract, candidate source, operational
wrappers, and evidence are under `artifacts/`. The predecessor is A10M5R11R2,
whose three residual adapters all failed broadly and nearly equivalently.

## Plan of Work

The frozen P2 controls are reconstructed first. Each candidate job trains all
three seeds and emits the complete six-site/eight-member/100-year stream
matrix. Candidate jobs run concurrently after serialized setup admission.
Local scoring reuses the exact observed/comparator/bootstrap implementation
from A10M5R11R2, with hardened exact comparator axes, retained raw-stream
replay, annual-family diagnostics, and source/receipt-bound two-pass execution.

## Concrete Steps

1. Run freeze, syntax, contract, calendar, and repository gates.
2. Commit and push the scaffold to `main`.
3. Prepare immutable runtime/corpus/source assets and create authority/plan.
4. Stage and verify; submit control, then the two candidates concurrently.
5. Observe terminal receipts, collect allowlisted evidence, and settle usage.
6. Replay retained raw streams, then run two isolated source/receipt-bound
   comparator/bootstrap passes and require byte identity.
7. Clean exact remote/job-local state, close the toolkit run, and publish the
   package result.

## Validation and Acceptance

Architecture tests must prove the OU FFT realization equals scalar recurrence
at training and generation lengths, stationary variance/covariance, finite
gradients, month/year tensors ignored by state evolution, and both arms share
the medium process. Execution requires 288 retained support-valid streams,
finite metrics, authenticated collection, identical selector replays, and all
standard Cargo gates.

## Idempotence and Recovery

Authority and remote run identities are single-use. Candidate roles have one
scientific attempt. Only the reserved five-minute exact-node cleanup role may
recover job-local residue. Local comparator replay uses separate scratch trees.

## Artifacts and Notes

Private credentials, scheduler state, runtime archives, and raw corpus remain
outside Git. Sanitized receipts, results, hashes, dispositions, and reviews
are committed.

## Interfaces and Dependencies

`SPEC-A10-CONTINUOUS-LATENT-TEMPORAL` governs candidate semantics.
`SPEC-A10-RETAINED-ADAPTER-TEMPORAL` supplies the inherited temporal
evaluation, and `SPEC-A10-CORPUS` supplies calendar/missingness semantics.

## Revision Notes

- 2026-07-19: created for the continuous-process successor campaign.
