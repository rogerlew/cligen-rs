# A11E14 — AR(1) Parameter Transfer

Status: `EXECUTED-COMPLETE — REGIME_PHI_TRANSFER_SUPPORTED`

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
  `execution-receipt-v1.json`.
- `artifacts/review.md`, `artifacts/test-results.md`.

## Outcome

Execution and byte-identical replay completed from exact published commit
`c5b60cbc5d6a12122c880e435f50b94347d92555`. Fitting used exactly 1,200
candidate-fit objects; 240 fit-validation objects were excluded, the 20
development objects were evaluation-only, and confirmation remained sealed.

Both estimators improved development `phi` MAE over the `phi=0` baseline
(`0.17852` global and `0.18876` regime versus `0.21079`) and passed the overall
and all four downstream cohort gates. The global estimator failed its frozen
leave-source-regime-out stability check in three of six regimes. Every regime
estimator hash-half median difference was below `0.15`, so the ordered fallback
passed. Its downstream annual-dispersion, lag-one, and low-frequency median
error ratios were `0.11447`, `0.62279`, and `0.79327`; all 640 pairs improved
annual dispersion and monthly means remained exactly preserved.

Disposition: `REGIME_PHI_TRANSFER_SUPPORTED`. This authorizes only fresh-burn
validation of the transferred regime AR(1) law. It does not authorize
confirmation, public integration, production, or a default change.
