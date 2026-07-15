# A5e0 — Direct Annual-Latent-State Pilot

Status: `EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`
Date: 2026-07-14
Evidence mode: Mixed
Execution authorization: operator authorized execution on 2026-07-14

## Objective

Implement and evaluate one deliberately low-complexity, rank-one annual-state
extension at three exposed development stations. The package asks only whether
an annual state applied inside the daily generator can improve the targeted
interannual dispersion and dependence while preserving monthly and daily
climate behavior. It ends with either `CONTINUE-A5E1` or `CLOSE-MECHANISM`; it
cannot promote a public profile.

## Decision boundary

- A5e0 evaluates one mechanism, not a family tournament.
- Climate properties are ensemble targets. Individual 30- or 100-year paths
  are not constructed or optimized to replay population moments.
- A scientifically negative result is a completed experiment with decision
  `CLOSE-MECHANISM`, not a hold and not authority for another optimizer.
- `CONTINUE-A5E1` authorizes only the separately dispatched 17-station
  development expansion already named in the roadmap.
- A materially different latent dimension, dependence model, parameter seam,
  or fitting rule requires a new prospective work package.

## Scope

Included:

- one independent scalar standard-normal state per synthetic year;
- 48 fitted monthly loadings per station, 144 total: precipitation occurrence,
  precipitation amount, Tmax mean, and Tmin mean, each with 12 direct monthly
  values in one three-station bundle;
- deterministic variance reallocation and feasibility checks, with derived
  compensation terms kept distinct from fitted loadings;
- one strict development-only coefficient bundle, one package-local research
  runner, and one combined campaign evidence record;
- integration at the generator's precipitation occurrence/amount and
  temperature-mean seams before daily draws;
- a dedicated, domain-separated extension RNG that never consumes `k1`–`k10`;
- continuous generation with `qc_filter: off` and `interpolation: none` only;
- three predeclared exposed stress stations, eight paired replicate records,
  and 30-/100-year ensemble analysis against the exposed Daymet evaluation
  targets;
- unchanged-storm-shape, descriptor, winter, daily-range, and dew-point
  diagnostics; and
- a concise public experiment report produced under the scientific report
  standard and authoring protocol.

Excluded:

- complete-year libraries, resampling, selectors, finite-count balancing,
  MILP, annealing, cooldown/reuse rules, or path optimization;
- Fourier/EOF compression, more than one latent dimension, serial persistence,
  VAR, HMM, or regime switching;
- post-generation overlays or changes to generated rows after the faithful
  storm/daily chain;
- observed-substitution, single-storm, and design-storm modes;
- interpolation modes other than `none` and annual recomputation of `r5monb`;
- a public station-schema, runspec, provenance-v1, typed-output, profile-enum,
  or default change;
- confirmation data, the 17-station expansion, GHCN adjudication, WEPP runs,
  candidate promotion, and production deployment; and
- exact finite-path climate-moment gates or significance claims from individual
  generated paths.

## Authority

- [ADR-0001](../../decisions/0001-source-code-authority-port.md) and the
  vendored Fortran govern the unchanged faithful path.
- [ADR-0002](../../decisions/0002-quality-metrics-authority.md) makes the
  observed-climate and station-contract quality vector authoritative for
  extensions.
- [ADR-0004](../../decisions/0004-a5b-interannual-no-promotion.md) requires a
  prospective successor, analytic variance-budget feasibility, variance
  reallocation, integrated precipitation behavior, and downstream guards.
- The operator-corrected [roadmap](../../ROADMAP.md) supersedes the A5d
  selector follow-ons and fixes this package to one scalar annual state.
- The original
  [interannual design seam](../20260712-faithful-generation-spec/artifacts/interannual-variation-follow-on.md)
  supplies the statistical-level, RNG, precipitation-seam, and dew-point
  cautions. Its older three-component latent-vector suggestion is not the A5e0
  mechanism.
