# Follow-on Design Seam — Modern Station Schema and Interannual Variation

Status: design input, not an interface or generation-profile decision
Date: 2026-07-12
Evidence mode: Static synthesis of the faithful model, ADR-0002/0003, Q3
results, and operator direction

## Direction

The intended sequence is:

1. modernize file and schema surfaces without changing climate behavior;
2. extend the quality instrument for the variation being proposed;
3. fit and compare explicit interannual model candidates; and
4. promote a successful candidate as a versioned generation profile.

Standalone single/design-storm modes are not a design constraint for the first
interannual profile. They are deprecated in WEPPcloud and the new profile
should reject them unless a later companion gives them explicit semantics.

## Keep three contracts separate

Three version axes must not be collapsed:

1. **Station-data schema** — how values, units, source period, estimator,
   hashes, and lineage are represented.
2. **Station-model variant** — which parameter families exist (for example,
   the fixed monthly CLIGEN 5.32.3 model or a model with interannual targets).
3. **Generation profile** — how the generator samples and applies those
   parameters, including RNG ownership, observed-substitution behavior, and
   output provenance.

A schema may represent data without activating a new algorithm. Faithful mode
must accept only a fixed-monthly variant whose conversion to its f32 parameter
surface is fully specified. It must reject, rather than ignore, a variant with
interannual parameters. Optional `yearly_variation` fields silently ignored by
faithful mode would violate the fail-closed and declared-divergence rules.

The first modern station schema should therefore be behaviorally inert: a
lossless, unit-explicit, provenance-bearing representation of the current
fixed monthly model. A later discriminated schema variant and generation
profile should land together once the model semantics are adjudicated.

## Existing SD fields are not interannual SDs

The legacy `.par` fields describe within-month daily distributions:

- `rst(:,2)` is the SD of wet-day precipitation depth;
- `stdtx` is the SD of daily Tmax; and
- `stdtm` is the SD of daily Tmin.

They do not describe variation across years in monthly precipitation totals or
monthly mean temperatures. New fields must use names such as
`interannual_sd_monthly_total` or `interannual_sd_monthly_mean` and record the
aggregation and estimator. Reusing the legacy `SD` name would make two
different statistical levels indistinguishable.

Observed target dispersion is also not automatically the latent variation the
generator should add. The daily generator already creates some interannual
variance. Under an independent additive temperature anomaly,

```text
target variance = baseline variance + added-anomaly variance
```

For a mean-one multiplicative precipitation factor `F` and baseline monthly
total `B`,

```text
Var(FB) = E[F^2] Var(B) + Var(F) E[B]^2
```

The station schema should therefore distinguish **observed targets** from
**fitted model parameters**. Runtime code must not infer a latent SD directly
from an observed output SD.

## Monthly values versus Fourier coefficients

Twelve monthly interannual SD values and Fourier coefficients are not two
spellings of the same complete stochastic model:

- monthly SDs specify marginal dispersion by month but no month-to-month or
  cross-variable dependence;
- fixed Fourier coefficients specify a deterministic seasonal curve and add
  no year-to-year variation;
- stochastic Fourier coefficients require a coefficient distribution and
  covariance, plus a harmonic count, phase/calendar convention, constraints,
  and fit lineage.

The faithful `fouri1/fouri2` implementation is deterministic interpolation of
the same climatology every year. Its fixed 366-day phase convention must not
be adopted implicitly as a modern interannual model.

For the first study, 12 canonical monthly target values per variable are the
more auditable representation. Fourier or other low-rank coefficients can be
recorded as a fitted model representation with reconstruction error and
lineage. If Fourier is used to smooth positive scales, it should operate on a
constrained scale such as log-SD; raw harmonic reconstruction can be negative.

## Dependence is part of the model

Marginal SDs alone permit several incompatible generators:

- one annual draw times all monthly scales gives within-variable month
  correlation `+1`;
- 12 independent monthly draws give zero cross-month correlation and jagged
  year boundaries;
