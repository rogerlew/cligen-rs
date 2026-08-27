# A11E5 full interannual family stability

## Purpose / Big Picture

Determine whether circular block resampling improves interannual behavior over
the Gaussian law across repeated members, and distinguish safe universal use
from a mixed result that would require a future prospective router.

## Progress

- [x] 2026-08-27: objective and frozen decision recorded.
- [x] 2026-08-27: Published prospective source `2eb5748`.
- [x] 2026-08-27: Executed and byte-identically replayed the 320-stream grid.
- [x] 2026-08-27: Reviewed evidence and ran repository gates.
- [x] 2026-08-27: Reconciled package, catalog, roadmap, and outcome.

## Surprises & Discoveries

- Member 0 repeated A11E1's favorable annual-temperature dispersion result,
  but all seven additional members reversed it.
- Circular block improved 88.75% of combined family scores despite failing two
  of ten aggregate metric noninferiority conditions.

## Decision Log

- 2026-08-27: Evaluate ten dispersion/dependence errors; keep nearest forcing
  and daily generation fixed.
- 2026-08-27: Define material change as five percent and report both pairwise
  harm and aggregate family noninferiority.

## Outcomes & Retrospective

Execution was complete, deterministic, and integrity-clean. The treatment
strongly improved precipitation dispersion but was not universally viable
because annual temperature dispersion and precipitation lag-one error missed
the frozen aggregate bounds. The next falsifiable direction is a prospective
field-wise/dependence composition, not an outcome-selected station router.

## Context and Orientation

A11E1 compared the laws for one member. A11E2 selected frozen nearest forcing.
A11E3 evaluated forcing location across eight members but did not compare the
two stochastic laws or score the full interannual family. The implementation
and evidence live under
`docs/work-packages/20260827-a11e5-interannual-family-stability/`.

## Plan of Work

Create a source-bound Python evaluator that imports the authenticated A11E
research implementation, repeats calendar preflight and fitting, generates the
two arms for every station/member, computes the frozen metrics, and writes
atomic compact evidence and decision receipts.

## Concrete Steps

From the repository root, run the synthetic tests and manifest validation,
commit and push the prospective source, execute using that exact commit, replay
after preserving the first outputs, then run the Rust repository gates.

## Validation and Acceptance

Acceptance requires the exact 20x8x2 grid, finite metrics, no invariants,
confirmation=false, correct decision arithmetic, byte-identical replay, and
all repository gates.

## Idempotence and Recovery

Outputs use atomic replacement. Re-execution is safe only from the same source
commit and must reproduce scientific files byte-for-byte. A partial file is
not evidence and may be replaced by the same authenticated run.

## Artifacts and Notes

The manifest, schema, executor, tests, evidence, decision, receipt, review, and
test transcript are stored in the package artifacts directory.

## Interfaces and Dependencies

Python 3.12.13 and NumPy 2.3.5 are frozen. A11E1 supplies models, calendar
loading, and daily primitives; A11E2 supplies the nearest-candidate mapping.
No production Rust interface changes.
