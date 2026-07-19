# A10M5R4 — Realized Temporal-Dispersion Adjudication

Status: `EXECUTED-HOLD-A10-REVISED-STOCHASTIC-PRISM-COMPARATOR`
Date: 2026-07-18
Evidence mode: Static prerequisite audit; no generated-output access
Starting branch and push target: `main` at `f1f4791`, push `main`

## Objective

Adjudicate realized generated calendar-month and interannual behavior for the
A10M5R3R1 P1/P2 capacity pair against observations, faithful CLIGEN, and the
independently versioned revised stochastic-plus-PRISM comparator required by
ADR-0005 and SPEC-A10-REFINEMENT-TRAJECTORY.

## Boundary

This package may audit the accepted corpus and predecessor evidence, but the
comparison design cannot be frozen or executed until the required comparator
has an exact specification, source-data identity, implementation, and
validation record. No neural output was accessed; no neural refit, neural
generated stream, protected role, confirmation target, Slurm allocation, or
remote mutation is authorized by this prerequisite audit.

## Plan

1. Bind A10M5R3R1's accepted `lognormal_wet_v2` P1/P2 identities.
2. Inventory the accepted A10M1 transfer and registered research surfaces for
   a versioned revised stochastic-plus-PRISM comparator.
3. Hold before generated-output access if the comparator is absent.
4. Dispatch the smallest corrective package that publishes and validates the
   missing comparator without scoring P1/P2.

## Gates

- the A10M5R3 parent hold and A10M5R3R1 accepted pair remain unchanged;
- the audit distinguishes Daymet/USCRN observations from PRISM inputs;
- no Daymet-derived monthly normal is labeled PRISM;
- no P1/P2 temporal output is generated or read;
- protected development-selection and confirmation roles remain sealed; and
- repository gates pass after the corrective package record is complete.

## Exit and terminal result

`HOLD-A10-REVISED-STOCHASTIC-PRISM-COMPARATOR`

The accepted A10M1 transfer has Daymet and USCRN objects but no PRISM object.
At entry there was no registered stochastic-plus-PRISM model identity,
machine-readable station input, executable generator, or validation evidence.
Proceeding would either omit the comparator or mislabel another monthly
surface as PRISM. The package therefore stopped before any neural output
access or allocation.

The directly corrective successor is
[A10M5R4R1](../20260718-a10m5r4r1-stochastic-prism-comparator/package.md),
which owns the independent comparator. Temporal adjudication must later resume
under a fresh package identifier; this hold is immutable.

## Artifacts

- `artifacts/prerequisite-audit.json` — machine-readable absence and role audit;
- `artifacts/terminal.md` — concise disposition and successor boundary; and
- `artifacts/verify.py` — fail-closed audit verifier.
