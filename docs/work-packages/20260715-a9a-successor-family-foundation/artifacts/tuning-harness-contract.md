# A9 tuning-harness contract

Status: executed optimizer-neutral contract; no optimizer implementation selected

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

### Frozen random-field contract

Simulation common random numbers use Philox4x32-10. A9b must publish golden
vectors for the exact encoding before observed tuning. The domain is
`cligen-rs/a9-crn/v1\0`; SHA-256 over length-prefixed campaign, site, burn,
component, Gregorian date, and variate-slot identities supplies key/counter
material. Occurrence, amount-body, amount-tail, event, latent-state, and daily-
context components own stable namespaces. A rejected or optional draw cannot
shift another component or date.

Fit, optimizer, parameter/member, and simulation domains are distinct. Their
artifacts record algorithm, version, full seed material, and derivation. No A9
domain consumes faithful `RANDN`, QC, or Rust faithful-state draws.

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

Resource governance requires:

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

The first development ceiling is fixed as follows; a later benchmark may
reduce it but cannot increase it after candidate outcomes are visible:

| Stage | Per candidate class | Station/burn/horizon policy |
|---|---:|---|
| analytic/support | 4,096 parameter proposals | no stochastic simulation |
| short screening | 256 configurations | six frozen anchor stations, two burns, 30-year prefix |
| full development | 64 configurations | complete development strata, four burns, one nested 100-year run |
| Pareto replay | eight configurations | complete development strata, eight burns, one nested 100-year run |

At most two candidate classes enter this campaign. A configuration rejected by
a hard analytic constraint does not consume a simulation slot but remains in
the append-only log. The executor uses at most eight worker processes, 12 GiB
aggregate resident memory, 24 hours per stage, 72 hours for the full campaign,
and 50 GiB retained output. Raw daily streams are retained only for fixtures,
failures under investigation, and the eight Pareto replays per class; all
attempts retain metrics and hashes. Artifacts at or above 10 MiB use Git LFS;
reproducible scratch streams remain outside Git.

Failure retries are limited to one byte-identical replay for infrastructure
errors. A second failure returns `evaluation_incomplete`; parameters, seed,
site, burn, and worker placement cannot change. Checkpoints are content-
addressed after every completed configuration.

## Gate calibration and frozen selection

Gate calibration uses 500 paired same-model/null replicates per horizon and
the versioned objective registry. Within each metric family and horizon, the
95th percentile of the maximum paired degradation defines the stochastic
noninferiority allowance, bounded below by the registry's absolute measurement
floor. The analogous improvement tail defines material improvement. Candidate
outputs are prohibited until the null artifact, exact numeric thresholds, and
their hash are frozen.

The complete Pareto vector is always published. The A9c selection rule is:

1. reject hard-infeasible, incomplete, or mandatory-stratum-ineligible fits;
2. reject a familywise material degradation in any mandatory family, stratum,
   or horizon;
3. maximize the worst regime-by-mandatory-family standardized improvement;
4. maximize materially improved families;
5. minimize median normalized distance;
6. minimize effective fitted parameter count; and
7. break an exact tie by candidate-class ID.

Final A9c replay uses eight burns. A9d confirmation uses twelve newly derived
burn identities and one 100-year stream per site/burn, with the 30-year prefix
evaluated from that same stream. A9d runs once and cannot feed the optimizer.

## Append-only evaluation state

Every attempted configuration has one state:

- `hard_infeasible` with exact failed constraints;
- `evaluation_complete` with full objective availability/vector;
- `evaluation_incomplete` with typed simulator/resource/infrastructure cause;
  or
- `dominated` as a derived label that never removes the underlying record.

Logs form a hash chain over canonical records. Resuming verifies the chain and
checkpoint hashes. A report may compact views, but the evidence archive retains
every proposal, failure, and dominated configuration.
