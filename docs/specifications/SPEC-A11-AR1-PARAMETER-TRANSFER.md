# SPEC-A11-AR1-PARAMETER-TRANSFER

Status: research-only revision 2

Owning package:
`docs/work-packages/20260910-a11e14-ar1-parameter-transfer/`

## Purpose and role firewall

A11E14 tests whether A11E13's oracle station `phi` can be estimated without
target-station annual observations. All fitting uses only 1,200 authenticated
`candidate_fit` Daymet objects from 1980–2009. The 20 development objects from
2010–2025 are evaluation-only. Confirmation remains sealed.

## Frozen estimators

Compute each candidate-fit object's weighted annual mean-air-temperature series
and clipped lag-one correlation in `[-0.75, 0.75]`.

1. `global_median_phi`: median across all candidate-fit objects.
2. `regime_median_phi`: median within the target station's authenticated
   observed-corpus regime. This is evaluated only as the ordered fallback.

No target normals, target annual observations, nearest-neighbor search,
regression, routing, or outcome-tuned fallback enters fitting.

## Admission

For each estimator, reconstruct all 640 A11E10 candidates using the A11E13
AR(1), centering, sample normalization, and exact zero-sum tenths semantics.
Require:

- development `phi` MAE strictly below the `phi=0` baseline;
- the A11E13 overall component gates;
- every A11E10 cohort independently passes its metric and improvement gates.

Global transfer stability additionally requires that, for every development
regime, the median trained after excluding all candidate-fit objects from that
regime has lower `phi` MAE on that regime's development stations than
`phi=0`. Regime transfer stability requires each regime's two deterministic
point-ID hash halves to produce medians differing by at most `0.15`.

Admit global first if it passes. Otherwise admit regime median if it passes.
The dispositions are `GLOBAL_PHI_TRANSFER_SUPPORTED`,
`REGIME_PHI_TRANSFER_SUPPORTED`, or `AR1_NONDEPLOYABLE_RETIRE_THERMAL_CAMPAIGN`.
A supported estimator authorizes only fresh-burn transferred-AR(1) validation.

## Provenance and replay

Calendar/missingness preflight must authenticate 1,200 candidate-fit objects
with 10,958 axis and 10,950 observed rows plus 20 development objects with
5,844 axis and 5,840 observed rows. Evidence and decision replay byte-identically.
