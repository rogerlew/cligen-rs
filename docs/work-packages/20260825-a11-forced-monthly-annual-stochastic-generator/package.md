# A11 — Forced Monthly/Annual Stochastic Generator with Conditional Daily Oracle

Status: `EXECUTED-HOLD-A11-CONTRACT-NONCONFORMANCE`
Date: 2026-08-25
Evidence mode: Ran + Static
Starting branch and push target: current `origin/main`, push `main`

## Objective

Implement and adjudicate exactly one non-neural stochastic generator in which
monthly climatology and monthly/annual variability are externally supplied
forcing, their moment surfaces are reconciled deterministically, and daily
precipitation, temperature, storm, and context series are sampled
conditionally on the resulting monthly targets. Execute one integrated climate
and WEPP development campaign followed, only on a complete development pass,
by one locked confirmation and one terminal scientific decision.

This is a fresh A11 lineage. It does not rescue, relabel, or continue an A10
neural candidate. A10M5R15R2R5 remains at its recorded
`HOLD-A10M5R15R2R5-E1-NONFINITE-TRAINING` terminal; no E1 numerical corrective
successor or unchanged R15 rerun is authorized.

## Thesis and frozen architecture boundary

The climate definition, generator structure, and random realization are three
separate surfaces:

1. **Forcing** states which climate exists at a location.
2. **Generator structure** states how that climate is distributed through
   years, months, days, spells, and events.
3. **Random state** selects one reproducible realization without changing the
   forcing or structure.

A11 contains one candidate identity,
`a11_forced_monthly_annual_oracle_v1`. Phase 1 must freeze its remaining
numeric choices before any candidate output. Later phases may correct an
implementation defect beneath the same package and immutable science contract,
but may not substitute an architecture, marginal family, selector, fallback,
or objective after results are visible.

## Terminal result

The candidate-free calendar and role preflight passed, but independent review
rejected the execution before scientific adjudication. The package-local
implementation was not contained in its named source commit; it omitted the
frozen annual transition, did not reconcile annual covariance after
site-specific PRISM scaling, omitted mandatory storm/context and evaluation
surfaces, changed wet-count targets through an unregistered rule, and
substituted a raw median for the frozen bootstrap estimator.

Attempt 0002's 48 stream records and ratios are retained only as invalid,
non-authoritative diagnostics. They cannot establish climate pass or failure.
Both authorized operational attempts are spent, and correcting the architecture
would change the frozen science contract after output inspection. The package
therefore closes at `HOLD-A11-CONTRACT-NONCONFORMANCE` with
`science_status=NOT_EVALUATED`. No confirmation target access was observed,
but the attempted seal lacked an authenticated roster/custodian/firewall
artifact. No production promotion is authorized.

## Scope

Included:

- a versioned forcing bundle containing, at minimum, monthly precipitation,
  Tmax, and Tmin means; interannual variance/covariance of monthly
  precipitation totals and monthly mean temperature; within-month daily
  mean-temperature residual SD; monthly mean diurnal-range targets and their
  interannual variance; within-month daily diurnal-range dispersion; annual
  precipitation and mean-temperature dispersion; interyear persistence;
  cross-month and cross-variable dependence; and monthly wet-day-count mean
  and dispersion;
- direct use of the immutable PRISM Norm91m monthly precipitation/Tmax/Tmin
  surface for climatological location, with no learned normals mapper;
- a prospectively frozen source map that distinguishes immutable transferable
  variation-product lookup at any eligible coordinate from candidate-fit-only
  estimator and pooled-texture fitting;
- deterministic positive-semidefinite reconciliation of monthly covariance
  with forced annual variance, including day-count weighting for temperature,
  followed by one frozen joint-feasibility construction for precipitation,
  wet counts, temperature, and diurnal range with requested/effective
  cross-block dependence and a published adjustment receipt;
