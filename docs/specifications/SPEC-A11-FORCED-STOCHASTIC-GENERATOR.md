# SPEC-A11-FORCED-STOCHASTIC-GENERATOR — Forced Climate and Conditional Daily Oracle

Status: research-only attempted revision 1, rejected at execution review (A11; no public runtime identifier)

## Surface

This specification defines the prospective A11 forcing bundle, deterministic
moment reconciliation, annual/monthly target stream, conditional daily oracle,
research evidence, and attempt lineage. It does not register a public
generation profile, amend faithful CLIGEN, or authorize production use.

The sole research candidate identity is
`a11_forced_monthly_annual_oracle_v1`. The attempted revision 1 freeze recorded the architecture,
guardrails, and numeric choices through the owning package's hash-bound
[`design-freeze-v1.json`](../work-packages/20260825-a11-forced-monthly-annual-stochastic-generator/artifacts/design-freeze-v1.json).
The strict research evidence surface is
[`a11-evidence-v1.schema.json`](../work-packages/20260825-a11-forced-monthly-annual-stochastic-generator/artifacts/a11-evidence-v1.schema.json).
Independent execution review found the freeze and evidence incomplete; the
package's `evidence-audit-v1.json` is the terminal authority. Neither record
registers a public generation profile.

## Producers and consumers

- The forcing builder produces a canonical forcing bundle and reconciliation
  receipt from immutable source manifests.
- The annual/monthly target generator consumes the effective forcing bundle
  and produces one target vector for every generated year.
- The daily oracle consumes each target vector, pooled texture parameters, and
  explicit random state and produces complete daily weather and event records.
- The A11 evaluator consumes generated records from the candidate and three
  fixed comparators plus role-correct observations and pinned WEPP inputs.
- Artifact verifiers, provenance readers, and a future promotion package
  consume the canonical records. Revision 0 has no public CLI consumer.

## Authority basis

A11 is a declared extension under ADR-0001 and ADR-0002. ADR-0007 admits the
immutable PRISM Norm91m climatology input. `SPEC-A10-CORPUS` governs inherited
Daymet role/calendar behavior; `SPEC-A10-STOCHASTIC-PRISM-COMPARATOR` governs
the PRISM asset and comparator; `SPEC-OBSERVED-TARGET-CORPUS`,
`SPEC-QUALITY-REPORT`, and `SPEC-A5-EVALUATION` govern reused measurement
surfaces only where the A11 design freeze names their exact revisions.

No statement here changes the source-authority meaning of
`faithful_5_32_3` or the public `qc_filter` values.

## Separation of surfaces

The schema must keep these records distinct and cross-hash them:

| Record | Responsibility | Forbidden responsibility |
|---|---|---|
| Forcing bundle | Site climate means, variability, persistence, and dependence | Random realization or fine-scale texture inference |
| Structure bundle | Frozen stochastic laws and pooled regional texture | Site climatology replacement or output-selected behavior |
| Random-state record | Reproducible realization and domain-separated streams | Parameter fitting or forcing changes |
| Generated stream | Realized daily/monthly/annual weather | Feeding back into forcing, selection, or repair |

Unknown fields, versions, units, calendars, roles, or cross-hashes fail closed.

## Forcing bundle

Each bundle has a stable site/location identity, coordinate and coverage
identity, source-period and role manifest, calendar profile, units, requested
forcing, effective forcing, and reconciliation receipt. At minimum it carries
twelve values or a fully specified twelve-dimensional surface for:

- precipitation total mean and interannual variance/covariance;
- Tmax and Tmin mean, from which mean temperature and positive diurnal-range
  targets are derived by one frozen transform;
- interannual variance/covariance of monthly mean temperature;
- within-month daily mean-temperature residual SD;
- monthly mean diurnal-range target mean and interannual variance, plus
  within-month daily diurnal-range mean and dispersion;
- wet-day-count mean and variance with integer support bounded by month length;
- annual precipitation-total variance and annual mean-temperature variance;
- lag-one annual persistence for precipitation and temperature;
- cross-month precipitation and temperature dependence; and
- precipitation/temperature and wet-count/amount dependence required by the
  target generator.

Every field declares physical units, estimator, sample support, source role,
period, missingness mask, and uncertainty/adjustment status. A monthly mean,
variance, or dependence value is never inferred from a missing field. PRISM
supplies monthly precipitation/Tmax/Tmin climatological location directly; no
learned geographic-to-normal mapping is admitted.

The interannual variance of monthly means and the within-month dispersion of
daily residuals are different surfaces and never share a field or estimator.
Likewise, a monthly mean diurnal-range target and within-month daily
diurnal-range dispersion are separate. Every one declares its estimator,
period, mask, units, leap handling, and reconciliation or conditioning role.

