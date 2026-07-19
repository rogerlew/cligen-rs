# A10 Climate-Normal Residual Architecture

Status: research-only

Revision: 1 (A10M5R9, 2026-07-19)

## Surface and authority

This specification defines a development-only architecture ablation after
A10M5R8 showed that the accepted P1 absolute-weather state space can improve
stochastic dispersion only by degrading climate location and proper fit. It
introduces no public generation profile, does not alter faithful CLIGEN, and
does not open development-selection or confirmation targets.

The producer is the A10M5R9 single-L40 experiment. Consumers are its frozen
checkpoint selectors and deterministic architecture decision. Only
`candidate_fit` observations may update parameters or define climate normals.
`fit_validation` is gradient-free and supplies no model input derived from its
weather targets.

## Frozen arms

`accepted_p1_context` exactly reconstructs P1/lognormal/seed-147031 and is a
noninferiority reference, not a fitted arm in the new family.

`climate_normal_baseline` has an explicit candidate-fit-only table for each of
the six registered regimes and twelve calendar months. The table owns all 15
distribution-head parameters. A small feed-forward correction receives only
latitude, longitude, and elevation and is shared across regimes and months.
It has no recurrent or stochastic latent state. Fit-validation regime and site
descriptors are permitted transferable inputs; fit-validation weather values
are not.

`climate_normal_plus_residual` freezes the selected baseline and adds a
six-dimensional stochastic state updated once per calendar month. The state is
an AR(1) process with learned persistence constrained to `[0, 0.995]` and
counter-based, arm-paired Gaussian innovations. A small decoder may perturb
only wet-occurrence logit, positive-precipitation log location, temperature
mean location, and log-diurnal-range location. It cannot change distribution
scale heads, site descriptors, baseline weights, or calendar features.

Innovations are centered across the even-sized member ensemble at every
year-month cell. Thus the baseline owns member-mean distribution parameters
and the residual state represents stochastic departures rather than a second
climate-location model. There is no observed or generated daily-weather
feedback, target lookup, post-generation repair, or monthly rescaling.

## Calendar and objective

Every arm follows `daymet_official_365_v1` and the A10 corpus revision-2
preflight. An exact eight-year target contains 2,922 Gregorian labels and 2,920
observed Daymet rows in the representative 1980--1987 window; the target end is
exclusive. Climate scores and proper likelihood use only jointly observed
precipitation/Tmax/Tmin rows, with at least 28 observations in every year-month.

The baseline is trained first with core daily proper NLL plus low-weight
monthly/annual location and wet occurrence/amount losses. Its checkpoint uses
the same fit-validation subset frozen for A10M5R8. The residual then starts
from and freezes that exact baseline checkpoint. Its loss is the complete
A10M5R8 climate-statistic score, a daily proper-NLL guard, and a residual-size
penalty. Paired daily MSE remains zero.

Four differentiable members are used for residual training and eight hard
members for checkpoint and final evaluation. Final scoring covers all 240
fit-validation points with identical output random fields for all arms and an
independent registered residual-innovation field.

## Decision

The residual architecture advances only when all conditions hold:

- the mean of monthly and annual interannual-dispersion errors is at least 15%
  lower than the baseline-only arm;
- the family-balanced climate score is at least 5% lower than baseline;
- no registered climate block is more than 10% worse than baseline;
- daily proper NLL is no more than 10% worse than baseline;
- family-balanced climate score is no worse than accepted P1;
- daily proper NLL is no more than 10% worse than accepted P1; and
- every arm is finite, physically supported, role-clean, and complete.

Failure is an informative architecture hold. No outcome-time change to state
dimension, persistence, decoder surface, weights, epochs, seed, members, or
thresholds is allowed. A passing result identifies a core candidate family but
does not authorize confirmation, public runtime integration, or solar input.

## Extensibility boundary

Solar radiation remains the first proposed extension only after this core
architecture passes. It must use a deterministic astronomical envelope from
latitude and day of year and a stochastic residual or clearness index; it may
not be added merely to rescue a failed precipitation/temperature architecture.

## Provenance and failure behavior

Outputs bind source commit, contract and calendar-profile hashes, corpus and
normalizer identities, all three arm identities, baseline checkpoint, residual
checkpoint, seed, member fields, sites, regimes, windows, and protected roles.
Unknown identities, incomplete preflight, target-derived validation inputs,
unfrozen baseline mutation, innovation drift, non-finite values, physical
support failure, incomplete pairing, or protected-role access fail closed.
