# A11E7 — Faithful Temperature QC Attribution

Status: `EXECUTING`

Date: 2026-08-28

Evidence mode: prospective observed-target development ablation; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Measure the contribution of faithful `RANSET` conditioning to temperature
underdispersion before choosing the base for a temperature temporal overlay.

## Authority

- [SPEC-A11-FAITHFUL-TEMPERATURE-QC-ATTRIBUTION](../../specifications/SPEC-A11-FAITHFUL-TEMPERATURE-QC-ATTRIBUTION.md)
- A11E6 faithful baseline evidence
- A11E6S static source review
- implemented, provenance-declared `qc_filter` seam
- operator authorization to scaffold and execute A11E7

## Scope

Included: 20 stations, 32 burns, conditioned/off paired generation, observed
temperature scoring, process-QC attribution, cryptographic provenance, exact
A11E6 overlap replay, full replay, review, gates, and reconciliation.

Excluded: generator changes, overlay implementation, precipitation decisions,
station selection changes, confirmation, promotion, defaults, and WEPP claims.

The first exact-source attempt found a quality-report relational-validator
defect at station `co050130`, burn `53`: one valid correlation estimator was
undefined while the other was defined. The published schema permits the two
nullable estimators independently, and their estimators have independent
finite-result gates. A bounded specification, validator, and regression-test
correction is therefore included before restarting the source-bound run. This
does not alter generated climate values or the frozen A11E7 estimand.

## Plan and gates

1. Freeze specification, manifest, schema, executor, and synthetic tests.
2. Publish exact execution source on `origin/main`.
3. Build release CLIGEN and execute the 1,280-stream grid.
4. Replay scientific outputs byte-identically, review, run gates, and close.

The quality-report validator correction changes one production Rust function,
so the workspace coverage/CRAP gates are required.

## Resource bound

One execution and one replay, each limited to 1,280 local CPU streams. No
external service or scarce accelerator is used.

## Exit

Close with the frozen attribution disposition or an exact integrity HOLD.
