# SPEC-A11-OBSERVED-EXPLORATORY-EXECUTION — Paired observed development

Status: research-only revision 1; no confirmation or promotion authority

## Purpose

This specification binds the first role-correct observed-development use of
`SPEC-A11-EXPLORATORY-STRATEGY-LAB`. It compares two integrated strategies on
the same candidate-fit cohort and the same 20 inherited development stations.
The result is diagnostic, not confirmatory, and creates no public profile.

## Registered integrated strategies

The physical adapter, evaluator, data role, and uncertainty semantics differ
from the base laboratory, so this specification registers new identities:

| Integrated strategy | Annual law implementation |
|---|---|
| `gaussian_latent_ar1_physical_core_v1` | `gaussian_latent_scalar_ar1_v1` |
| `circular_fixed_block_physical_core_v1` | `circular_fixed_block_bootstrap_v1`, five-year blocks |

An executed identity is immutable. A changed transform, estimator, evaluator,
role, or RNG law requires another strategy ID.

## Source and roles

Execution uses the published base implementation at commit `b842430`, Python
3.12.13, NumPy 2.3.5, A10M5R15R1 Daymet `candidate_fit` objects from 1980–2009,
and 20 A9C Daymet `development` objects from 2010–2025. `fit_validation` values
are calendar-preflighted as members of the authenticated shard corpus but are
not fit or scored. Only `candidate_fit` values may fit transforms, locations,
covariance, hurdle/count laws, or daily texture. Development values are opened
only after all source has been published and are used only as scoring targets.
Confirmation metadata and targets are not opened.

The executor requires its full source commit to equal published `origin/main`
and verifies its own bytes, manifest, schema, tests, base source, normalized
manifest, cohort selection, every candidate shard, development manifest, and
every selected development object before scientific work.

## Calendar, missingness, and estimand

The source transform is `daymet_official_365_v1`; the normalized axis is
proleptic Gregorian. Candidate objects have 10,958 axis rows, 10,950 observed
rows, and eight masked leap-year December 31 dates. Development objects have
5,844 axis labels, 5,840 observed rows, and four corresponding masked dates.
February 29 remains observed. Every month-year requires finite jointly observed
precipitation, Tmax, and Tmin rows.

The evaluation transform is `daymet_mask_normalized_month_v1`:

- precipitation is observed-day mean precipitation times 30.4375 days;
- mean temperature and diurnal range are observed-day means; and
- wet support is the fraction of observed days with precipitation at least
  1.0 mm.

Generated full-Gregorian months use the same statistics. This makes 30- and
31-observed-day December samples comparable without fabricating a missing raw
value. Annual normalized precipitation is the sum of the 12 equivalent-month
values. The preflight pins exact axes, masks, counts, boundaries, and leap
fixtures before fitting.

## Two-part physical adapter

Adapter `a11e_two_part_physical_core_36_v1` maps each site-year to 36 monthly
states: 12 equivalent precipitation, 12 mean-temperature, and 12 log-range
fields. For each candidate region-month:

- a dry-month hurdle is the empirical probability of zero days at or above the
  wet threshold; such months generate exactly zero total and zero wet days;
- positive support uses the smallest positive candidate wet count, scaled to
  the 30.4375-day equivalent and the shortest Gregorian instance of that month;
- positive precipitation state is the log excess above that support floor;
  threshold-dry observations have a censored 0.01 mm excess in the continuous
  fit but the hurdle controls their generated mass;
- mean temperature is the observed-day mean of `(Tmax + Tmin) / 2`; and
- range is the log observed-day mean of `Tmax - Tmin` and must be positive.

The annual strategies fit within-site standardized states. Generation location
is the median candidate-fit site mean for the region, never a development target
moment. Monthly variances and the annual-temperature variance are candidate-fit
regional medians. This deliberately coarse pooled forcing makes level errors a
joint adapter/strategy diagnostic; it is not a station-normal experiment.

The dry hurdle uses NumPy Philox. Its unsigned 64-bit seed is the little-endian
interpretation of an eight-byte BLAKE2b digest of the UTF-8 key
`a11e1-integrated-v1\0{point_id}\0{integrated_strategy_id}\0{member_id}\0month_hurdle`.
This domain is independent of all base daily streams and is part of the
immutable integrated strategy identity.

Wet counts and daily texture are candidate-fit region-month laws. Prospective
texture semantics floor temperature SD at 0.01 °C, censor zero daily ranges to
0.01 °C only for the log-range autocorrelation estimator, clip AR coefficients to
[-0.8, 0.8], and clip transition probabilities to [1e-6, 1-1e-6]. Generated
month count support is conditioned to `0 <= fitted_count <= generated_days`, so
a candidate leap-February count of 29 cannot enter a 28-day February law.
Generated positive totals are feasible for at least the minimum positive fitted
count. All base daily-core invariants remain mandatory.

## Evaluation and uncertainty

Evaluator `a11e_mask_normalized_observed_diagnostics_v1` and metric set
`a11e_mask_normalized_observed_metrics_v1` report monthly level errors, annual
precipitation and temperature variance errors, annual precipitation lag-1
error, and exact daily invariant failures. Five fixed site folds report
annual-strategy-only cross-validation conditional on the full candidate-fit
adapter; they are not an adapter generalization estimate.

Held-out development uses all 20 development stations, 16 generated years, and
one member per strategy. A 1,000-replicate NumPy Philox paired site bootstrap,
seed 410542 and domain `a11e1_site_bootstrap_domain_v1`, describes the composite
score contrast. It resamples spatial targets only and is not a Monte Carlo
uncertainty interval. There is no pass or promotion threshold. Numerically
valid arms are `RETAINED_FOR_EXPLORATION`; invalid arms are
`RETIRED_WITH_FINDING`.

## Failure and boundary

Unknown identity, source drift, role leakage, calendar drift, unsupported wet
totals, singular covariance, nonfinite output, RNG mismatch, incomplete metrics,
or an invariant failure closes the package on HOLD. Results may motivate a new
bounded strategy or adapter. They do not authorize confirmation, production,
faithful-mode changes, WEPP claims, or promotion.
