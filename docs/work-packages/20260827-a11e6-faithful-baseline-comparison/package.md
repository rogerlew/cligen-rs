# A11E6 — Faithful Baseline Comparison

Status: `SCAFFOLDED`

Date: 2026-08-27

Evidence mode: prospective observed-target development comparison; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Determine whether the circular-block experiment is better than the existing
faithful/legacy cligen-rs implementation against observed development data.

## Authority

- [SPEC-A11-FAITHFUL-BASELINE-COMPARISON](../../specifications/SPEC-A11-FAITHFUL-BASELINE-COMPARISON.md)
- closed A11E3, A11E5, and A11E5D evidence
- A8A exact parameter identities
- operator authorization to scaffold and execute

## Scope

Included: exact faithful release build, 160 faithful streams, 14-metric paired
comparison, directional variance context, cryptographic provenance, replay,
review, gates, and record reconciliation.

Excluded: generator changes, selector changes, tuning, Gaussian decision
baseline, confirmation, production, CLI changes, and WEPP claims.

## Plan and gates

1. Freeze the specification, manifest, schema, executor, and arithmetic tests.
2. Publish the exact source on `origin/main`.
3. Build and run faithful CLIGEN on the frozen 20-by-eight grid.
4. Replay scientific outputs byte-identically, review, run repository gates,
   and reconcile records.

Required gates are strict source and dependency identity, calendar/missingness
preflight, exact station and `.par` identity, fresh locked release build, 160
finite faithful rows, exact circular evidence replay, full cryptographic
receipts, confirmation=false, deterministic replay, review without P0/P1,
standard Cargo gates, `git diff --check`, and link validation. No production
Rust function changes occur, so coverage/CRAP is not triggered.

## Resource bound

One execution and one replay, each bounded to 160 local CPU streams. No
external service or scarce accelerator is used.

## Exit

Close with the frozen comparative disposition or an exact integrity HOLD.
