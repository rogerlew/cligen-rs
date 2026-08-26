# SPEC-A11-MULTI-MEMBER-FORCING-STABILITY — Fixed-adapter stability screen

Status: research-only revision 1; no confirmation or promotion authority

## Purpose

This specification binds A11E3, the prospectively fixed multi-member successor
to A11E2. It asks whether A11E2's two across-site median improvements persist
when the stochastic member changes. It does not refit, tune, select, or modify
either forcing adapter.

The compared integrated strategies are
`circular_fixed_block_physical_core_v1` (regional-median forcing) and
`circular_fixed_block_nearest_candidate_forcing_v1` (A11E2 nearest-candidate
forcing). Both use `circular_fixed_block_bootstrap_v1`, five-year blocks, and
the unchanged A11E1 physical daily core.

## Frozen comparison grid

The development grid is exactly 20 registered stations, member IDs 0 through
7, and the two forcing adapters: 320 complete strategy/site/member cells over
2010–2025. Member 0 is an authentication anchor and must reproduce the closed
A11E1 regional-median and A11E2 nearest-candidate stream summaries and metrics.
Members 1–7 are the new stability evidence.

For member `m` and primary metric `k`, the estimand is

`delta[m,k] = median_site(nearest[m,k]) - median_site(region[m,k])`.

The primary metrics remain:

- monthly equivalent-precipitation mean relative absolute error; and
- monthly temperature mean absolute error in °C.

`STABLE_FOR_EXPLORATION` requires all 320 cells to be complete and finite,
zero daily invariant failures, confirmation access false, exact member-0
replay, and all 16 primary deltas strictly below zero. A complete valid run
missing any strict inequality is `NOT_STABLE_FOR_EXPLORATION`. Ties fail the
strict rule. Integrity, completeness, nonfinite, invariant, replay, source, or
confirmation-firewall failure fails closed and produces no scientific
disposition. Secondary metrics and site/member summaries are descriptive only.

## Common random numbers

Both forcing arms receive identical random identities for each station and
member. Annual targets use experiment `a11e1-development-{station}`, strategy
`circular_fixed_block_bootstrap_v1`, the fixed member ID, and domain
`annual_target`. The hurdle key remains
`a11e1-integrated-v1\0{station}\0circular_fixed_block_physical_core_v1\0{member}\0month_hurdle`.
The five daily domains use experiment `a11e1-core-{station}`, the circular-block
strategy, and ordinal
`member*3840 + site_ordinal*192 + year_index*12 + month_index`. This preserves
all member-0 identities exactly and makes member/site/month identities
collision-free. Common RNG means common inputs to the two arms; it does not
claim identical draw consumption or stationwise dominance.

## Frozen data, selector, and adapters

A11E3 inherits A11E2's coordinate-only selector, exact station-to-candidate
mapping, candidate-fit-only 1980–2009 fit, target-region adapter transform,
regional-median locations, nearest-candidate locations, model parameters,
calendar estimator, evaluator, metrics, roles, and 20-station ordering. It
repeats the complete A10 calendar and missingness preflight before generation.
The source transform is `daymet_official_365_v1`; the normalized estimator is
`daymet_mask_normalized_month_v1`. The selector remains haversine distance
with mean Earth radius 6371.0088 km and point-ID tie-break. No distance cutoff,
elevation term, fallback, or output-dependent routing is permitted.

## Interpretation and failure boundary

The same development targets have informed multiple A11 stages. Even a stable
result is exploratory mechanism evidence only: it does not select a production
strategy, authorize confirmation, or justify tuning from member/site results.
Known long nearest-candidate distances and geographic heterogeneity remain
reported limitations. Confirmation targets remain sealed.
