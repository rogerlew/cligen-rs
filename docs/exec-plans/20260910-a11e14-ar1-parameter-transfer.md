# A11E14 AR(1) Parameter-Transfer ExecPlan

Status: scaffolded

## Purpose / Big Picture

Replace A11E13's observed-target oracle with the simplest role-correct estimator.

## Progress

- [x] 2026-09-10: freeze firewall, estimator hierarchy, and gates.
- [ ] Publish, execute, replay, review, and close.

## Surprises & Discoveries

- Candidate-fit support contains 1,200 thirty-year objects across the six
  established strata, sufficient for median estimators without regression.

## Decision Log

- Global median is primary; regime median is the only fallback.
- Development targets never enter fitting.

## Outcomes & Retrospective

Pending execution.

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

2026-09-10: initial scaffold.