- one transformed multivariate annual/monthly target generator producing
  twelve monthly precipitation totals, wet-day counts, mean temperatures, and
  positive diurnal ranges per year, with compact and interpretable annual,
  seasonal, and cross-variable dependence derived from the forcing;
- one conditional daily oracle: exact-count Markov-bridge precipitation
  occurrence, total-preserving positive wet-day amounts, conditioned daily
  mean-temperature residuals, positive diurnal range, and conditional storm
  and secondary-variable distributions;
- pooled regional fitting only for spell shape, wet-amount texture and
  persistence, daily temperature autocorrelation, storm descriptors, and
  secondary-variable conditional distributions;
- the four frozen comparator arms: faithful CLIGEN, faithful CLIGEN with QC
  off, `stochastic_prism_localized_par_v1`, and the single A11 candidate;
- nested 30/100-year development runs and integrated monthly, annual,
  interannual, daily, event, compound-behavior, physical-support, runtime, and
  WEPP-response adjudication;
- candidate-byte and forcing-rule sealing after development pass, followed by
  one atomic consume of locked confirmation targets and one confirmation run;
- package-local operational attempts identified by an immutable
  `science_contract_id` and incrementing `attempt_id`, with execution status
  separated from `science_status`;
- a research-only implementation, evidence record, independent review,
  roadmap/catalog reconciliation, and a promotion recommendation only if the
  locked confirmation passes.

Excluded:

- neural networks, backpropagation, GPU execution, architecture tournaments,
  candidate grids, or distribution-family grids;
- a runtime climate classifier, output-selected fallback, candidate
  substitution, or a learned mapping from geographic descriptors to monthly
  normals;
- full-year path optimization, rejection toward monthly or annual statistics,
  repeated month generation, or a fixed attempt cap used as calibration;
- output-time clipping, target-seeking rescaling, ordering repair, or physical
  repair outside the registered conditional sampling law. The oracle's single
  wet-weight normalization and registered temperature centering/scaling are
  structural conditional transforms, not post-generation repair;
- separately promoting the monthly target generator or daily oracle;
- reading confirmation target series before the complete development seal;
- production profile registration, public runspec/schema changes, default
  changes, or consumer integration before confirmation and a separate explicit
  promotion authority;
- creating a new work package solely for parser, evidence, scheduler, or other
  operational failures while the A11 science contract is unchanged.

## Authority

- [ADR-0001](../../decisions/0001-source-code-authority-port.md) protects the
  faithful comparator and requires declared extension behavior.
- [ADR-0002](../../decisions/0002-quality-metrics-authority.md) requires
  measurement before promotion.
- [ADR-0007](../../decisions/0007-a10-external-normal-conditioning.md) admits
  immutable measured normals as transferable site inputs and establishes the
  PRISM identity and provenance boundary.
- [SPEC-A11-FORCED-STOCHASTIC-GENERATOR](../../specifications/SPEC-A11-FORCED-STOCHASTIC-GENERATOR.md)
  is the research interface and architecture contract owned by this package.
- [SPEC-A10-CORPUS](../../specifications/SPEC-A10-CORPUS.md) governs inherited
  Daymet calendar, missingness, and role handling until A11 freezes an
  independently versioned corpus manifest.
- [SPEC-A10-STOCHASTIC-PRISM-COMPARATOR](../../specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md)
  governs the immutable PRISM bundle and comparator arm.
- [SPEC-OBSERVED-TARGET-CORPUS](../../specifications/SPEC-OBSERVED-TARGET-CORPUS.md),
  [SPEC-QUALITY-REPORT](../../specifications/SPEC-QUALITY-REPORT.md), and
  [SPEC-A5-EVALUATION](../../specifications/SPEC-A5-EVALUATION.md) are inherited
  measurement authorities where the Phase-1 freeze explicitly reuses them.

The operator's 2026-08-25 instruction authorizes this scaffold and the fresh
A11 lineage on `main`. The scaffold does not itself authorize candidate
output, confirmation access, production integration, external acquisition, or
an unbounded execution. Those become reachable only through the prospective
freezes and gates below.