- [SPEC-A5-EVALUATION revision 3](../../specifications/SPEC-A5-EVALUATION.md)
  supplies the quality leaves, metric-template identities, observed target
  surfaces, and base absolute/relative distance rules used where this package
  does not say otherwise. `SPEC-A5E0-PILOT` owns A5e0's exact membership,
  stated target/distance overrides, aggregation hierarchy, and decision
  arithmetic. A5e0 does not amend the A5b/A5c promotion contract or claim to
  pass its seven gates.
- A package-local `SPEC-A5E0-PILOT` must be authored and registered before
  fitting or implementation. It is the sole normative study contract and owns
  exactly two machine resources: the coefficient-bundle schema and a combined
  campaign-evidence schema containing run records, aggregate results, and the
  decision. These are research surfaces, not accepted public profile values.

## Prospective study design

### Mechanism

The research profile identifier is `a5e0_direct_annual_state_v1`; the fitting
recipe is `a5e0_direct_monthly_loading_fit_v1`; and the coefficient schema is
`a5e0_direct_annual_state_coefficients_v1`. Phase 1 freezes these identities,
the mechanism, fitting recipe, numerics, schemas, and decision rule in
`SPEC-A5E0-PILOT` before fitting or implementation. After that point there is
no amendment, certificate, or outcome-time repair chain; a material contract
defect produces a hold and requires a newly dispatched package.

For each synthetic year, draw exactly one `z ~ N(0,1)` and use that same value
at all four parameter seams. Annual states are IID; the faithful weather-state
chains still carry continuously. There is no finite annual-state table,
recentering, normalization, selection, or ordering.

For month `m`, let `p_ww` and `p_wd` be the base CLIGEN transition
probabilities, `q = p_wd / (1 - p_ww + p_wd)`, and
`rho = p_ww - p_wd`. The annual wet fraction parameter is
`q_y = logistic(a_m + occurrence_loading_m * z)`. Reconstruct
`p_wd_y = (1 - rho) * q_y` and
`p_ww_y = rho + (1 - rho) * q_y`. Invalid probabilities or an infeasible
station/month fail before climate generation. The 12 intercepts are solved
jointly so the model-implied expected wet-day occupancy in each month, under
the continuous finite-calendar Markov recurrence, equals the corresponding
base-generator occupancy; merely imposing `E[q_y] = q` is not sufficient.

Wet-day amount mean uses a positive transform
`mu_y = mu * exp(c_m + amount_loading_m * z)`. Because occurrence and amount
share `z`, centering is occupancy-weighted. If `w_m(z)` is the model-implied
expected wet-day occupancy from the continuous finite-calendar Markov
recurrence, the fitting equations preserve
`E[w_m * mu_y] / E[w_m] = mu` and
`E[w_m * (residual_sd_m^2 + mu_y^2)] / E[w_m] = mu^2 + sigma^2`.
The spec freezes the recurrence/initial-state treatment and quadrature used to
solve those equations. Precipitation skew remains the base station value; the
0.01-inch generated-amount floor is measured as a departure from the ideal
parameter identity, not hidden in post-generation correction.

Tmax and Tmin means use additive monthly loadings, with residual daily SD
derived from `sqrt(base_sd^2 - loading^2)`. Any invalid probability or negative
residual variance is a valid H0 failure that closes the mechanism before
candidate output. An all-zero bundle bypasses every transform and returns the
original base `f32` bits. A wholly zero occurrence surface returns base `prw`
bits even when other seams are active. Within a mixed occurrence surface, a
zero monthly loading remains in the joint finite-calendar intercept solve and
does not promise base bits. Individual zero amount or temperature loadings do
bypass their local transform and return the base mean/SD bits.

The execution spec must freeze the quadrature, root solver, tolerances,
rounding, bounds, and the exact mapping from fitted observed/baseline moments
to loadings before code is integrated. Observed output SD is never copied
directly into a latent loading. Occurrence and amount loadings are dimensionless
logit/log-scale values; temperature loadings are stored as `f64` degrees C.
The generator converts temperature loadings to degrees F in `f64` and narrows
once to `f32`; amount operations start from the consumed inch-valued `f32`
station parameter widened to `f64`. All extension transcendentals use pinned
`libm` behavior, never platform `std` methods.

