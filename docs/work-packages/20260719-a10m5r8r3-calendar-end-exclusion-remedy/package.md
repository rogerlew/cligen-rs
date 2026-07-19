# A10M5R8R3 — Calendar End-Exclusion Remedy

Status: `EXECUTED-HOLD-CORE-OBJECTIVE-NOT-SUPPORTED`
Date: 2026-07-19
Evidence mode: Mixed
Starting branch and push target: current clean `main`, push `main`

## Objective

Execute A10M5R8 with the exact eight-year target end treated as an exclusive
calendar boundary in dates, missingness masks, and target tensors.

## Scope

Included: the unchanged R2 masked-calendar experiment and one correction from
inclusive to exclusive target-end slices, backed by a synthetic boundary test.
All architecture, objective, stochastic, role, threshold, resource, and
cleanup semantics remain unchanged.

Excluded: every other scientific or operational change, retries, imputation,
new fields, protected roles, and promotion.

## Authority

R2's single attempt is closed. R3 receives an independent development-only
65-minute authority under the operator's end-to-end execution direction: one
60-minute primary and one five-minute exact-node cleanup reserve.

## Plan

1. Publish the exclusive-end correction and boundary test.
2. Freeze the exact full Git/source/asset/authority/plan identity.
3. Execute the unchanged control/treatment job once.
4. Reconcile result, resources, roles, cleanup, records, and gates.

## Execution & dispatch

Codex executes from `/Users/roger/src/cligen-rs`, current `origin/main` to
`main`. Private state lives beneath
`/Users/roger/.cache/cligen-rs/a10m5r8r3-climate-objective/`.

## Gates

All A10M5R8/R2 gates apply. The synthetic document must yield one 2,922-day
eight-year window and exclude its first post-window day.

## Exit criteria

Scientific outcomes are exactly A10M5R8's. Any boundary, authority, firewall,
resource, or cleanup drift holds without retry.

## Artifacts

- `artifacts/build_control_records.py` — R3 authority wrapper
- live comparison, decision, toolkit/resource records, review, and gates

## Disposition

Job `1014025` completed the exact control reconstruction, 40-epoch treatment,
and paired all-240 fit-validation evaluation. The treatment improved the
family-balanced climate score by 14.35%, below the frozen 15% threshold. It
also degraded annual location by 44.74%, monthly interannual dispersion by
11.70%, monthly location by 10.13%, and core daily proper NLL by 110.59%.
Accordingly it did not advance. See `artifacts/execution-disposition.md`.
