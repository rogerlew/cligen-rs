# A11E12 — Station Loading and Signal-Influence Attribution

Status: `EXECUTED-COMPLETE — STATION_SPECIFIC_NO_COMMON_LOADING_RULE`

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

## Outcome

Execution and byte-identical replay completed from published commit
`116022b60f1324be7e4c7435ef58f64eca1ed284`. No magnitude or shape predictor
met the frozen common-association rule. All cross-surface magnitude
correlations were small (absolute maximum `0.234`), and shape correlations
changed sign or remained below `0.342`.

No single station exclusion cleared all failures. Individual exclusions clear
only the already denominator-sensitive cohort-3 lag-one crossing; none clears
cohort-2 lag-one or cohort-3 low-frequency. The disposition is
`STATION_SPECIFIC_NO_COMMON_LOADING_RULE`, and no normalization hypothesis is
authorized. The current rank-one thermal line should be retired rather than
cap-tuned. A11E10 remains rejected.