The same annual effective `prw` surface must be routed to both the amount mask
in `ranset` and the wet/dry branch in `gen_precip`; otherwise the amount stream
desynchronizes. This is parameter-routing identity, not equality of realized
wet/dry decisions: `RansetState.ell` and the daily generator's warm-start/state
remain distinct source-faithful chains, carry continuously across month/year
boundaries, and are never synchronized or reset by A5e0. Effective annual
values are supplied as an explicit parameter view, not written back into the
fixed station model. The pilot is restricted to `interpolation: none` because
Fourier/Yoder interpolation state is prepared once from base monthly arrays.

`r5monb` remains the once-per-run base-station storm-shape calculation. It is
not recomputed from annual effective precipitation parameters because that
would introduce an unfitted fifth seam. The base dew-point/RH parameter has no
new loading; the derived Tmin anomaly is applied consistently at the existing
dew-point mean seam. Resulting storm and dew-point behavior is measured rather
than repaired after generation.

The annual-state PRNG is the existing `splitmix64_box_muller_v1` algorithm
under the new domain `cligen-a5e0-annual-state-v1\0`. Its station-specific
stream key includes station ID and replicate master seed. Each year consumes
two open-interval uniforms, emits the cosine normal, and discards the sine
mate. It draws once per year regardless of horizon. The dedicated PRNG never
reads or advances `k1`–`k10`; nonzero occurrence changes may legitimately
change later faithful-stream consumption through the unchanged generator.

### Development stations

Stations are selected only from A5a 1980–2009 fit-period metadata, before A5e0
output: the driest arid station by mean annual precipitation, the wettest humid
station by that measure, and the coldest cold station by annual-mean Tmin;
ties break by station ID. They are stress cells, not a representative sample.

| Stress cell | Station | A5a regime | Fit-period selection value |
|---|---|---|---:|
| dry | `ca042319` — Death Valley, CA | arid | precipitation 58.9713 mm/year |
| wet | `ms227840` — Saucier Experimental Forest, MS | humid | precipitation 1786.2243 mm/year |
| cold | `co051660` — Climax, CO | cold | Tmin mean -7.1575 °C |

The source is the hash-pinned A5a observed-target corpus. Coefficient fitting
may read only Daymet 1980–2009. The same stations, Daymet 2010–2025 surface,
and A5b results were already inspected and are disclosed design inputs to this
scaffold. A5e0 is therefore a prospective development test on an exposed
surface, not independent confirmation or unexposed model selection. Once the
Phase 1 spec is registered, only A5e0 candidate output remains sealed; A5b
output may not tune coefficients, seams, thresholds, or decisions. No
confirmation object is accessed.

### Replicates and matrix

The eight fixed values below seed only the station-specific annual-state PRNG.
The faithful streams use disjoint, auditable substreams of each source
`k1`–`k10` recurrence instead of arbitrary four-word states. Order stations
lexicographically by ID and set
`segment = 8 * station_ordinal + (replicate - 1)`. For every `k` stream, both
arms start at its canonical source state advanced exactly
`segment * 500_000` raw recurrence updates by exact modular integer
skip-ahead; all runs then use burn zero. The shortest canonical stream period
is 12,500,000 raw updates, so Phase 1 must verify the ten periods and prove
from a conservative per-run bound that every stream consumes fewer than
500,000 raw updates and no one of the 24 segments overlaps or wraps. The bound
counts internal updates skipped when a rounded endpoint is rejected, not only
returned deviates. Stream ID is intrinsic because each substream starts from
its own canonical `k` state.

The annual-state key is derived separately from
`(station_id, replicate_master_seed)` under its dedicated domain. Both arms
receive the same faithful substream for a station/replicate; only the candidate
uses the annual state. Thus replicates use nonoverlapping pseudorandom
substreams and paired common random numbers across arms, without claiming that
pseudorandom trajectories are formal statistical IID samples.

| Replicate | Master seed |
|---:|---|
| 1 | `0x0c8862ed55f21e2e` |
| 2 | `0x0c268832683959b1` |
| 3 | `0x1a237b2016b95a3f` |
| 4 | `0x91328e5fa9a0e916` |
| 5 | `0x0ee45605e7d362c3` |
| 6 | `0xc59c065475f321a3` |
| 7 | `0x9d9ef1d097f866ab` |
| 8 | `0x50984769b3e59a89` |

