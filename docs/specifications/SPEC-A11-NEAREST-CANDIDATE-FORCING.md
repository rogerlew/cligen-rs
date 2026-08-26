# SPEC-A11-NEAREST-CANDIDATE-FORCING — Bounded location test

Status: research-only revision 1; no confirmation or promotion authority

## Purpose

This specification binds A11E2, a single-factor successor to A11E1. It keeps
the circular fixed-block annual law, two-part physical daily adapter, Daymet
calendar estimator, development roles, evaluator, metric set, and common random
numbers fixed. It changes only the 36-field forcing location from a regional
candidate-fit median to one prospectively selected candidate-fit point per
development station.

The registered integrated strategy ID is
`circular_fixed_block_nearest_candidate_forcing_v1`. It wraps the unchanged
published `circular_fixed_block_bootstrap_v1` annual law with five-year blocks
and the unchanged A11E1 daily core.

## Prospective selector

Selector `a11e2-nearest-candidate-coordinate-v1` uses only prepublished
non-target latitude/longitude metadata. Development station coordinates come
from the A8A panel and candidates come from the A10M5R15R1 `candidate_fit`
cohort. Distance is haversine great-circle distance with mean Earth radius
6371.0088 km. The selected point minimizes `(distance_km, point_id UTF-8 byte
order)` across all candidate-fit points; candidate regime is recorded but is
not a selector.

The rule, hashes, and source are published before observed values are read.
There is no result-dependent fallback, distance cutoff, elevation tuning, or
development-target lookup. The cohort has known geographic gaps—most notably
Maine—and distance is reported per station as an applicability limitation.

## Forcing and common random numbers

For a selected candidate point, the forcing location is its 1980–2009 mean
36-state vector under the target development station's registered regional
adapter transform. All scale, covariance, hurdle, count, texture, and model
parameters remain fit from the full target-region candidate-fit cohort exactly
as in A11E1.

To isolate the forcing-location change, annual, hurdle, wet-count, occurrence,
amount, temperature, and range streams reuse the A11E1 circular-block stream
identities. The new strategy ID records changed forcing semantics; its RNG
reference identity is prospectively frozen as
`circular_fixed_block_physical_core_v1`.

## Hypothesis and evaluation

The comparator is the exact A11E1 circular-block member-0 evidence. On the same
20 development stations and 2010–2025 horizon, the hypothesis is supported only
if both of these across-site medians are strictly lower than A11E1:

- monthly equivalent-precipitation mean relative absolute error; and
- monthly temperature mean absolute error in °C.

All 20 new streams must complete with zero daily invariant failures. The
unchanged A11E1 evaluator also reports the other frozen metrics and composite
score. A 1,000-replicate paired site bootstrap is descriptive only. A supported
hypothesis retains this forcing adapter for further exploration; it does not
select a production strategy or authorize confirmation.

## Calendar, roles, and failure

`SPEC-A11-OBSERVED-EXPLORATORY-EXECUTION` revision 1 supplies the exact
candidate/development calendar, mask-normalized estimator, hurdle law, physical
adapter, evaluator, and role boundaries. A11E2 repeats and records the complete
calendar preflight before fitting. Only `candidate_fit` values affect models or
forcing. Development values are scoring targets only. Confirmation remains
sealed.

Unknown or drifting identity, selector mismatch, duplicate station/candidate,
calendar or role failure, missing selected candidate, nonfinite location or
metric, incomplete stream, invariant failure, evidence mismatch, or source not
equal to published `origin/main` fails closed. A failure cannot mutate this
strategy ID in place.
