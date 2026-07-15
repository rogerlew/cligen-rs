# A9 tuning-harness contract

Status: scaffolded requirements; no harness or optimizer selected

## Purpose and firewall

The harness exists to make model development practical across climate regimes.
It is explicitly developmental. It may fit, tune, compare, fail, and record
tradeoffs on authorized fit/development evidence. It may not inspect locked
confirmation targets and continue tuning.

```text
fit data -> parameter estimation
               |
development data -> objectives -> optimizer/model revision loop
               |
gate-calibration data -> thresholds and false-failure calibration
               |
freeze model + fit recipe + objectives + gates + seeds
               |
untouched confirmation -> one registered adjudication
```

The confirmation step is a new package with its own freeze. A failed
confirmation returns its registered stop; it does not reopen the optimizer.

## Harness boundaries

The harness is external research tooling until a candidate earns Rust
integration. It may call a candidate simulator through a versioned interface,
but it does not add candidate IDs to accepted runtime enums.

The optimizer is a plugin behind the harness contract. Changing from grid,
Bayesian, evolutionary, gradient-free, or another optimizer changes optimizer
provenance, not the climate model or fit-artifact schema.

## Required inputs

Each run consumes immutable, hash-identified inputs:

- candidate-class and parameter-schema version;
- exact executable/source identity;
- fit-artifact recipe and parameter bounds;
- observed-source objects and normalized logical-record hashes;
- data-role partition manifest;
- objective-registry version;
- hard-constraint registry;
- optimizer configuration and seed;
- simulation seed/burn matrix and horizon policy;
- calendar, units, wet-day threshold, missingness, completeness, and
  detrending rules; and
- CPU, wall-time, memory, evaluation-count, and storage budgets.

Unknown, missing, duplicate, nonfinite, wrong-unit, wrong-calendar, or
role-inconsistent input fails closed.

## Required outputs

Every attempted configuration produces an append-only record containing:

- parameter vector and canonical hash;
- parent/proposal identity;
- hard-constraint results and reasons for infeasibility;
- objective vector with availability and uncertainty;
- per-station, per-regime, per-horizon summaries;
- simulation and fit failures without coercion to a good/bad score;
- optimizer state needed for deterministic continuation;
- elapsed/resource use;
- Pareto rank/dominance computed by a versioned rule; and
- exact input/output identities.

The harness retains failed and dominated attempts. A report may summarize them,
but an unexplained survivor-only log is not acceptable tuning evidence.

## Hard constraints versus objectives

Hard constraints are distributional, physical, numerical, or interface
conditions whose violation makes a fit invalid. Initial categories include:

- probabilities, covariance/state matrices, and distribution parameters have
  valid support;
- wet amounts and event durations are finite and nonnegative/positive as
  specified;
- time-to-peak fractions and peak ratios remain in declared support;
- analytical or deterministic-quadrature monthly moment budgets are feasible;
- temperature/dew-point ordering and other declared physical constraints are
  satisfiable without output repair;
- RNG ownership, calendar, provenance, and deterministic replay invariants
  hold; and
- fit exposure, scale, and identifiability minima are met or yield a typed
  `fit_ineligible` result.

Objectives are stochastic climate distances and tradeoffs. They are not hard
constraints merely because a finite development realization misses a target.
The initial objective registry must cover:

- seasonal wet frequency and wet/dry spell distributions;
- higher-order occurrence residuals;
- wet-amount mean, SD/CV, lag dependence, upper tail, and threshold exceedance;
- zero-month frequency and monthly total mean/SD/CV;
- annual dispersion, cross-month covariance, lag persistence, and spectral
  summaries where supported;
- annual 1/3/5-day extremes;
- storm duration, time-to-peak, peak ratio, and depth/season dependence;
- wet/dry/event-conditioned Tmax, Tmin, dew point, radiation, and wind metrics
  for available sources;
- cold-wet precipitation/temperature and freeze-transition proxies; and
- intervention diagnostics, which should be zero for a direct generator.