## Forced versus fitted quantities

Forced per location:

- monthly precipitation, mean-temperature, and mean diurnal-range
  climatological means;
- interannual variance/covariance of monthly precipitation totals and monthly
  mean temperature, plus annual precipitation-total and annual
  mean-temperature dispersion;
- within-month daily mean-temperature residual SD and daily diurnal-range
  mean/dispersion, each distinct from interannual monthly-target variance;
- interyear persistence;
- cross-month and cross-variable covariance or its fully specified target
  representation; and
- wet-day-count mean and dispersion.

Pooled or fitted by a prospectively frozen climate region:

- occurrence transition and spell-shape parameters;
- positive wet-amount body/tail shape and amount persistence;
- daily mean-temperature and diurnal-range autocorrelation/shape;
- storm-duration, time-to-peak, and peak-ratio conditional distributions; and
- solar, humidity, wind, and dew-point conditional distributions.

Only the forcing bundle defines the site's climate. Pooled parameters define
fine-scale texture and may not overwrite or infer missing forced fields.
Every dispersion field names its estimator, period, mask, units, and calendar
handling. Malformed or incomplete forcing fails closed.

An immutable transferable forcing product may be queried at development or
confirmation coordinates without reading their target series only when its
asset identity, fixed period, coverage, estimator, and period-overlap
limitation are frozen before candidate output. `candidate_fit` restricts
estimator fitting and product construction, not coordinate lookup in an
already frozen transferable product. If no transferable per-site variation
product exists for a required field, revision 1 must label that field as
region-pooled; it may not call a development/confirmation target read
"site-specific forcing."

## Deterministic moment reconciliation

For monthly precipitation covariance `C`, A11 enforces
`annual_variance = 1^T C 1`. For annual mean temperature the same constraint
uses the normalized vector of month day-count weights. The Phase-1 freeze must
name the norm, weights, solver, tolerance, serialization, and deterministic
tie breaks for the nearest-covariance problem subject to positive
semidefiniteness and the forced monthly diagonal.

Priority is prospective and fixed:

1. preserve monthly means exactly;
2. preserve monthly variances exactly;
3. adjust cross-month covariance minimally to satisfy annual variance when it
   lies in the feasible positive-semidefinite interval; and
4. when the annual target is outside that interval, project it to the nearest
   feasible boundary, retain the requested and effective values, and emit an
   explicit adjustment rather than silently changing a monthly quantity.

No generated realization is used to fit or repair this surface.

Independent precipitation and temperature PSD blocks are necessary but not
sufficient. Phase 1 must also freeze one joint dependence construction across
monthly precipitation totals, wet-day counts, monthly mean temperature, and
diurnal range. It must identify whether each requested dependence lives on the
observed or latent scale, prove joint feasibility, publish requested/effective
cross-block values and adjustments, and validate realized-scale dependence.
No target generator may be ratified from independently valid blocks alone.

## Daily oracle invariants

- Occurrence samples a first-order Markov path conditional on month length,
  exact wet-day count, and the previous month's terminal state by a
  forward/backward dynamic program. A second-order or renewal alternative is
  outside revision 1.
- For `K = 0` and zero monthly total, the oracle emits no wet amounts. For
  `K > 0`, positive relative event weights are sampled once and normalized
  once to the exact positive total. Exponential tilting is not part of revision
  1; it requires a prospective specification revision, not an output-time
  switch.
- Daily mean-temperature residuals are sampled from one frozen seasonal AR
  law and conditioned to exact zero mean and the forced within-month daily
  residual SD. This is distinct from interannual variance of monthly mean
  temperature. Positive daily diurnal range is sampled in log space from its
  separately forced mean/dispersion surface. Tmax and Tmin are derived from
  mean temperature and range, making ordering structural.
- Storm descriptors condition on event depth, month/season, and spell
  position. Secondary variables condition on generated occurrence and
  temperature context through bounded distributions.
