# A9 model-family envelope

Status: scaffolded design boundary; candidate classes not selected

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
Whether the eventual family supports an explicit predeclared fallback remains
an A9a decision.

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

A9a must define at least two genuinely distinct slots without fitting them.
Examples to assess, not selections, include:

- a duration-aware semi-Markov occurrence model with a conditional
  body/tail amount law; and
- a latent weather-regime model with joint occurrence/amount/event emissions.

An event-cluster or point-process class is eligible only if the data plan can
identify it. A block selector, fixed-count realization, or parameter relabeling
does not satisfy the independent-class requirement.

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
