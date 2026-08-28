# A11E6S faithful temperature static review

Date: 2026-08-27

Disposition: `DESIGN_CONSISTENT_UNDERDISPERSION_EXPECTED`

## Executive finding

No inspected evidence indicates that cligen-rs accidentally suppresses
faithful temperature variance. The Rust path is a source-shaped transcription
with extensive bit-identity evidence. The observed deficit is consistent with
the source design: fixed monthly daily distributions have no year-scale state,
and `RANSET` further conditions the realized daily-normal sequence to look
typical cumulatively.

This is a high-confidence implementation finding and a high-confidence
qualitative mechanism finding. The fraction of the deficit caused by QC versus
fixed-parameter structure is not statically identifiable.

## Source trace

### 1. Parameter meaning

The station path loads twelve monthly mean daily Tmax/Tmin values and twelve
monthly daily Tmax/Tmin standard deviations. `sta_parms` converts the source
temperature quantities but does not introduce an annual or interannual
parameter. In A11E6, `interpolation: none` selects each month's values directly.

These parameters describe the distribution of *daily* temperature within a
calendar month. They are not observed interannual standard deviations of
monthly or annual temperature.

### 2. Daily temperature equations

`cligen.f:1346-1446` and `daily.rs::temps_generated` draw independent Tmax and
Tmin standard-normal columns and then couple them using the smaller-SD scheme.
When `SDmax >= SDmin`, the effective equations are:

```
Tmin = mean_min + SDmin * Zmin
Tmax = Tmin + (mean_max - mean_min)
             + sqrt(SDmax^2 - SDmin^2) * Zmax
```

The opposite branch is symmetric. With independent unit normals, this
construction preserves the requested daily Tmax and Tmin means and marginal
variances while inducing their intended same-day covariance. It supplies no
year-level anomaly, no slowly varying temperature state, and no explicit
cross-month covariance.

The normal transform is source `DSTN1`, using a rolling pair of source `RANDN`
uniforms. Rolling state provides local dependence through a shared uniform,
but nothing in this path represents a persistent annual climate condition.

### 3. Monthly-batch conditioning

At every month boundary, source `RANSET` fills separate random columns for
Tmax and Tmin. For each parameter and calendar month it maintains from-run-start
cumulative:

- count of generated days;
- sum of standard-normal deviates;
- sum of squared deviates;
- twenty-bin distribution counts.

It runs K–S, normal-mean, and normal-variance tests and rejects a candidate
monthly batch when any verdict exceeds the threshold. Both source thresholds
are 50.0. Rejected attempts restore the cumulative statistics and rolling
normal input but deliberately keep consumed RNG state advanced. One `iredo`
counter is shared across the nine columns for the refill; after 10,000 failures
the source ships the failed batch.

Because the mean test operates on the cumulative sequence for the same
calendar month, sustained same-signed monthly temperature anomalies push the
cumulative mean toward rejection. This is negative feedback against low-
frequency drift. Cumulative testing relaxes the effect as the run grows, but
does not make the accepted sequence an unconditional sample.

### 4. Annual variance implication

Without a year-level factor, a generated monthly or annual mean is primarily an
average of daily-scale residuals. Averaging reduces its variance roughly with
effective sample size. Real observations contain persistent weather, coupled
seasonal anomalies, and year-varying climate conditions, so their daily
residuals do not average away as rapidly.

The QC mean feedback can reduce the low-frequency component further. Its
variance and K–S gates control daily marginal fidelity and convergence; they
cannot create missing annual covariance or parameter drift.

This predicts the A11E6 direction: good fixed monthly climatology, markedly
low annual temperature variance, and improvement from a treatment that adds
an explicit multimonth/interannual state.

## Rust correspondence and implementation assessment

- `daily.rs::temps_generated` follows both Fortran smaller-SD branches,
  including REAL*4 arithmetic and the Tmin range check.
- `rng.rs::ranset` follows the cumulative counters, parameter exclusions,
  test ordering, state restoration, consumed-draw behavior, shared retry
  counter, and 10,000-attempt escape.
- `crandom3.rs` preserves the source REAL*8 islands for cumulative sums and
  REAL*4 thresholds and other state.
- `deviates.rs::dstn1` preserves the f32 transform, source constant, range
  checks, and pinned transcendentals.
- Completed port evidence records 26,402,148 `DSTN1` values, 2,584 `RANSET`
  calls, and 189,207 daily `clgen` calls as bit-identical, plus twelve complete
  golden `.cli` outputs byte-identical to the reference build.

This evidence rules strongly against a Rust-only translation error in the
reviewed path. It does not assert that the legacy design is scientifically
adequate.

## A11E6 comparison-path audit

A11E6 reads the intended `.cli` precipitation, Tmax, and Tmin columns, forms
daily mean temperature as `(Tmax + Tmin) / 2`, averages by generated calendar
month, and applies the inherited canonical annual month weights. Generated
coverage is exact for years 1–16. Observations use the canonical Daymet 365-day
transform and mask-normalized monthly statistic.

Potential comparator limitations are real but do not resemble a Rust faithful
bug:

- point-station `.par` parameters are compared with gridded Daymet targets;
- only sixteen observed years are available;
- `.cli` temperatures are text-quantized;
- the annual statistic uses a normalized common month-weight vector.

None introduces a hidden annual stochastic state. All 160 faithful pairs being
underdispersed, with median generated/observed variance 0.0821, is qualitatively
consistent with the traced model structure.

## Prior dynamic evidence and remaining question

ADR-0002 and Q3 already isolated QC for precipitation: conditioning reduced
interannual dispersion about 19% at 30 years and 11% at 100 years, while both
conditioned and unconditioned generation remained structurally underdispersed
at monthly grain. That supports the same two-layer explanation, but it is not a
temperature-specific estimate and must not be substituted for one.

The existing `qc_filter: off` path is exactly the required temperature
ablation: source RNG and downstream temperature equations remain unchanged;
only batch acceptance/retry is removed and the faithful verdicts are recorded
diagnostically.

## Recommended successor

Run an A11E6Q temperature QC attribution before implementing A11E7:

1. exact A11E6 20-station observed corpus and `.par` identities;
2. `faithful_5_32_3` with `qc_filter: faithful` versus `qc_filter: off`;
3. enough independent 16-year members to estimate station-level distributions
   rather than one noisy trajectory (32 is a reasonable bounded target);
4. primary signed monthly and annual temperature variance ratios, annual lag
   one, low-frequency power, and cross-month covariance;
5. report the on/off shift as QC contribution and the off/observed residual as
   fixed-parameter structural deficit;
6. preserve observed as target, faithful-conditioned as operational baseline,
   and confirmation=false.

If QC removal repairs most of the deficit without unacceptable climatology
cost, A11E7 should build from `qc_filter: off`. If a large deficit remains, the
temperature-only annual-state overlay remains justified and should be compared
against both faithful configurations.
