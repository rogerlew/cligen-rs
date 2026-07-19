# A10 Climate-Normal Residual Architecture

This living ExecPlan follows `.agent/PLANS.md`. It coordinates A10M5R9 without
replacing the package, specification, machine contract, or toolkit evidence.

## Purpose / Big Picture

A10M5R8 showed that aggregate stochastic training pressure is informative but
that P1 entangles climate location with variability. A10M5R9 tested the
smallest new architecture question: can a candidate-fit-only monthly climate
baseline plus a small persistent stochastic residual outperform the identical
baseline without that residual while preserving P1-level location/proper fit?

The answer is mixed and terminal for this package. The residual met its
dispersion target and preserved all baseline blocks, but the combined arm
missed the overall-improvement threshold and both P1 guards. No arm advances.

## Progress

- [x] (2026-07-19) Operator authorized the next science architecture package.
- [x] (2026-07-19) Froze baseline-only, baseline-plus-residual, exact P1
  context, calendar, roles, objective, and decision surface.
- [x] (2026-07-19) Passed local architecture, calendar, decision, source, and
  complete immutable-corpus preflight checks.
- [x] (2026-07-19) Published source commit `68b57fe`, initialized one 65
  GPU-minute authority, and executed job `1014027` on one L40.
- [x] (2026-07-19) Authenticated the all-240 comparison and deterministic HOLD.
- [x] (2026-07-19) Collected evidence, verified exact cleanup, released the
  reserve, closed the authority, and reconciled package records.
- [x] (2026-07-19) Passed the committed result verifier and repository gates.

## Surprises & Discoveries

- Official Daymet's missing leap-year rows are December 31, not February 29.
  The revision-2 preflight correctly accepted 10,950 observations on a 10,958-
  label Gregorian axis and 2,920 observations in each 2,922-label test window.
- The 30-parameter residual reduced the registered monthly/annual dispersion
  composite by 15.15% and did not degrade any baseline block. Its mechanism is
  therefore useful even though the combined architecture failed.
- The explicit-normal baseline scored 2.8687 climate / 4.6118 NLL versus P1 at
  2.5904 / 4.1787. The residual recovered some climate error but not this
  starting deficit.
- Both selected checkpoints landed at their prospective epoch ceilings. That
  cautions against reading the values as converged optima, but does not alter
  or reopen the frozen decision.
- A manually copied source SHA failed during private asset preparation. Assets
  were rebuilt from the exact published SHA before authority creation, staging,
  or compute; no frozen identity or ledger was affected.

## Decision Log

- The baseline is a six-regime by twelve-month distribution-head table plus a
  shared latitude/longitude/elevation correction. This is transferable to
  fit-validation without target lookup.
- The residual state updates monthly, not daily, because monthly and annual
  stochastic dispersion are the frozen target.
- Residuals perturb only occurrence and core location heads. Scale parameters
  and baseline weights remain owned by the baseline.
- Member innovations are centered and arm-paired so the residual represents
  variability rather than an unconstrained second location surface.
- The result is held exactly as frozen; the 4.41% overall improvement is not
  rounded into the 5% gate and no epoch/threshold retry is authorized.
- Solar remains downstream. The evidence instead motivates preserving exact P1
  and attaching the supported monthly residual as a small adapter.

## Outcomes & Retrospective

Job `1014027` completed successfully in 811 GPU-seconds and charged 14
GPU-minutes. The accepted P1 control reconstructed exactly, all roles and
calendar gates passed, and the baseline remained byte-identical during
residual fitting. Relative to baseline, the residual achieved 15.15%
dispersion improvement, 4.41% overall climate improvement, no block
degradation, and an acceptable daily NLL. It nevertheless remained 5.86% worse
than P1 on climate score and 11.03% worse on NLL, so the selector issued
`HOLD-A10M5R9-RESIDUAL-ARCHITECTURE-NOT-SUPPORTED`.

