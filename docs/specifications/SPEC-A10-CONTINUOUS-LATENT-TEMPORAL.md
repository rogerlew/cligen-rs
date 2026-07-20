# A10 continuous latent temporal processes

Status: research-only, revision 1 (A10M5R12)

## Surface

This specification governs a development-only comparison of two stochastic
latent-process extensions to the frozen P2 daily weather backbone:

- `continuous_medium_latent_process-k2`; and
- `continuous_hierarchical_latent_process-k2`.

It defines no public generation profile or promoted model.

## Authority basis

The candidate roster responds to
`HOLD-A10M5R11-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`. The observation roles,
calendar, training seeds, precipitation/Tmax/Tmin objective families,
100-year stream matrix, temporal metrics, component scales, comparators,
bootstrap, and eligibility gates are inherited from the ratified A10M5R11
protocol. The P2 daily backbone is reconstructed from the accepted A10M5R3
checkpoint identities and remains frozen.

## Continuous state semantics

Latent state follows a stationary Ornstein--Uhlenbeck process in continuous
time. For time scale `tau` days, its exact one-day transition is
`z[t+1] = exp(-1/tau) z[t] + sqrt(1-exp(-2/tau)) epsilon[t+1]`, with stationary
Gaussian initialization. Daily evaluation is the numerical output cadence,
not a calendar reset.

No state resets, innovations, or parameter changes occur at month or year
boundaries. Month and year labels are used only to aggregate training and
evaluation statistics. Seasonal loadings vary continuously with sine/cosine
day-of-year covariates and static latitude, longitude, and elevation. The new
loading surface excludes the inherited binary leap-year indicator.

The frozen matched P2 backbone still consumes its original 13-feature input,
including that leap-year indicator. This package therefore claims continuous
OU state and smooth new loadings, not that the complete frozen-backbone output
is free of every calendar-boundary discontinuity. Changing that accepted
backbone would confound the matched temporal-process comparison.

Calendar aggregation still defines the estimand observed by this development
comparison; continuous state semantics do not establish scale invariance. A
qualifying candidate must pass a later random-origin rolling-window sensitivity
analysis before architecture promotion. That sensitivity is non-gating here so
the inherited A10M5R11 comparison remains exact.

The medium-only candidate has eight joint latent factors with time scales
bounded to 14--180 days. The hierarchical candidate contains that identical
medium process plus four slow factors bounded to 180--1,460 days. Both modify
wet occurrence, positive precipitation amount, temperature mean, and log
diurnal range jointly. Neither consumes observed weather during generation.

## Training and comparison

Both candidates use K2 shape and the same frozen P2 backbone so the only
structural contrast is the slow process. Three seeds and counter-based common
random fields are used. The error signal gives equal family weight to monthly
and annual location and dispersion, within-month daily dispersion, wet
occurrence/amount, and precipitation-temperature dependence. Daily proper NLL
is still reported but has zero training and checkpoint weight, and paired
daily-pattern weight is zero. The inherited implementation computes expected
conditional-member NLL rather than marginal mixture NLL; weighting it would
penalize every unpaired latent trajectory against the observed day and suppress
the target stochastic spread.

Final scientific eligibility is determined only by the inherited realized
temporal protocol: the bootstrap upper-90 median regime ratio must be at most
1.25 and the maximum point ratio at most 1.50 against the lower faithful or
stochastic localized-PRISM comparator error. Every eligible candidate
continues; no extra parsimony selector is introduced.

The inherited eligibility bootstrap resamples observation years independently,
so its annual lag components do not preserve the observed multi-year ordering.
The slow-process ablation is therefore interpreted only with additional
non-gating annual location, dispersion, lag, and cross-field diagnostics. Those
diagnostics preserve the actual 1980--2009 observation series, pair bootstrap
member indices across candidates, and report learned factor time scales. They
may support a slow-process disposition but cannot change temporal eligibility.

## Calendar and failure behavior

Daymet observations remain unfilled. Bootstrap blocks use the exact leap-safe
relabel `2000 + 16 * position + (0 if the source block contains February 29
else 1)`. Missing identities, non-finite state or gradients, state-boundary
resets, incomplete streams, physical-support failures, role opening, or
comparator/replay failure close without inference.

Every generated float32 precipitation/Tmax/Tmin daily stream and each fitted
adapter checkpoint is retained. Selector intake authenticates candidate
admission and terminal evidence, exact seed/site/member keys, the complete
registered metric surface, archive and row hashes, physical support, and a
tight cross-platform recomputation of derived metrics. Comparator streams must
have the exact contiguous 2001-01-01 through 2100-12-31 date axis. The local
selector is accepted
only through two isolated byte-identical replays bound to the published source
commit, collection/cleanup/terminal receipts, exact inherited comparator
binary and per-site comparator provenance, data, contracts, and
sites.

## Solar boundary

Solar remains sealed. A later candidate may add a procedural latitude/day-of-
year astronomical envelope and a learned stochastic clearness/cloud residual
coupled to generated precipitation and temperature only after the core
temporal process qualifies.
