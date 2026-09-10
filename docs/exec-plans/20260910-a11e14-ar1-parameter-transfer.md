# A11E14 AR(1) Parameter-Transfer ExecPlan

Status: complete — `REGIME_PHI_TRANSFER_SUPPORTED`

## Purpose / Big Picture

Replace A11E13's observed-target oracle with the simplest role-correct estimator.

## Progress

- [x] 2026-09-10: freeze firewall, estimator hierarchy, and gates.
- [x] 2026-09-10: publish exact source, execute, byte-replay, review, and close.

## Surprises & Discoveries

- Candidate-fit support contains 1,200 thirty-year objects across the six
  established regimes, sufficient for median estimators without regression.
- Panel strata and observed-corpus regimes differ; the first attempt failed
  closed before evidence and revision 2 froze the shared corpus regime field.
- Both estimators passed downstream gates, but only regime median passed its
  frozen stability rule.

## Decision Log

- Global median is primary; regime median is the only fallback.
- Development targets never enter fitting.

## Outcomes & Retrospective

The regime median is transferable under the frozen development protocol. The
global median failed exclusion stability in arid-boundary, cold, and
non-monsoonal-semi-arid regimes. Fresh-burn validation is the next bounded
stage; confirmation and production remain unauthorized.

## Context and Orientation

Package: `docs/work-packages/20260910-a11e14-ar1-parameter-transfer/`.

## Plan of Work

Authenticate calendars, fit candidate-role phi summaries, evaluate development
phi and downstream climate metrics, replay, and reconcile records.

## Concrete Steps

Publish scaffold on `main`; execute and replay from the exact commit; compare
outputs and close.

## Validation and Acceptance

Require role separation, exact counts, finite estimates, stability, complete
downstream gates, byte replay, confirmation=false, and repository gates.

## Idempotence and Recovery

Analysis writes atomic deterministic JSON and may safely be rerun.

## Artifacts and Notes

No new CLIGEN streams or external resources are used.

## Interfaces and Dependencies

No public or production interface changes.

## Revision Note

2026-09-10: initial scaffold; revision 2 corrected pre-evidence grouping
authority; exact-source execution and replay closed the package.
