# A10M5R8R2 — Calendar-Missingness Remedy

Status: `SCAFFOLDED`
Date: 2026-07-19
Evidence mode: Mixed
Starting branch and push target: current clean `main`, push `main`

## Objective

Execute the unchanged A10M5R8 climate-statistics experiment while respecting
the accepted A10M1 `source_observed` core-field missingness on an exact
Gregorian date axis.

## Scope

Included: exact eight-year date windows; source-observed precipitation/Tmax/
Tmin masks; at least 28 observed rows per year-month; aggregate-only climate
statistics; a core-field daily proper-score guard; exact P1 control; unchanged
treatment architecture, seed, weights, thresholds, roles, and one-L40 limit.

Excluded: imputation, leap-day synthesis, calendar compression, altered
estimands, new fields, architecture changes, retries, protected roles, and
promotion.

## Authority

R1 spent one failed attempt and cannot retry. Under the operator's end-to-end
execution direction, R2 receives an independent development-only 65-minute
authority: one 60-minute primary and one five-minute exact-node cleanup
reserve. The R1 authority and evidence remain closed and immutable.

## Plan

1. Verify the source-observed mask on synthetic and accepted corpus structure.
2. Publish and hash the corrected source with an exact full Git identity.
3. Execute the inherited toolkit lifecycle and control/treatment comparison.
4. Reconcile the scientific decision, resources, roles, cleanup, campaign
   records, repository gates, and living ExecPlan.

## Execution & dispatch

Codex executes from `/Users/roger/src/cligen-rs`, starting from current
`origin/main` and pushing only `main`. Private state lives beneath
`/Users/roger/.cache/cligen-rs/a10m5r8r2-climate-objective/`.

## Gates

All A10M5R8 gates apply. R2 additionally requires 1,200/240 eligible points,
at least 28 accepted observations in every scored year-month, zero use of
unobserved targets, and a core-only daily proper-score guard.

## Exit criteria

Scientific success and hold outcomes remain exactly A10M5R8's. Missingness,
source, resource, firewall, or cleanup drift fails closed without retry.

## Artifacts

- `artifacts/build_control_records.py` — R2 authority wrapper
- live comparison, decision, toolkit/resource records, review, and gates
