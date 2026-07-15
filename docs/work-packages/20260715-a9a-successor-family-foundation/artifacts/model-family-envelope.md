# A9 model-family envelope

Status: executed, freeze-ready family boundary

## Purpose

This envelope defines what an A9 candidate must compose and what remains
separate. It prevents another isolated occurrence or annual-state intervention
from becoming a runtime before its coupled climate consequences are designed.

## Required hierarchy

```text
declared fit artifact + generation profile
  -> seasonal context
  -> optional latent context (only when justified)
  -> precipitation occurrence / spell state
  -> wet-day amount body + tail + temporal memory
  -> event descriptors conditional on amount, season, and state
  -> daily context made available to meteorological consumers
  -> typed daily output and quality evidence
```

### Seasonal context

- Represents seasonality explicitly through registered monthly, harmonic,
  spline, or other candidate-specific parameters.
- Defines interpolation, calendar, boundary, and year-crossing semantics.
- Does not infer climate regime from simulated output.

### Optional latent context

- May represent daily weather regimes, seasonal persistence, or low-frequency
  state only when the candidate class declares its probability law and the
  fitting evidence identifies it.
- A year-level state is not mandatory in the first core model. A5f0 retired
  the exact scalar-IID construction and A7a did not establish that daily gaps
  cause aggregate dispersion.
- State dimension, persistence, identifiability, and variance allocation are
  fit diagnostics, never implicit defaults.
- Neither first-core class includes a year-level state. A later low-frequency
  state is a new candidate class/version and is eligible only after the
  selected daily/event family leaves a measured residual on development data.

### Occurrence and spells

- Supports wet/dry frequency and spell-duration structure across month and
  year boundaries.
- Candidate classes may use duration-aware, higher-order, latent-regime, or
  another explicit stochastic law.
- A9c candidates must not be relabelings of one state machine. A pre-outcome
  equivalence review compares stationary distributions, transition laws,
  duration distributions, and likelihood parameterizations.

### Wet-day amount

- Represents distribution body, upper tail, and temporal dependence.
- States how amount dependence resets or persists through dry intervals.
- Analytically or numerically establishes expected wet amount and the monthly
  total moment contribution before generated-climate adjudication.
- Does not enforce realized month totals by rejection, scaling, or repair.

### Event descriptors

- Generates duration, time-to-peak fraction, and peak-intensity ratio from a
  joint conditional law that includes precipitation depth and season at
  minimum.
- Defines support, mass points, cold-weather behavior, dependence, and
  unavailable-data semantics.
- A descriptor-only candidate is not called a true subdaily generator.
  Subdaily intensity or hyetograph claims require high-resolution calibration
  and a separate output contract.

### Daily meteorological context

The precipitation engine emits a typed context, conceptually including:

- wet/dry and occurrence-state identity;
- precipitation amount and amount-state/quantile information;
- event/storm state and descriptors;
- seasonal and optional latent-state identity; and
- fit/profile identity needed for provenance.

Temperature, dew point, radiation, and wind components may remain faithful in
an early candidate, but the profile must declare which context fields each
consumer uses. Evaluation measures observed wet/dry/event-conditioned
relationships. Faithful exact identity is retained only for variables whose
declared computation and inputs are unchanged.

## Monthly and cross-scale contract

Every candidate defines, before climate generation:

- stationary/seasonal wet fraction;
- expected wet-day amount and variance;
- expected monthly total mean and a finite-window variance calculation or
  bounded numerical certification for 28-, 29-, 30-, and 31-day months as
  applicable;
- zero-month probability behavior in sparse climates;
- amount and occurrence covariance contributions;
- year-boundary and leap-day semantics; and
- which low-frequency moments are emergent versus explicitly state-driven.

These are distribution-level constraints. Exact finite realized monthly totals
are not targets and may not be manufactured through output conditioning.

## Across-regime fit semantics

One family may have multiple fit scopes:

- station-specific;
- regional or regime-stratified;
- hierarchical with partial pooling; or
- a declared hybrid selected during fitting.

Every fit artifact records the scope and source group. Runtime receives a
fully declared artifact; it does not classify the station from coordinates,
annual precipitation, generated output, or coefficient success.

Fit outcomes are typed:

- `fit_valid` — parameters and diagnostics pass registered constraints;
- `fit_ineligible` — exposure, scale, source, or identifiability requirement
  fails; or
- `fit_failed` — algorithm or numerical failure requiring investigation.

`fit_ineligible` is a scientific result, not permission to drop a month,
substitute a station, relax a threshold, or silently use another model.
The first A9 family has no runtime fallback: `fit_ineligible` and `fit_failed`
produce no climate. A fallback can enter only through a separately versioned,
prospective package after the first family is evaluated.

### Frozen pooling and exposure rules

Pooling membership is derived from the pre-fit metadata stratum/group manifest
and is immutable for a fit campaign. Candidate class, month, or station failure
cannot trigger a different group. The first rules are:

- both first classes use the same three-level hierarchy: station parameters
  nested in one frozen primary-stratum hyperdistribution, with the six stratum
  hyperdistributions nested in one global family hyperdistribution;
- the primary strata are hot-arid, arid-boundary, monsoonal-transition, non-
  monsoonal semi-arid, humid, and cold; cold-arid is a reporting cross-tag and
  cannot create another fit group;
- shrinkage strength is fitted on coefficient-fit data and frozen before
  development evaluation. The artifact records station, stratum, global, and
  effective-parameter contributions; and
- runtime receives a fully materialized station fit. It never reads the
  stratum label, applies a hyperprior, or chooses a pool.

- occurrence/seasonal shape: at least 15 complete daily years, 300 wet days,
  300 dry days, and 50 complete wet and dry spells overall;
