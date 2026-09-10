# SPEC-A11-CENTERED-THERMAL-PROSPECTIVE-VALIDATION

Status: retired research record — candidate retired by A11E13

Owning work package:
`docs/work-packages/20260910-a11e10-centered-thermal-prospective-validation/`

## Purpose and boundary

A11E10 prospectively validates the single correction supported by A11E9: a
temperature-only rank-one annual residual whose 16 annual states are centered
and whose rendered tenths sum exactly to zero within every month. It adds no
selector or model component. Confirmation and production remain sealed.

## Fresh identities

The validation uses the frozen 20 development stations and sixteen-year Daymet
target, but four new ordered cohorts of eight faithful burns. All 32 burns are
disjoint from A11E8/A11E9. Candidate annual states use the A11E8
SplitMix64/Box-Muller algorithm with the new ASCII domain including terminal
NUL `cligen-rs/a11e10/centered-thermal-state-v1\0`, station ID, candidate model
ID, cohort root seed, and candidate index.

## Fit and overlay

For each station, fit the A11E8 rank-one residual loading from observed monthly
temperature covariance minus the mean covariance of all 32 fresh faithful
streams. Fit occurs before constructing or scoring any candidate. Ambiguous or
nonpositive leading eigenpairs retain A11E8 fail-closed/zero semantics.

For each candidate, subtract the chronological binary64 mean from its 16
states. Form monthly deltas, round tenths ties-to-even, and deterministically
adjust tenths until each month's 16 deltas sum exactly to zero, minimizing the
incremental absolute error with chronological year tie-breaking. Add the same
delta to Tmax, Tmin, and dewpoint. Scoring the equivalent monthly matrix is
exact because each daily value in a month receives the same rendered delta.

## Data preflight

Use `daymet_official_365_v1` and `daymet_mask_normalized_month_v1` under
SPEC-A10-CORPUS. Require 20 development objects, 5,844 axis rows, 5,840
observed rows, four expected masked dates, mask-based eligibility, and no
confirmation access before generation.

## Decision

Apply A11E8's component gates to all 640 fresh pairs: annual-temperature
dispersion error ratio at most `0.90`; each other registered temperature ratio
at most `1.05`; at least one third of pairs improve annual dispersion; no
station median annual-error ratio above `1.25`.

Stability additionally requires each 160-pair cohort to meet the `0.90` annual
ratio, all `1.05` noninferiority ratios, and one-third improvement fraction.
The disposition is `CENTERED_THERMAL_COMPONENT_RETAINED_FOR_TRANSFER` only if
both overall and stability gates pass; otherwise it is
`CENTERED_THERMAL_COMPONENT_REJECTED`.

Retention authorizes only parameter-transfer feasibility. It does not
authorize a selector, hydroclimate state, confirmation, public integration,
production, or a default change.

## Replay and provenance

The exact-source execution publishes an authenticated compact bundle of fresh
faithful monthly matrices, observations, fitted loadings, and state identities.
Replay reconstructs, scores, and decides all candidates from that bundle.
Preflight, loading bundle, evidence, and decision must be byte-identical.
