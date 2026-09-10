# A11E11 Cohort Temporal-Instability Attribution ExecPlan

Status: complete

## Purpose / Big Picture

Attribute A11E10's cohort instability before proposing another thermal law.

## Progress

- [x] 2026-09-10: freeze diagnostics and disposition vocabulary.
- [x] 2026-09-10: publish exact source, execute, replay byte-identically,
  review, run gates, and close.

## Surprises & Discoveries

- A11E10 passed overall but failed two of four prospectively frozen cohort
  stability gates.

## Decision Log

- Reuse authenticated evidence; do not search more burns.
- Preserve A11E10's rejection and label all inference retrospective.

## Outcomes & Retrospective

The disposition is `STATION_CONCENTRATED_LOADING_INSTABILITY`. Two or three
stations explain half of positive deterioration on every failed surface,
although two surfaces are also broad by station and pair counts. The next
minimal diagnostic is station loading/signal influence, not a new temporal law
or another burn search.

## Context and Orientation

Package: `docs/work-packages/20260910-a11e11-cohort-temporal-instability-attribution/`.

## Plan of Work

Authenticate A11E10, reconstruct signed annual statistics, classify the three
failed surfaces, replay exactly, and reconcile records.

## Concrete Steps

Publish scaffold to `main`; run `analyze.py` with the exact source commit;
preserve outputs; rerun with `--replay`; compare and close.

## Validation and Acceptance

Require complete identities, finite diagnostics, exact replay,
confirmation=false, review GO, and repository gates.

## Idempotence and Recovery

Outputs are deterministic atomic JSON and may safely be regenerated.

## Artifacts and Notes

No raw climates or external compute are used.

## Interfaces and Dependencies

No public or production interface changes.

## Revision Note

2026-09-10: initial scaffold.

2026-09-10: attribution executed and replayed; station concentration was the
frozen terminal classification.
