# A11E12 Station Loading and Signal-Influence ExecPlan

Status: complete

## Purpose / Big Picture

Test whether A11E11's concentration supports one simple loading correction.

## Progress

- [x] 2026-09-10: freeze predictors and attribution rules.
- [x] 2026-09-10: publish exact source, execute, replay byte-identically,
  review, run gates, and close.

## Surprises & Discoveries

- A11E11 found two or three stations account for half of deterioration on each
  surface, but the leading stations differ by cohort.

## Decision Log

- Require one predictor to explain all three surfaces before considering a
  common normalization.
- Treat station exclusions as diagnostics, never a remedy.

## Outcomes & Retrospective

No common loading magnitude or shape explains all three failures, and no
single station exclusion clears them. The rank-one thermal line has no simple
loading normalization supported by this evidence and should be retired.

## Context and Orientation

Package: `docs/work-packages/20260910-a11e12-station-loading-signal-influence/`.

## Plan of Work

Authenticate A11E10/A11E11, compute loading and signal predictors, associate
them with deterioration, run leave-one-out diagnostics, replay, and close.

## Concrete Steps

Publish scaffold to `main`; execute and replay `analyze.py` from that exact
commit; compare artifacts and reconcile records.

## Validation and Acceptance

Require complete identity, finite diagnostics, byte-identical replay,
confirmation=false, review GO, and all repository gates.

## Idempotence and Recovery

Analysis writes deterministic atomic JSON and may safely be rerun.

## Artifacts and Notes

No new climates or external resources are consumed.

## Interfaces and Dependencies

No public or production interface changes.

## Revision Note

2026-09-10: initial scaffold.

2026-09-10: closed `STATION_SPECIFIC_NO_COMMON_LOADING_RULE` after exact replay.