- An infeasible conditional request fails with a typed reason. It is never
  resolved through rejection, clipping, fallback, or post-generation repair.

## Plan

1. **Prospective freeze.** Authenticate predecessor authorities; freeze the
   forcing/source/role contract, region map, calendars, units, schemas,
   reconciliation algorithm, stochastic laws, RNG/domain separation,
   comparator identities, station roster, horizons, replicate seeds,
   evaluation cells, aggregation, thresholds, confirmation lifecycle, CPU and
   storage ceilings, and terminal decision table. Use comparator and observed
   evidence only; produce no A11 candidate stream.
2. **Calendar and forcing preflight.** Build and verify representative forcing
   bundles; exercise leap-year and window-boundary fixtures; prove mask-based
   month/year eligibility, covariance feasibility behavior, canonical bytes,
   and source/provenance identity before fitting or substantial execution.
3. **Forcing builder and target generator.** Implement schemas, deterministic
   moment reconciliation, annual/monthly target sampling, reproducible random
   streams, and analytic/Monte Carlo fixture gates. No daily output enters
   evaluation until this integrated surface passes.
4. **Conditional daily oracle.** Implement exact-count occurrence bridging,
   positive total-preserving amounts, conditioned temperature/range, storm
   descriptors, and secondary variables. Verify support and exact monthly
   target realization structurally, not by repair.
5. **Integrated development.** Execute all four frozen arms as nested
   100-year streams with 30-year prefixes. Evaluate the complete frozen
   climate families and the pinned WEPP response matrix. Components do not
   receive separate promotion decisions.
6. **Conditional confirmation.** If and only if every development gate passes,
   seal candidate bytes, forcing rules, parameter/source identities, evaluator
   bytes, and the confirmation manifest; atomically consume the locked target
   series once and run the unchanged confirmation protocol.
7. **Terminal and closeout.** Emit one scientific terminal, reconcile every
   attempt/resource/artifact, record absent conditional artifacts explicitly,
   run independent review and repository gates, and update roadmap/catalog.

## Data calendar and missingness preflight

A11 consumes calendarized Daymet observations, so preflight is mandatory
before fitting, substantial CPU execution, or confirmation reservation.

- Source transform: inherited `daymet_official_365_v1` unless Phase 1 creates
  and validates a new A11 corpus identity.
- Normalized axis: complete proleptic Gregorian dates.
- Bounds: source bounds are inclusive; fitting/evaluation window ends are
  exclusive.
- Canonical A10 fit example: 1980-01-01 through 2009-12-31 contains 10,958
  calendar rows, 10,950 observed rows, and eight masked leap-year December 31
  rows.
- The preflight must pin axis/observed/masked counts for every consumed object,
  exercise February 29, absent December 31, and both window boundaries, and
  derive month/year eligibility from the conjunction of required-field masks.
- A complete date axis or a generic `365-day` label is never evidence of
  observational completeness.

The exact source-calendar transform, period, field mask, minimum monthly and
annual support, PRISM cell identity, and role for every forcing or target
quantity must appear in `artifacts/calendar-preflight-v1.json` and pass the
package verifier before the resource ledger can open.

## Execution and attempt semantics

All work starts from current `origin/main` and pushes only to `main`. The
single immutable `science_contract_id` is frozen before candidate output. Each
operational execution uses a fresh incrementing `attempt_id` and records:

```text
science_contract_id
attempt_id
source_commit
input_manifest_sha256
execution_status
science_status: NOT_EVALUATED | PASS | FAIL
resource_use
artifact_manifest_sha256
cleanup_status
```

A parser, evidence, environment, or execution failure remains
`science_status=NOT_EVALUATED`. A safe package-local retry may change only the
operational implementation or attempt identity, must preserve previous
evidence, and must remain inside the frozen aggregate resource ceiling.
Scientific output cannot authorize a changed contract. If the science
contract must change, this package closes honestly before any successor is
considered.