Every objective defines units, estimator, direction, normalization, aggregation,
missing/unavailable rule, baseline-zero rule, minimum sample support,
uncertainty, and whether it participates in selection.

## Multi-objective rule

The development harness reports the full objective vector and Pareto frontier.
It must not begin with one opaque weighted score. A9a may define staged
feasibility filters and a later scalar or lexicographic selection rule, but:

- normalization and weights are calibrated without confirmation access;
- regime and station aggregation cannot allow humid breadth to hide an arid
  boundary failure;
- unavailable values cannot be treated as passes or favorable zeros;
- a baseline-zero denominator uses a registered absolute rule; and
- selection must expose material tradeoffs rather than average them away.

## Deterministic comparison

- Candidate comparisons use a frozen common-random-number matrix where their
  RNG contracts permit meaningful pairing.
- Multiple domain-separated burns are used at 30 and 100 years.
- A 30-year record is an exact prefix of its paired 100-year record only for
  candidates whose state and execution contract guarantees nesting.
- Optimization may use cheaper screening horizons/replicates only under a
  registered successive-fidelity policy that prevents favorable survivor
  bias from being hidden.
- Re-running a completed evaluation from the same artifacts reproduces exact
  engineering identities and metric bytes within declared numeric formats.

## Synthetic and adverse fixtures

Before observed tuning, A9b must implement fixtures for:

1. parameter recovery from synthetic data generated by each candidate class;
2. known non-identifiability and candidate-equivalence cases;
3. all-dry/zero-scale month behavior matching the A8b failure class;
4. sparse adjacent-wet and long-state exposure matching the A7b failure class;
5. tail-knot/support boundary behavior;
6. degenerate covariance, nonfinite input, duplicate key, and unit/calendar
   errors;
7. time-to-peak mass collapse and depth/descriptor independence defects;
8. wetness-context propagation to mock downstream consumers;
9. deterministic seed-domain separation and replay;
10. optimizer termination, crash recovery, budget exhaustion, and append-only
    log integrity; and
11. mutation tests proving confirmation-role data are rejected by fit and
    development commands.

Synthetic recovery demonstrates executable machinery, not suitability for
observed climate.

## Fit artifact

The external fit artifact records at minimum:

- model family/class/schema and parameter ordering;
- station/site/group identity and coordinates/elevation;
- source products, object/logical hashes, variables, units, calendar, timezone
  or day-boundary convention, period, completeness, flags, and wet threshold;
- preprocessing, detrending, event segmentation, aggregation, pooling, and
  regularization;
- optimizer/software version, fit seed, bounds, stopping rule, objective
  registry, resource budget, and diagnostics;
- uncertainty or ensemble-member identity where present;
- support/PSD/normalization/moment checks;
- fit role and explicit prohibition on confirmation-derived fitting; and
- canonical content hash used by generation provenance.

Fit artifacts are immutable inputs to later simulation. Runtime does not refit
or reinterpret missing values.

## Development/confirmation exposure policy

- Commands operating on fit or development roles refuse confirmation-role
  paths and hashes.
- Target acquisition for confirmation follows metadata-only station selection
  and a pre-access freeze.
- Access events are append-only and independently reviewable.
- A parser/calculation defect discovered before outcome access may use a
  bounded amendment and successor freeze.
- After confirmation outcome access, model, fit recipe, thresholds, objective
  normalization, selection rule, stations, periods, burns, and missingness
  rules cannot change within that campaign.

## Resource governance

A9a must turn “enough tuning” into bounded execution by specifying:

- maximum candidate evaluations by fidelity stage;
- maximum simulations and retained bytes per configuration;
- per-task and campaign wall-time/memory/CPU ceilings;
- checkpoint/restart identity;
- pruning rules fixed before results;
- failure retry policy that cannot preferentially rescue favorable candidates;
  and
- storage/LFS policy for raw streams versus reproducible derived metrics.

Resource exhaustion produces a typed incomplete result, not silent pruning or
a scientific failure score.
