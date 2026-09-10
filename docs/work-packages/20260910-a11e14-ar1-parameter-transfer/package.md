# A11E14 — AR(1) Parameter Transfer

Status: `SCAFFOLDED`

Date: 2026-09-10

Evidence mode: role-separated observed transfer feasibility; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Determine whether A11E13's station AR(1) persistence can be transferred from
candidate-fit data without using target-station annual observations in fitting.

## Scope

Included: global and regime median estimators, strict fit/development firewall,
calendar preflight, phi and downstream gates, stability, replay, review, and
closure. Excluded: regression, nearest donors, new CLIGEN streams, confirmation,
public integration, production, and defaults.

## Authority

- [SPEC-A11-AR1-PARAMETER-TRANSFER](../../specifications/SPEC-A11-AR1-PARAMETER-TRANSFER.md)
- A11E13 `AR1_FEASIBLE_TRANSFER_REQUIRED`
- operator authorization to scaffold and execute A11E14

## Plan

1. Freeze role firewall, estimators, stability, and decisions.
2. Publish exact source, execute, replay, review, and reconcile.

## Data calendar and missingness preflight

Authenticate SPEC-A10-CORPUS candidate-fit and development calendars before
analysis: 1,200 fit objects at 10,958/10,950 rows and 20 development objects at
5,844/5,840 rows, with exact masks and confirmation=false.

## Gates

- exact role separation and input hashes;
- deterministic estimator and stability tests;
- 640 downstream pairs per estimator and four-cohort decisions;
- byte-identical replay, repository gates, links, and diff check.

## Exit criteria

Close with one frozen transfer disposition or exact integrity HOLD.

## Artifacts

- `artifacts/execution-manifest-v1.json`, `analyze.py`, `test_analyze.py`.
- `artifacts/calendar-missingness-preflight-v1.json`, `phi-fit-v1.json`.
- `artifacts/transfer-evidence-v1.json`, `transfer-decision-v1.json`, and
  `execution-receipt-v1.json` — pending execution.
- `artifacts/review.md` — pending review.
