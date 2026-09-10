# A11E11 — Cohort Temporal-Instability Attribution

Status: `EXECUTED-COMPLETE — STATION_CONCENTRATED_LOADING_INSTABILITY`

Date: 2026-09-10

Evidence mode: retrospective authenticated diagnostic; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Explain whether A11E10's cohort-specific lag-one and low-frequency failures are
broad IID-state behavior, station/loading concentration, or ratio-denominator
sensitivity.

## Scope

Included: exact A11E10 bundle reconstruction, signed annual diagnostics,
station concentration, denominator sensitivity, deterministic decision,
replay, review, gates, and reconciliation. Excluded: new generation, changed
gates, new model laws, selectors, transfer, confirmation, and production.

## Authority

- [SPEC-A11-COHORT-TEMPORAL-INSTABILITY-ATTRIBUTION](../../specifications/SPEC-A11-COHORT-TEMPORAL-INSTABILITY-ATTRIBUTION.md)
- A11E10 rejected fresh validation and authenticated replay bundle
- operator authorization to scaffold and execute A11E11

## Plan

1. Freeze diagnostic thresholds and executable analysis.
2. Publish exact source, execute, and independently replay.
3. Review, run gates, and close campaign records.

## Data calendar and missingness preflight

No new calendarized data are loaded. Authenticate A11E10's completed preflight
and bundle; confirmation access must remain false.

## Gates

- exact A11E10 input hashes and 640 identities;
- signed-statistic reconstruction and frozen classification tests;
- byte-identical evidence and decision replay;
- standard Cargo gates, link validation, and `git diff --check`.

## Exit criteria

Close with one frozen attribution disposition or an exact integrity HOLD.

## Artifacts

- `artifacts/execution-manifest-v1.json`, `analyze.py`, `test_analyze.py`.
- `artifacts/review.md` — pending execution review.

## Outcome

Execution and byte-identical replay completed from published commit
`1bc31db5fe5748e4808a5819406f5b2741438834`. All 640 A11E10 records and the three frozen failure surfaces were
authenticated; confirmation remained sealed.

All three failures are station-concentrated: two or three stations account for
half of positive deterioration on each surface. Cohort 2 lag-one and cohort 3
low-frequency failures are nevertheless broad by count, each worsening 11
station medians and 51.875% of pairs. Cohort 3 lag-one is not broad and exceeds
the `1.05` bound by only `0.00054` absolute error, making that crossing
denominator-sensitive.

The largest contributors differ by cohort: `or350412` leads cohort-2 lag-one;
`la160549` leads both cohort-3 failures, followed by `id101022` for cohort-3
low-frequency. The disposition is `STATION_CONCENTRATED_LOADING_INSTABILITY`.
A11E10 remains rejected. A bounded successor should test loading magnitude and
annual-signal influence at these stations before proposing a new temporal law.