Revision 1 must define exact transformations from Tmax/Tmin forcing to mean
temperature and diurnal range, count-dispersion feasibility, dry-month
behavior, dependence representation, numeric tolerances, and canonical JSON.

## Deterministic reconciliation

For precipitation, let `C_p` be the monthly-total covariance matrix and `u`
the twelve-vector of ones. The effective surface must satisfy:

```text
C_p is symmetric positive semidefinite
diag(C_p) = forced monthly variances
u^T C_p u = effective annual precipitation variance
```

For annual mean temperature, let `w` be normalized calendar-day weights and
`C_t` the monthly mean-temperature covariance matrix. The corresponding
constraint is `w^T C_t w = effective annual mean-temperature variance`.

Separate PSD checks for `C_p` and `C_t` do not establish a feasible joint
surface. Revision 1 must freeze either one reconciled joint block-dependence
matrix or one fully specified conditional/copula construction spanning monthly
precipitation totals, wet-day counts, monthly mean temperature, and diurnal
range. The contract identifies observed-scale versus latent-scale dependence,
publishes requested and effective cross-block values, applies a prospective
adjustment priority, and validates dependence on the realized scale. A joint
construction that cannot establish feasibility fails closed.

The deterministic nearest-covariance solver minimizes one prospectively frozen
weighted norm relative to a source covariance `C0`. Revision 1 must freeze the
solver/version, convergence test, maximum iterations if iterative, arithmetic
width, eigenvalue tolerance, tie breaks, and canonical receipt.

The priority rule is immutable:

1. monthly means are exact;
2. monthly variances are exact;
3. cross-month covariance changes minimally to meet a feasible annual target;
4. an infeasible annual target projects to the nearest feasible boundary and
   records requested value, feasible interval, effective value, adjustment,
   and reason.

Silently changing a monthly mean/variance, using generated output in the
solver, or treating nonconvergence as a usable bundle is prohibited.

## Annual/monthly target generator

For each year the generator produces exactly these twelve-element target
families:

- precipitation total;
- integer wet-day count;
- mean air temperature; and
- positive diurnal range.

The architecture is one transformed multivariate process with compact,
interpretable annual/seasonal dependence constructed from the forcing. It is
not fitted end to end. Revision 1 must freeze one marginal family and transform
per target family, one dependence construction, the number/meaning/order/sign
convention of latent contrasts, the annual state-transition rule, initial
state, and all degeneracy handling. A grid or output-selected family is not
permitted.

The generated target distribution must reproduce the effective reconciled
means, variances, persistence, and dependence within prospectively frozen
Monte Carlo tolerances. Individual finite runs are realizations, not paths to
be optimized toward empirical moments.

## Conditional daily oracle

### Precipitation occurrence

Given month length `D`, exact wet-day count `K`, previous terminal wet/dry
state, and frozen seasonal transition parameters, sample a first-order Markov
path conditional on `sum(wet) = K`. A numerically stable forward/backward
dynamic program computes and samples the bridge. Revision 1 freezes a
forcing-dependent feasible-count set for each reachable starting state and
requires the transition law to give every count the target generator can emit
strictly positive conditional probability. The implementation preserves the
supplied prior state across month boundaries and fails on a count outside that
set or zero conditional probability. Rejection and retry are prohibited.

Monthly amount/count support is joint: `K = 0` if and only if `P_m = 0`; a
positive `P_m` requires `1 <= K <= D`. The target generator cannot emit any
other pair.

### Wet-day amounts

For `K = 0` and `P_m = 0`, emit no wet amounts and do not evaluate a
normalizer. For `K > 0`, draw exactly `K` positive relative event weights from
one revision-1 frozen body/tail law with one frozen within-spell persistence
mechanism, then set `p_i = P_m * w_i / sum(w)`. The output has exactly `K`
positive amounts and an exact monthly sum under the frozen summation/tolerance
rule. A zero or non-finite denominator fails closed. Exponential tilting and
alternative amount families are not revision-1 runtime choices. This one
registered normalization is part of the conditional probability law, not an
output-time repair or target-seeking retry.

### Temperature

Sample standardized daily mean-temperature residuals from one frozen seasonal
AR law and condition them to exact zero mean and the forced within-month daily
mean-temperature residual SD. That conditioning is distinct from the
interannual covariance of monthly mean-temperature targets. Sample positive
daily diurnal range in log space from its separately named forced mean and
dispersion. Derive Tmax/Tmin from mean temperature plus/minus half the range.
The registered centering/scaling is part of conditional sampling; ordering is
structural, and clipping, swapping, or later repair is prohibited. Revision 1
must define short-month or zero-variance handling and cross-month state
continuity.

### Storm descriptors and context variables

Storm duration, time to peak, and peak ratio condition on event depth,
month/season, spell position, and only the annual wetness state if revision 1
freezes that dependency. Solar radiation, humidity, wind, and dew point consume
the generated occurrence and temperature context through frozen bounded
distributions. They are not required to reproduce legacy trajectories after
precipitation changes, but every support and compound-behavior gate remains
mandatory.