- station-specific wet-amount body: at least 300 wet days; otherwise
  `fit_ineligible`;
- station-specific amount memory: at least 100 adjacent-wet pairs per retained
  season; a frozen hierarchical group may supply memory only when the station
  has at least 25 pairs and the group has at least 500 pairs;
- upper tail: at least 30 exceedances over a threshold selected from fit data
  by the frozen recipe, never from development/confirmation outcomes;
- event descriptors: at least 150 valid station events; a frozen hierarchical
  group may supply descriptors only when the station has at least 50 events
  and the group has at least 1,000 events across five or more sites; and
- conditional daily variables: at least 200 valid days in each compared
  condition or the metric is unavailable.

A structurally zero month is not standardized, imputed, or removed. Seasonal
functions borrow according to the pre-fit model law; exposure diagnostics
retain the zero cell.

## Identity axes

The following identities remain independent:

- station-document schema version;
- station/model-family identifier;
- fit-artifact schema and exact fit ID/hash;
- generation-profile identifier;
- optimizer and objective-registry versions;
- observed dataset/source-object identity;
- parameter-member identity;
- simulation RNG/burn identity; and
- typed/output/provenance schema versions.

Changing one does not automatically revise the others. A fit artifact cannot
silently select a profile, and a station schema cannot imply scientific
qualification.

## RNG and numerical contract

- Extension randomness is domain-separated from faithful CLIGEN streams.
- Draw ownership is specified by component and is deterministic under the
  candidate's state transitions.
- Fit, optimizer, parameter uncertainty, and simulation randomness use
  distinct identities.
- Replay, calendar, and 30-/100-year common-prefix claims are exact engineering
  invariants only when the candidate contract explicitly guarantees them.
- Production Rust remains `#![forbid(unsafe_code)]`, no-fast-math, fail closed,
  and CRAP-gated. Faithful f32/f64 arithmetic remains untouched.

## Candidate-class slots

A9c compares these two research class slots. This freezes state semantics, not
parameters, distribution subfamilies, state count, knots, or fitted values;
those are selected on fit/development evidence under the harness contract.

### `alternating_renewal_marked_v1`

- The observable wet/dry process alternates explicitly between wet and dry
  spells. Each seasonal discrete duration law is nongeometric unless its
  fitted support includes the geometric special case.
- There is no hidden weather state. The current spell type, elapsed duration,
  seasonal phase, and declared previous observable marks are the complete
  precipitation state.
- Positive wet amounts use a continuous body/tail law with dependence indexed
  by wet-run position, previous wet amount, antecedent dry time, and season.
- Event descriptors are joint marks conditional on depth, season, antecedent
  dry time, and cold context.

### `latent_regime_marked_v1`

- A finite hidden semi-Markov state has its own explicit duration law. Each
  state emits both wet and dry days with strictly interior wet probability;
  hidden state is not the observed spell label.
- Occurrence, positive amount, amount memory, and event descriptors are a
  joint zero-inflated marked emission conditional on hidden state and season.
- Observed wet/dry spells emerge from emissions and may cross hidden-state
  boundaries. State labels are canonically ordered by fitted wet probability,
  then wet-amount mean, to make replay and diagnostics stable.
- The admissible support excludes deterministic wet/dry emissions and a
  transition matrix that makes hidden state identical to alternating observed
  spells.

### Equivalence and identifiability gate

Before either class may enter A9c observed comparison, A9b/A9c must:

1. inspect the implemented likelihood/state factorization against the four
   bullets above and hash the implementation/schema;
2. demonstrate on synthetic renewal data that the renewal implementation
   recovers observable duration and mark parameters without an invented hidden
   state;
3. demonstrate on synthetic latent-regime data containing wet and dry
   emissions within each state that state occupancy, transition/duration, and
   joint emissions are identifiable up to the canonical label rule;
4. cross-fit both classes and report whether the fitted observable laws are
   indistinguishable within the registered synthetic tolerance; and
5. hold `MODEL-CLASS-EQUIVALENCE` if either implementation enters the excluded
   degenerate intersection or the same state/probability law can be obtained
   by a bijective parameter relabeling.

The classes may approximate one another on finite data; that is model
uncertainty, not structural isomorphism. A block selector, fixed-count path,
output repair, or a renamed A7b four-state chain cannot occupy either slot.

## Descriptor-level event law

Both class slots use the same source-variable interface and event definition
but fit independent conditional laws. USCRN five-minute precipitation defines
`a9_uscrn_event_6h_v1`: 72 consecutive valid zero intervals separate events;
missing separation intervals invalidate the event; cross-day events remain
whole. Depth, duration, earliest-peak time fraction, and peak/mean rate ratio
are joint marks. Temperature supplies a cold-context covariate without a
rain/snow interpretation.

This is not a true subdaily generator. It produces the daily/event descriptors
already consumed by the climate row. It does not emit five-minute rain,
hyetographs, EI30, or a single-design-storm series.

## Explicit non-goals for the first A9 core

- automatic climate classification;
- one coefficient vector forced across every regime;
- guaranteed realized monthly totals;
- a mandatory annual scalar state;
- multisite/spatial coherence;
- future-scenario forcing;
- true subdaily output without high-resolution evidence;
- complete replacement of every meteorological component;
- deprecated single-storm generation; and
- production/default promotion.

## Foundation terminal boundary

The envelope is ready for A9b only as a research contract. No class has been
implemented, fitted, ranked, or assigned a runtime ID. A9b may implement the
harness, canonical schemas, RNG vectors, synthetic fixtures, and mock plugins;
observed-data candidate tuning begins no earlier than a separately dispatched
A9c.