The primary matrix is `3 stations × 8 replicates × 2 arms = 48` 100-year
executions. Both arms use the faithful 5.32.3 generator core with
`qc_filter: off`; `baseline` uses the bit-preserving zero-loading bypass and
`candidate` activates `a5e0_direct_annual_state_v1`. All runs begin at
synthetic year index 1. The first 30 complete years of each run form the paired
30-year analysis, yielding 96 arm/horizon cells. Standalone 30-year runs are
conformance checks only: their typed daily rows must equal years 1–30 of the
matched 100-year run. Complete `.cli` bytes are not compared because headers
and termination records legitimately encode the requested horizon.

Because it starts from package-selected nonoverlapping substreams, `baseline`
is an A5e0 research baseline using the faithful generator core, not an accepted
public `faithful_5_32_3` profile run. The unchanged public profile remains the
byte-parity control in the repository gates.

Results report all eight paired values plus conventional medians (the mean of
the fourth and fifth ordered values) and ranges. No confidence interval,
significance claim, or independence claim about the three deliberately chosen
stress stations is made.

### Hypotheses and continuation rule

**H0 — Analytic feasibility** requires every station/month/seam budget and
transform to be feasible under the frozen equations. A valid infeasibility is
a completed negative result: H0 fails, H1–H3 are `NOT-EVALUATED`, and the
decision is `CLOSE-MECHANISM`. A numerical implementation defect is a hold,
not an H0 result.

H1–H3 apply separately at 30 and 100 years. Every registered cell must be
available for every station, arm, and replicate. For an arm/station/family,
compute each replicate's equal-weight mean cell distance, then take the
conventional median across eight replicates. Composite arm scores average the
named family distances before the candidate/baseline ratio is formed. The
three-station median is the middle station score. All thresholds are inclusive.
If a baseline aggregate is zero, a zero candidate aggregate has ratio 1.0 and
a positive candidate aggregate is encoded as `UNBOUNDED` and fails; missing or
otherwise undefined required values produce `EXECUTED-HOLD-EVIDENCE` and are
never dropped from a smaller median.

- **H1 — Intended signal.** Membership is narrower than the inherited family
  labels: annual and monthly nonnegative-variable cells include `sd` and `cv`
  only, temperature cells include `sd` only, and all registered cross-month
  and cross-variable dependence cells are included. Means are excluded from
  H1 and remain preservation evidence. The equal-weight four-family composite
  has a three-station median candidate/baseline distance ratio no greater than
  0.90 and no station ratio greater than 1.25.
- **H2 — Primary preservation.** For each of `monthly_station_contract`, the
  package-local `interannual_mean_contract` containing the nonnegative-variable
  `mean` cells excluded from H1, and `precipitation_structure`, the
  three-station median distance ratio is no greater than 1.10 and no station
  ratio exceeds 1.25. The package-local
  `daily_thermodynamic_contract` contains two Celsius absolute-error cells:
  daily-range mean targets Daymet 2010–2025 `tmax - tmin`, while dew-point mean
  targets the base station contract because Daymet has no dew-point field.
  Those two equally weighted cells form the arm score; its median ratio is no
  greater than 1.25 and no station exceeds 1.50. At Climax, the complete
  `winter_air_temperature_proxies` ratio is no greater than 1.25.
- **H3 — Catastrophic-regression guard.** For each of
  `interannual_annual_dependence` and `interannual_low_frequency`, the
  three-station median ratio is no greater than 2.0 and no station exceeds
  3.0. The `descriptor_guard` compares candidate to its paired baseline and
  maps every cell to `[0,1]`: time-to-peak distribution cells use absolute
  difference; peak-intensity-ratio distribution cells use
  `abs(candidate - baseline) / max(abs(candidate), abs(baseline))` with
  both-zero defined as zero; and correlation cells use absolute difference
  divided by two. Average cells within those three subfamilies, weight the
  subfamilies equally, then take the median across replicates. Its three-station
  median must not exceed 0.50 and no station may exceed 0.75. This is one
  coarse ensemble guard, not a per-cell or per-path acceptance system.
