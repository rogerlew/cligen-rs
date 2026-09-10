# A11E12 — Station Loading and Signal-Influence Attribution

Status: `SCAFFOLDED`

Date: 2026-09-10

Evidence mode: retrospective authenticated diagnostic; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Determine whether one common loading magnitude or shape explains A11E10's
station-concentrated temporal deterioration.

## Scope

Included: loading/eigenvalue/signal summaries, cross-station associations,
leave-one-station-out diagnostics, deterministic classification, replay,
review, gates, and reconciliation. Excluded: fitting a cap, deleting stations,
new burns, new temporal laws, transfer, confirmation, and production.

## Authority

- [SPEC-A11-STATION-LOADING-SIGNAL-INFLUENCE](../../specifications/SPEC-A11-STATION-LOADING-SIGNAL-INFLUENCE.md)
- A11E10 and A11E11 authenticated artifacts
- operator authorization to scaffold and execute A11E12

## Plan

1. Freeze predictors, association threshold, leave-one-out rules, and code.
2. Publish exact source, execute, replay, review, and close.

## Data calendar and missingness preflight

No new data load. Authenticate the completed A11E10 preflight and inputs;
confirmation access remains false.

## Gates

- exact dependency hashes and complete 20-station/640-record identity;
- deterministic association and leave-one-out tests;
- byte-identical replay, hashes, review, Cargo gates, links, and diff check.

## Exit criteria

Close with one frozen attribution disposition or exact integrity HOLD.

## Artifacts

- `artifacts/execution-manifest-v1.json`, `analyze.py`, `test_analyze.py`.
- `artifacts/review.md` — pending review.