## Development evidence families

The Phase-1 freeze must enumerate every scalar cell and threshold for:

1. **Monthly climate:** means, SD/CV, wet-day counts, and
   precipitation-temperature dependence.
2. **Annual/interannual climate:** annual total/mean SD, lag-one dependence,
   low-frequency power, and cross-variable annual dependence.
3. **Daily precipitation:** wet/dry spells, second-order occurrence
   diagnostics, amount persistence, wet-day quantiles, and annual 1-, 3-, and
   5-day maxima.
4. **Thermodynamics and events:** temperature persistence and diurnal range,
   storm-descriptor distributions/dependence, compound wet/cold,
   wet/low-radiation, and hot/dry behavior, plus zero support violations.
5. **WEPP response:** annual runoff, peak runoff, soil loss, and frozen winter
   and rain-on-snow responses where supported by the pinned WEPP surface.

Thresholds and aggregation are calibrated candidate-blind from observed and
comparator evidence and serialized before any A11 stream. No favorable subset,
metric substitution, or runtime-selected comparator is permitted.

## Gates

- complete prospective design freeze and schema validation before candidate
  output;
- forcing-source, role, unit, calendar, missingness, PRISM-cell, and canonical-
  byte identity;
- exact deterministic reconciliation fixtures, including feasible-boundary,
  infeasible-target, singular, dry-month, and weighted-temperature cases;
- exact-count occurrence bridge normalization for every count in the frozen
  forcing-dependent feasible-count set and each reachable cross-month starting
  state; transition probabilities must give every emitted count positive
  conditional support;
- joint monthly precipitation/wet-count support: `K = 0` if and only if the
  monthly total is zero, while a positive total requires `1 <= K <= D`;
- positive wet-day amounts with exact monthly totals and no zero/non-finite
  normalizer;
- exact monthly mean and within-month daily-residual dispersion realization for
  temperature, distinct interannual monthly-target evidence, and structural
  `Tmax >= Tmin` without repair;
- deterministic seed/domain separation, replay, nested 30/100 prefix identity,
  and complete provenance;
- all four comparator arms, all frozen replicates, all evidence cells, and no
  unavailable mandatory result;
- zero physical-support violations;
- complete WEPP response matrix bound to exact climate, executable, input-deck,
  parser, and extraction identities;
- confirmation roles remain sealed unless the complete development decision is
  `PASS`, then one atomic sealed-to-consumed transition and no further tuning;
- one reconciled attempt/resource ledger and verified cleanup;
- independent review with zero unresolved P1/P2 findings;
- `git diff --check` and authored-text whitespace scan;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`; and
- for every new or changed production function in `crates/`,
  `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` followed
  by `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**'
  --fail-above`, with no production function above CRAP 30.

## Exit criteria

The package has exactly one terminal scientific disposition:

- `A11-CONFIRMATION-PASS`: development passed, the candidate was sealed, and
  the unchanged one-shot confirmation passed; this permits a separately
  authorized production-promotion decision, not implicit integration;
- `FAIL-A11-DEVELOPMENT`: the complete integrated development candidate failed
  one or more frozen climate or WEPP gates; confirmation remains unopened and
  the revision-1 architecture is final;
- `FAIL-A11-CONFIRMATION`: development passed but the sealed candidate failed
  the one-shot confirmation; no tuning or replacement follows; or
- `HOLD-A11-NOT-EVALUATED-<REASON>`: the package cannot reach a scientifically
  interpretable result inside its frozen inputs, authority, and aggregate
  resource ceiling. The exact failed prerequisite, evidence, and smallest
  decision required must be named.

No component-level pass, operational attempt, or development-only result
authorizes public runtime behavior.

## Artifacts

- [artifacts/README.md](artifacts/README.md) — required artifact names,
  conditionality, and evidence labels.
- [A11 ExecPlan](../../exec-plans/20260825-a11-forced-stochastic-generator.md)
  — living end-to-end implementation and execution plan.