- **H4 — Engineering invariants.** Every hard gate below passes. These are
  exact per-output requirements, not climate-moment requirements.

Detailed diagnostic cells are reported, but cannot override the aggregate
rules. GHCN and WEPP are outside A5e0. `CONTINUE-A5E1` requires H0 and H1–H4,
with H1–H3 passing at both horizons. Any valid H1–H3 failure yields
`CLOSE-MECHANISM`; an H4 failure yields the applicable hold. Near misses do not
authorize tuning against A5e0 outcomes.

## Plan

1. **Freeze before code or output.** Record the source commit, authorities,
   station/source hashes, profile/RNG identities, matrix, exact metric cells,
   aggregation, and decision arithmetic in the single `SPEC-A5E0-PILOT`.
   Register its coefficient-bundle and campaign-evidence schemas before
   fitting or implementation; do not create freeze amendments or certificates.
2. **Establish analytic feasibility.** Derive the occurrence, amount, and
   temperature moment budgets; implement deterministic fit/quadrature fixtures;
   fit one three-station bundle from 1980–2009 only; and close the mechanism
   without climate output if any required station/month is infeasible.
3. **Implement the integrated research path.** Add the annual effective-
   parameter view, independent seed derivation, extension RNG, strict bundle
   intake, package-local runner/evidence record, and diagnostics. Keep public
   compatibility surfaces and faithful functions unchanged. The single
   campaign-evidence record is the mandatory A5e0 research provenance: it
   declares every climate and quality artifact's station, replicate, substream
   segment, master seed, arm, research profile, coefficient hash, RNG
   identities, source commit, and output hash. Public provenance v1 is not
   fabricated for research output.
4. **Pass hard conformance gates.** Prove zero-loading identity, RNG isolation,
   effective-probability routing, fail-closed inputs/modes, deterministic
   replay, row-prefix identity, and all faithful goldens before scoring A5e0
   climate.
5. **Execute and analyze once.** Complete and validate all 48 primary runs,
   derive the 96 horizon cells, run the frozen analysis, and emit the compact
   result and machine decision. Do not alter the mechanism or rule after
   opening candidate scores.
6. **Report, review, and close.** Author the public report under the active
   report standard. Use read-only evidence, methods, and reference analysts
   plus one consolidated accuracy/scientific-validity/consistency review. Run
   all gates, record the terminal decision, update the catalogs/roadmap, and
   leave A5e1 unauthorized unless the decision is `CONTINUE-A5E1`.

## Execution & dispatch

The scaffold turn did not execute A5e0. The operator subsequently authorized
execution from the repository on `main`. No side branch was used. The lead was
the sole editor and delegated agents were read-only. Execution did not commit
or push because no such instruction accompanied the kickoff.

## Execution result

H0 passed its recorded analytic checks. The 48-run matrix and 96 arm/horizon
cells completed, and independent replay found no disagreement in product
hashes, aggregation arithmetic, formatted-row prefixes, or realized RNG
states. The provisional H1--H3 analysis found:

- H1 failed at both horizons: three-station median candidate/baseline error
  ratios were 1.2076 at 30 years and 1.2665 at 100 years, versus the 0.90
  continuation limit; every station ratio exceeded 1.0 at both horizons;
- H2 passed at 30 years and failed at 100 years because the monthly-station-
  contract median was 1.1451 versus its 1.10 limit; and
- H3 passed at both horizons under both the scaffold's composite descriptor
  reading and the specification's per-subfamily reading.

That climate-only mapping is `CLOSE-MECHANISM`, but it is not the terminal
package decision. The named execution-base commit contains the scaffold, not
the exact specification, fitter, implementation, or analyzer, and their exact
pre-output hashes were not independently sealed. The fitter, runtime intake,
formatted-prefix check, and RNG evidence also did not demonstrate every H4
obligation in its predeclared form. H4 therefore fails and the controlling
decision is `EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`.

The implementation and outputs are retained as exploratory evidence only.
There was no post-output tuning, public-profile promotion, confirmation
access, commit, or push. A5e1 remains unauthorized. This package does not
scaffold a repair campaign; the default next action is to stop this mechanism
unless an operator later dispatches a clean prospective reproduction.

