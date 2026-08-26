# A11E2 nearest candidate-fit forcing ExecPlan

## Purpose

Run the smallest falsifiable successor to A11E1 by changing only forcing
location for the circular-block arm.

## Progress

- [x] 2026-08-25: inherited A11E1's independent successor recommendation.
- [x] 2026-08-25: verified coordinate metadata and candidate-fit coverage.
- [x] 2026-08-25: scaffolded and independently cleared exact source for publication.
- [ ] Preflight, fit, generate, evaluate, and replay.
- [ ] Review, gate, reconcile, commit, and push terminal evidence.

## Decisions and limitations

- Geographic distance alone is the selector. Adding elevation weights would
  introduce an unfrozen tuning scale and a second factor.
- Candidate regime is not a selector. The candidate supplies location only;
  target-region anomaly/covariance/daily laws remain fixed.
- Sparse cohort geography is accepted and reported rather than hidden behind a
  fallback. Maine's nearest candidate is expected to be materially distant.
- A11E1 circular-block RNG identities are reused to isolate location.

## Execution

Publish implementation, manifest, schema, and tests to `origin/main` before
observed access. Runtime verifies all source and predecessor/input hashes,
materializes the metadata-only mapping, repeats calendar preflight, fits the
unchanged candidate models, generates 20 streams, evaluates the two primary
medians and frozen secondary metrics, and writes compact atomic JSON evidence.

Use the bundled Python 3.12/NumPy 2.3.5 runtime. Required gates are recorded in
the package. Replay must reproduce every scientific output byte-for-byte; only
elapsed time in the execution receipt may differ.

## Outcome

Pending execution.
