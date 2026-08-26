# A12R1 — Localizability-Aware Station Selection

Status: `SCAFFOLDED`

Date: 2026-08-26

Evidence mode: observed fit-validation; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Determine whether a prospectively frozen full-localization eligibility filter
restores complete automatic donor coverage and, only then, whether current or
elevation/PRISM scoring improves on closest eligible selection.

## Trigger

A12 stopped at `EXECUTED-HOLD-UNLOCALIZABLE-DONOR`: site
`p+3325_-11650` made all three raw policies select `ca040983.par`. Its June
`P(W/W)=P(W/D)=0` defines an all-dry stationary state, but gives zero source
expected precipitation for a positive PRISM target and an undefined `0/0`
persistence ratio. A12 emitted no scientific policy disposition.

## Authority

- [SPEC-A12R1-LOCALIZABILITY-AWARE-SELECTION](../../specifications/SPEC-A12R1-LOCALIZABILITY-AWARE-SELECTION.md)
- [A12 failure receipt](../20260826-a12-station-selection-heuristic-evaluation/artifacts/execution-failure-receipt-v1.json)
- [SPEC-A12-STATION-SELECTION-EVALUATION](../../specifications/SPEC-A12-STATION-SELECTION-EVALUATION.md)

Immutable predecessor: A12 source commit
`d94f6eab53c9103c797b332ae51aea3a87341bcb`; failure-receipt file SHA-256
`ba103ab7d50fbc510910f980181aec9f3a8c188a05cdbee2b7780f7ce567fa7f`.

## Scope and plan

1. Freeze a new source-bound manifest, exact feasibility predicate, all-ten
   rank semantics, seed/domain, evaluator, schemas, and tests.
2. Independently review and publish the prospective source.
3. Authenticate inputs, execute the complete 2,400 candidate feasibility
   census, and stop if any site has no eligible donor.
4. If coverage is complete, execute and replay the three-policy quality
   comparison under the unchanged A12 structural estimand.
5. Review evidence and reconcile the package without changing runtime defaults
   or opening confirmation.

## Exit

`EXECUTED-COMPLETE` requires a complete eligibility matrix, either an explicit
zero-eligible HOLD or a frozen quality disposition, byte-identical replay,
cryptographic provenance, all repository gates, and independent GO.

## Current boundary

This package is scaffolded but not executed. It records the recommended
corrective successor without retroactively changing A12 after observed
failure evidence.