## Gates

Repository gates:

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`
- `git diff --check`

Package-specific gates:

- the coefficient bundle and single campaign-evidence record validate against
  the schemas owned by `SPEC-A5E0-PILOT`, with duplicate-key, unknown-field,
  and nonfinite-number rejection;
- every authority, station input, Daymet source, coefficient bundle,
  executable, climate/quality output, and analysis is hash-bound in that
  record, and every research output is semantically labeled with the A5e0
  profile, study arm, station/replicate seeds, coefficient identity, and RNG
  identities;
- analytic/synthetic fixtures reproduce the centering and second-moment
  identities and reject negative residual variance or invalid probabilities;
- an all-zero bundle bypasses all transforms, reproduces the paired baseline
  typed rows, and finishes with the same `k1`–`k10` states as the matched
  baseline; zero-surface and local-zero tests follow the mechanism rules above;
- the same annual effective transition surface is routed to `ranset` and
  `gen_precip` while their distinct state machines and continuous carry are
  preserved, with dedicated boundary tests;
- exact skip-ahead and annual-state RNG goldens, all ten canonical-period
  checks, the fewer-than-500,000-raw-update bound and 24-segment no-overlap
  proof, fixed one-normal-per-year consumption, deterministic replay, and
  30-/100-year typed-row prefix identity pass;
- unsupported modes/interpolation, missing or unknown fields, wrong hashes or
  array lengths, nonfinite values, and invalid derived values fail closed;
- every primary and prefix-conformance output has a complete, ordered calendar
  and finite values satisfying the registered physical row constraints;
- all existing faithful `.cli` goldens remain byte-identical and accepted
  public schemas/defaults remain unchanged;
- all 48 primary executions and 96 analysis cells validate before scoring;
- the frozen analyzer reproduces H0–H3 membership and arithmetic and reports
  every replicate, station, family, horizon, zero denominator, and unavailable
  value without substitution, including the thermodynamic target surfaces and
  three descriptor normalizations;
- the report and consolidated review pass the active report-authoring protocol
  and contain no independent-confirmation claim; and
- no production function exceeds CRAP 30.

## Exit criteria

### `EXECUTED-COMPLETE` with `CONTINUE-A5E1`

All hard gates pass, H0 passes, H1–H3 pass at both horizons, the report/review
is accepted with no open P1/P2 finding, and the machine decision authorizes
only the conditional A5e1 development expansion.

### `EXECUTED-COMPLETE` with `CLOSE-MECHANISM`

The analytic moment budget validly fails H0, or valid climate evidence fails
H1–H3 at either horizon. H1–H3 are explicitly `NOT-EVALUATED` after an H0
failure. The result is retained as a completed negative experiment. A5e1
remains unauthorized, and no count solver, path optimizer, threshold
relaxation, or post-outcome mechanism repair follows.

### Legitimate holds

- `EXECUTED-HOLD-IMPLEMENTATION` — an unresolved code, numerical, or strict-
  intake defect prevents valid candidate execution;
- `EXECUTED-HOLD-EVIDENCE` — required hashes, source objects, matrix cells, or
  review evidence cannot be validated;
- `EXECUTED-HOLD-REPRODUCIBILITY` — replay, RNG isolation, faithful parity, or
  prefix identity fails; or
- `EXECUTED-HOLD-PROSPECTIVE-BOUNDARY` — coefficients or rules were tuned with
  evaluation-period or A5e0 candidate outcomes.

Every hold names the exact blocker. A failed scientific hypothesis is not a
hold.

## Retained artifacts

Execution produced the pilot spec and two schemas, one three-station
coefficient bundle, feasibility and analysis records, one combined campaign-
evidence record, one post-output descriptor-rule audit, one consolidated
review, one gate record, and the report files required by the report protocol.
The campaign record explicitly binds a post-output implementation-tree
snapshot rather than fabricating an implementation commit or prospective
freeze. Raw climate outputs remain reproducible working data under
`target/a5e0/`; no A5e0 LFS archive is required.