## Forced and fitted boundary

Location forcing owns monthly means; interannual monthly and annual
dispersion; within-month daily temperature/range dispersion; interyear
persistence; cross-month/cross-variable dependence; and wet-day-count mean and
dispersion. Candidate-fit-only regional pooling owns spell and amount texture,
daily temperature autocorrelation, storm descriptors, and secondary-variable
conditional laws. Evaluation and confirmation targets cannot update either
surface.

Region membership, pooling estimators, regularization, source periods, and
minimum support are frozen before candidate output. Unsupported required
texture is an explicit fit-ineligible result, not a fallback to a mutable
database or a different model.

## Calendar, roles, and confirmation

All Daymet consumers follow `daymet_official_365_v1`, the complete Gregorian
normalized axis, missing leap-year December 31 masks, and exclusive window-end
semantics in `SPEC-A10-CORPUS`. Month/year eligibility is based on required
field masks. Revision 1 must bind exact counts and boundary fixtures.

Only `candidate_fit` observations may fit an estimator, construct a forcing
product, or fit pooled texture. An independently frozen transferable forcing
product may be queried at development or confirmation coordinates without
target-series access when revision 1 pins its asset, fixed period, coverage,
estimator, and overlap limitation before candidate output. If such a product
does not supply a required location-specific variation field, the field is
explicitly region-pooled; development or confirmation observations cannot be
read to manufacture site-specific forcing. Development observations may score
the frozen candidate. Locked confirmation target bytes remain unread until a
complete development pass, candidate/evaluator/forcing seal, and atomic access
transition. Confirmation is consumed once and cannot cause tuning.

## Comparators and evidence

The complete development and confirmation comparison contains exactly four
arms:

1. `faithful_5_32_3` with faithful QC;
2. `faithful_5_32_3` with `qc_filter: off`;
3. `stochastic_prism_localized_par_v1`; and
4. `a11_forced_monthly_annual_oracle_v1`.

Every arm uses the frozen station/site roster, horizons, burn/seed mapping,
calendar, and measurement code. Each 30-year record is the prefix of its
matched 100-year stream. The design freeze must enumerate monthly climate,
annual/interannual, daily precipitation, thermodynamic/event/compound, support,
runtime, and WEPP response cells plus candidate-blind thresholds and
aggregation. Monthly and daily components never receive separate promotion.

## Attempt and science status

One immutable `science_contract_id` binds every A11 attempt. Operational
attempts increment `attempt_id` and preserve previous records. Their
`science_status` is exactly `NOT_EVALUATED`, `PASS`, or `FAIL`; execution state
has a separate vocabulary frozen by revision 1. Operational corrections may
not change forcing semantics, architecture, fit, roster, evaluator, thresholds,
or confirmation state. Resource use accumulates across attempts and never
resets.

## Failure behavior

Readers and generators fail closed on malformed or missing forcing, unknown
units/calendar/role/schema, invalid count support, source/hash mismatch,
non-finite numeric input/output, infeasible unreported moment targets,
reconciliation failure, zero-probability conditional paths, zero amount
normalizers, support violations, random-domain collisions, unsealed
confirmation access, or incomplete mandatory evidence.

An operational failure is `science_status=NOT_EVALUATED`; it is not evidence
for or against the generator. A completed integrated development or
confirmation failure is final for revision 1.

## Provenance obligations

Every forcing, structure, random-state, generated-stream, climate-evidence,
and WEPP record binds:

- schema and model identity;
- `science_contract_id` and `attempt_id` where applicable;
- source commit and exact implementation/evaluator hashes;
- source/corpus/role/calendar/period and PRISM bundle identities;
- requested/effective forcing and reconciliation receipt;
- pooled texture fit and region-map identities;
- seed, domain separation, and horizon/prefix identity;
- comparator, climate output, quality, WEPP executable/input/parser, and
  artifact-manifest hashes as applicable; and
- confirmation state, resource use, and cleanup state.

Absolute host paths, credentials, mutable URLs as identities, raw restricted
targets, and unverified cache presence never enter canonical evidence.

## Revision-1 ratification record

Before candidate output, the owning package ratified
`a11-forced-monthly-annual-oracle-science-v1`. Its design freeze pins the source
map and period, six climate regions, 48-variable empirical Gaussian-copula
marginals, binary64 eigensolver and tolerance, Philox domains, six-site
development roster, eight nested 100-year members, existing temporal metric
scales and thresholds, mandatory A5 WEPP protocol, sealed confirmation state,
and aggregate resource ceiling. The package-local verifier/preflight fails
closed on source identity, role/calendar/mask, covariance, support, or
confirmation drift. Generated streams are represented by exact hashes and
complete registered metric vectors; raw daily payloads are intentionally not
committed.
