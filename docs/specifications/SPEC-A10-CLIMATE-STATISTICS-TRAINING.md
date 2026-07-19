# A10 Climate-Statistics Training

Status: research-only

Revision: 2 (A10M5R8 calendar terminology and preflight hardening,
2026-07-19)

## Surface and authority

This specification defines a development-only training-objective comparison
for the accepted A10 P1 architecture. It introduces no public generation
profile, does not change faithful CLIGEN, and does not promote a candidate.

The producer is the A10M5R8 single-L40 experiment. Consumers are its frozen
checkpoint selector and deterministic control-versus-treatment decision. Only
the accepted A10M1 `candidate_fit` role may contribute gradients or
normalization. `fit_validation` is gradient-free. Development-selection and
confirmation roles are prohibited.

## Frozen arms

`proper_nll_control` is the exactly reconstructed A10M5R3 P1 seed-147031
lognormal-wet model and accepted open-loop generator.

`climate_statistics_treatment` has the same P1 dimensions, wet-amount family,
initialization seed, corpus, normalizers, and open-loop generation closure. It
differs only in training objective and checkpoint selection. Its loss is the
mean of registered climate-statistic block losses plus a 0.05-weight daily
proper-NLL guard and a 0.005-weight latent-state stability guard. No paired-day
MSE, rescaling, target lookup, or post-generation repair is legal.

## Calendar and stochastic surface

Training and checkpoint windows contain eight exact Gregorian years on the
accepted A10M1 date axis, with the target end treated as exclusive. Under
[`daymet_official_365_v1`](SPEC-A10-CORPUS.md#daymet-calendar-contract),
February 29 is observed and leap-year December 31 is the absent source day on
the normalized Gregorian axis. Statistics and the core daily proper-score
guard use only rows where `source_observed` is true and precipitation, Tmax,
and Tmin are present; every year-month must retain at least 28 such rows. This
preserves accepted calendar-normalization missingness instead of inventing
observations or discarding calendar years. The model receives zero normalized
weather inputs and the inherited calendar and transferable site descriptors.
Four differentiable stochastic members are drawn for training and eight hard
members for checkpoint/final evaluation. Random fields are deterministic and
arm-paired.

Before training, the package must replay the A10 Daymet calendar profile and
show, for the 1980--2009 fit surface, 10,958 Gregorian-axis rows, 10,950 jointly
observed core rows, and the eight expected unobserved leap-year December 31
rows. A representative eight-year window must contain 2,922 calendar labels,
2,920 observed target rows, and no included target-end row. Calendar-axis
completeness is not observational completeness; an all-calendar-row-observed
eligibility predicate is prohibited.

For precipitation, Tmax, and Tmin, each window computes:

- the mean and across-year standard deviation of each calendar month's
  precipitation total and temperature mean;
- the mean within-month daily standard deviation for all three variables;
- the mean and across-year standard deviation of annual precipitation total
  and annual temperature mean;
- monthly wet-day frequency and wet-day amount; and
- precipitation association with Tmax, Tmin, and diurnal temperature range
  over year-month aggregates.

Losses use only aggregates, dispersions, and dependence. Member/date streams
may be retained for audit, but daily values are never paired in the climate
score.

## Checkpoint and decision

The treatment checkpoint minimizes the family-balanced climate score on the
lexicographically first four eligible fit-validation points per regime. Ties
within `1e-6` select the earlier epoch. Final scoring uses every eligible
fit-validation point and identical arm-paired member fields.

Treatment support requires finite values, nonnegative precipitation, and
Tmax not below Tmin. It advances only when its full fit-validation score is at
least 15% lower than control, no registered block is more than 10% worse, and
its open-loop daily proper-NLL guard is no more than 10% worse. Otherwise the
result is a scientific hold. Neither outcome automatically authorizes spatial,
confirmation, public-runtime, or production work.

## Extensibility boundary

Statistic blocks are field-addressed so a successor can add solar radiation
without changing the accepted core meanings. That successor must first derive
a deterministic astronomical envelope from latitude and day of year, train
the stochastic radiation residual or clearness index, and register wet/dry and
temperature dependence. Learning a latitude effect requires multi-site
evaluation; latitude is not identifiable within one site.

## Provenance and failure behavior

Every output binds source commit, contract hash, corpus and normalizer
identities, architecture, amount family, seed, arm, checkpoint, point, regime,
window years, member field, and protected-role list. Unknown fields, incomplete
calendar windows, identity drift, non-finite statistics, missing blocks,
protected-role access, or incomplete arm pairing fail closed.

Revision 2 is a terminology and preflight correction only. It does not change
the executed A10M5R8 estimand, weights, thresholds, roles, or disposition.