- random harmonic coefficients give smooth anomalies whose covariance is
  determined by the coefficient covariance matrix.

At minimum, a candidate must declare:

- month-to-month dependence within precipitation, Tmax, and Tmin;
- Tmax/Tmin dependence, so annual anomalies do not create implausible
  temperature ranges;
- precipitation/temperature dependence;
- IID years versus serial persistence; and
- independence or coupling between annual anomalies and the existing daily
  residual processes.

Precipitation also needs a declared mechanism. Interannual variation in
monthly totals can enter through occurrence probabilities, wet-day amounts,
or both. Those choices have different consequences for wet-day counts,
intensity distributions, spells, and event descriptors. A generic
"precipitation SD" cannot select among them.

## Candidate first experiment

A useful low-complexity diagnostic candidate is a rank-one seasonal annual
latent model, not yet a recommendation for promotion:

1. Draw one correlated `(z_precip, z_tmax, z_tmin)` vector per synthetic year
   from a required positive-semidefinite 3x3 correlation matrix.
2. Use 12 fitted seasonal loadings per variable.
3. Apply additive temperature anomalies.
4. Apply a mean-one positive precipitation anomaly, for example a centered
   lognormal factor, at a declared occurrence/amount seam.
5. Give the annual model a dedicated, domain-separated RNG stream. Do not
   consume `k1`-`k10`, because doing so would entangle annual variation with
   the faithful daily trajectory.
6. Draw the same fixed-size annual vector regardless of observed substitution
   so missingness cannot shift other annual streams.
7. In observed mode apply anomalies only to generated values; observed values
   already carry their realized-year climate signal.

The model intentionally imposes rank-one cross-month covariance within each
variable. That limitation must be declared and measured. A later profile can
sample multiple EOF/Fourier coefficients with a fitted covariance.

Dew point needs an explicit ruling. Changing Tmax/Tmin means while leaving
`rh` fixed changes the generated temperature/dew-point relationship. The
first model must either declare that consequence or fit a joint dew-point
anomaly; it cannot remain accidental.

## Measurement work before implementation

The existing instrument is necessary but incomplete:

- Group A can gate preservation of the monthly climatology, wet-day amount
  moments, transition probabilities, and daily temperature SDs.
- Group B measures annual precipitation/temperature dispersion and monthly
  interannual SD of precipitation totals.
- Group B does **not** measure interannual SD of monthly mean Tmax/Tmin.
- Existing Q3 evidence found that even `qc_filter: off` under-dispersed
  observed monthly precipitation totals in 9-11 of 12 months, but the campaign
  used one burn and did not adjudicate temperature variation.

Before comparing candidates, revise the metrics to add:

- per-calendar-month mean, SD, and CV of precipitation totals;
- interannual SD of monthly wet-day count and monthly wet-day mean amount;
- per-calendar-month mean and interannual SD of monthly mean Tmax/Tmin
  (temperature CV is unsuitable near 0 °C);
- cross-month anomaly covariance or an agreed reduced summary;
- precipitation/Tmax/Tmin anomaly correlations and Tmax/Tmin correlation;
- optional year-to-year lag-one persistence; and
- effects on daily range, dew point, spells, precipitation maxima, duration,
  and peak intensity through existing Groups C/D.

The assessment should retain ADR-0002's 30- and 100-year horizons but use
multiple independent burns with uncertainty intervals. It should preregister
the aggregation hierarchy and decision bounds, compare against the
`qc_filter: off` variance-priority baseline, and include held-out stations or
periods. Observed targets must record source hashes, period, detrending,
missing-data/completeness rules, wet-day threshold, calendar, units, and
estimator. Raw and detrended comparisons should both be retained.

## Promotion boundary

Promotion requires both:

1. improved observed-climate interannual dispersion/dependence at the intended
   horizons; and
2. acceptable preservation of the monthly station contract and event/tail
   behavior.

Distance from faithful output is compatibility information. Scientific
promotion follows the quality vector under ADR-0002 and requires a new
generation-profile identifier plus complete station/input/output provenance.