The package answered its ablation cleanly: retain the monthly stochastic
mechanism, reject the combined replacement architecture. The next prospective
test should compare frozen P1 with frozen P1 plus a centered monthly residual
adapter. Solar and broader physical inputs remain deferred.

## Context and Orientation

The package authority is
`docs/work-packages/20260719-a10m5r9-climate-normal-residual-architecture/package.md`.
The public research contract is
`docs/specifications/SPEC-A10-CLIMATE-NORMAL-RESIDUAL.md`; the machine freeze is
`artifacts/architecture-contract.json` below the package. Experiment sources
are under `artifacts/jobs/`. The committed result is
`artifacts/comparison-summary.json`, and the authenticated private publication
is retained below
`/Users/roger/.cache/cligen-rs/a10m5r9-climate-normal-residual/state/runs/a10m5r9-climate-normal-residual-r0/publication/`.

Candidate-fit is the only gradient/normal source. Fit-validation is
checkpoint/final scoring only. Development-selection and confirmation remain
sealed.

## Plan of Work

The package first froze the architecture and decision, then verified the full
immutable corpus calendar before reserving scarce compute. One package-scoped
toolkit authority staged the exact published source and private corpus to an
exact remote root. The allocation reconstructed P1, trained and selected the
baseline, froze it, trained the residual, scored all three arms on all 240
fit-validation points, and published a deterministic decision. Evidence was
collected before exact cleanup and terminal authority close. Finally, concise
hash-bound results were committed and repository gates were run.

## Concrete Steps

From `/Users/roger/src/cligen-rs`, the prospective and result checks are:

    python3 docs/work-packages/20260719-a10m5r9-climate-normal-residual-architecture/artifacts/verify_freeze.py
    python3 docs/work-packages/20260719-a10m5r9-climate-normal-residual-architecture/artifacts/verify_result.py
    cargo fmt --check
    cargo clippy --all-targets -- -D warnings
    cargo test

The immutable experiment was published from commit
`68b57fecd931d0cf10f9e962f8fe228e78a61287` and executed as toolkit run
`a10m5r9-climate-normal-residual-r0`, Slurm job `1014027`. The source-specific
toolkit transcript identities are in `artifacts/toolkit-records.md`; commands
must not be replayed against the closed authority.

## Validation and Acceptance

Acceptance requires exact P1 identity, a valid revision-2 calendar over all
1,440 eligible points, byte-identical baseline state before/after residual
fitting, gradient-free fit-validation, sealed protected roles, complete
all-240 scores, deterministic decision, nine publication gates, settled
accounting, collected evidence, absent exact roots, closed authority, and all
repository gates. All conditions passed. Scientific advancement was separate
and failed prospectively, producing an executed HOLD rather than an operations
failure.

## Idempotence and Recovery

Local verifiers and repository gates are repeatable. The authority and run are
closed and must not be reset or resubmitted. Recovery was never invoked; its
five-minute reserve was released. Any future architecture test requires a new
package identifier, source commit, authority, remote root, and ledger. The
private publication is immutable evidence, not a staging source for a retry.

## Artifacts and Notes

- `artifacts/comparison-summary.json` records the all-240 scores and decision.
- `artifacts/execution-disposition.md` records the terminal and successor.
- `artifacts/review.md` records scientific/evidence/operations review.
- `artifacts/resource-ledger.md` settles 14 of 65 authorized GPU-minutes.
- `artifacts/toolkit-records.md` binds receipts and sanitized evidence.
- `artifacts/gate-results.md` records package and repository validation.

## Interfaces and Dependencies

The experiment depends on Python, NumPy, PyTorch, the private A10 corpus, the
accepted P1 checkpoint/control records, the revision-2 Daymet calendar profile,
Slurm, and `research/a10/lemhi_toolkit`. It changes no Rust production
interface or public generation profile. Its only downstream interface is the
research conclusion that a future, separately authorized package may test a
frozen-P1 monthly residual adapter.

## Revision note

2026-07-19: completed the plan with authenticated job `1014027` results,
resource/cleanup closure, the scientific HOLD, and the next bounded
architecture recommendation.
