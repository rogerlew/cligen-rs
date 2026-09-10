# SPEC-A11-STATION-LOADING-SIGNAL-INFLUENCE

Status: research-only revision 1

Owning work package:
`docs/work-packages/20260910-a11e12-station-loading-signal-influence/`

## Purpose and boundary

A11E12 tests whether A11E11's station-concentrated deterioration has one common,
prospectively definable loading-magnitude or loading-shape explanation. It uses
only authenticated A11E10/A11E11 artifacts and cannot revise A11E10.

## Diagnostics

For each station compute loading L2 norm, maximum absolute loading, absolute
annual-weighted loading, max/L2 concentration, cyclic roughness/L2, fitted
eigenvalue, and median rendered annual-signal standard deviation relative to
observed annual-temperature standard deviation. For each of the three failed
surfaces, aggregate candidate-minus-faithful absolute-error change by station.

Compute Pearson correlations across the 20 stations between each loading/signal
predictor and each surface's station-median deterioration. A common association
requires absolute correlation at least `0.50` on all three surfaces with the
same sign. Magnitude predictors and shape predictors are adjudicated separately.

For each failed surface, recompute its median ratio after excluding each station
individually. Record every station whose exclusion makes the ratio at most
`1.05`, and whether one common exclusion clears all surfaces. These are
diagnostics only; station deletion is not an admissible model remedy.

## Disposition

- `COMMON_LOADING_MAGNITUDE_ASSOCIATION` when a magnitude predictor meets the
  common-association rule;
- `COMMON_LOADING_SHAPE_ASSOCIATION` when no magnitude predictor passes and a
  shape predictor does;
- `STATION_SPECIFIC_NO_COMMON_LOADING_RULE` when no predictor passes, no common
  exclusion clears all failures, and at least one surface has a clearing
  single-station exclusion;
- `NO_SIMPLE_LOADING_ATTRIBUTION` otherwise.

Only a common association may motivate one frozen normalization hypothesis.
No result authorizes tuning, transfer, confirmation, or production.

## Replay

Execution and replay deterministically analyze exact hash-pinned inputs.
Evidence and decision must be byte-identical.
