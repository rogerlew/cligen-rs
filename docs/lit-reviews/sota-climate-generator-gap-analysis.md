# State-of-the-Art Climate Generators: Gaps and Feasibility for `cligen-rs`

Date: 2026-07-12
Author: OpenAI Codex
Status: informational research synthesis; not a model or interface decision
Evidence labels: **Measured** = quantified in this repository; **Structural** =
absent by source/spec inspection; **Published** = reported by the cited primary
source; **Proposed** = implementation recommendation requiring adjudication

The companion
[`annotated bibliography`](sota-climate-generator-annotated-bibliography.md)
provides full citations, DOIs, access status, and source-acquisition guidance.
References below use its `AB-xx` identifiers.

## Executive finding

The first scientific study should target CLIGEN's measured aggregate and
interannual variance deficit, after behaviorally inert station-schema/
provenance modernization and a quality-metric expansion. An explicit
interannual climate state is the leading candidate, but acquired full-text
evidence shows that richer daily precipitation structure is a necessary causal
counterfactual. The best annual-state comparison is not “monthly SD versus
Fourier” as two complete models: monthly SDs are output targets, while
Fourier/EOF coefficients are a representation that still needs a coefficient
distribution, covariance, and year-to-year evolution.

The next priorities are precipitation tails and multi-day dependence, then
cross-variable dependence. A full subdaily rainfall process is highly relevant
to WEPP erosion but requires substantially more data and work. Multisite
weather and neural climate systems are later interoperability projects, not
good first changes to the point-scale generator.

The roadmap direction is therefore supported:

1. modernize schema, provenance, typed output, and fitting/validation surfaces;
2. compare declared annual-state candidates and a narrowly scoped daily
   precipitation-structure counterfactual;
3. promote one only if it improves the observed-climate quality vector;
4. then address precipitation extremes/dependence and daily multivariate
   coherence;
5. treat spatial/subdaily field generators and ML downscalers as external
   producers before considering native implementations.

## 1. What counts as a peer

“Climate generator” currently covers systems with very different objectives.
Conflating them produces a misleading feature race.

| Class | Examples | Generates | Relationship to CLIGEN |
|---|---|---|---|
| Impact-model stochastic weather generators | WeaGETS, GWEX, AWE-GEN, BayGEN, Rglimclim, MSTWeatherGen, `swxg` | Arbitrarily long synthetic station/network weather from fitted climatology | Direct comparison class |
| Storm/rainfall generators | Bartlett–Lewis models, STORM, RainyDay, AWE-GEN-2d | Subdaily point events or spatial rainfall fields, sometimes conditioned on lower-frequency state | Direct for precipitation/event features; incomplete forcing by themselves |
| Scenario/downscaling layers | California regime WGEN, simulation-based climatology matching, generative downscalers | Weather under prescribed climate/circulation/coarse-model conditions | Relevant to future profiles and external forcing |
| Forecast and climate emulators | GenCast, NeuralGCM, ACE-family systems | Global forecast or boundary-forced atmosphere trajectories | Not direct peers; possible future coarse forcing sources |

The SOTA comparison in this review means mature or recent methods that
materially improve impact-model forcing: hierarchical variability,
precipitation persistence/tails, multivariate consistency, subdaily structure,
spatial coherence, uncertainty, and controlled nonstationarity. Forecast skill
at 1–15 days is not a CLIGEN acceptance criterion.

## 2. Faithful CLIGEN baseline

CLIGEN 5.32.3 as implemented in `cligen-rs` is a fixed-climatology,
seasonally varying, single-site daily generator. Its exact behavior is specified in
[`SPEC-FAITHFUL-GENERATION`](../specifications/SPEC-FAITHFUL-GENERATION.md),
with field dependencies in the package
[`parameter-to-output map`](../work-packages/20260712-faithful-generation-spec/artifacts/parameter-to-output-map.md).

| Dimension | Faithful capability | Important boundary |
|---|---|---|
| Station climate | Twelve fixed monthly parameter sets, reused every synthetic year | No year-level climate state |
| Within-year seasonality | Fixed-month, linear, deterministic Fourier, or Yoder–Foster interpolation, depending on variable and run option | Faithful Fourier interpolation adds no stochastic interannual variation |
| Precipitation occurrence | First-order, two-state wet/dry Markov chain using monthly `P(W|W)` and `P(W|D)` | One-day state; no explicit higher-order, semi-Markov, or latent regime state. QC-conditioned uniforms mean realized spells are not an ideal geometric chain |
| Wet-day amount | Monthly mean/SD/skew through the faithful cubic transform | No explicit heavy-tail family, amount persistence, or climate regime |
| Tmax/Tmin/dew point | Normal deviates with hard-coded smaller-SD algebraic coupling | No fitted covariance model or precipitation-conditioned parameter surface |
| Radiation | Monthly normal, bounded by astronomical maximum/floor | Generated independently of wetness |
| Wind | Monthly direction frequencies and direction-conditioned speed | No fitted dependence on precipitation/temperature/storm state |
| Storm output | One duration/time-to-peak/peak-ratio tuple on each positive-rain day | No hyetograph, multiple events/day, or gridded event field |
| Observed mode | Positional substitution of precipitation and the Tmax/Tmin pair | Other variables remain generated; legacy quantization and EOF semantics |
| Random process | Ten legacy streams plus trajectory-conditioning QC | Modern extension RNG/state must not consume or silently replace these streams |
| Scientific reporting | Quality groups A–D/P, with decadal blocks where defined | Missing several candidate-specific low-frequency, dependence, and subdaily metrics |

**Measured:** Q3 found that faithful QC reduced annual precipitation
dispersion by about 19% at 30 years and 11% at 100 years relative to
`qc_filter: off`; in single-burn descriptive comparisons, `off` was closer to
Daymet annual-total CV at 14 of 17 stations at 30 years and 15 of 17 at 100
years. Even `off` under-dispersed observed monthly precipitation-total SD in
9–11 of 12 calendar months, while faithful under-dispersed all 12. See the
[`frontier analysis`](../work-packages/20260710-q3-qc-filter-dissection/artifacts/frontier-analysis.md)
and
[`monthly-SD addendum`](../work-packages/20260710-q3-qc-filter-dissection/artifacts/monthly-sd-addendum.md).

That evidence establishes a low-frequency output deficit, not its unique
cause. Published work shows that higher-order occurrence and amount dependence
can recover much of aggregate precipitation variance, while explicit
low-frequency conditioning can recover more (AB-02/03). The first study must
therefore adjudicate daily precipitation structure against a year-level state
rather than assume the latter is proved. The other absences above are
**Structural** until an observed-data campaign measures their magnitude and
downstream benefit. Storm descriptors are an exception: published evaluations
of earlier CLIGEN versions/configurations report duration and peak-intensity
deficiencies (AB-40–42 and AB-44), AB-43 documents a lower-cost hourly parameter-
fitting path, and the vendored faithful source incorporates Yu's corrections.
Those studies establish prior bias directions and calibration options, but
their magnitudes must be reproduced for the exact vendored 5.32.3
implementation and current target datasets before benefit is inferred.

Meyer's historical USDA description (AB-39) independently records CLIGEN's
single-point monthly-parameter design, sparse daily coupling, and QC evolution.
It is context only; the vendored 5.32.3 Fortran remains the faithful-mode
authority.

## 3. Feature frontier

No single reviewed system dominates every dimension. Modern generators are
modular combinations of a scale hierarchy, marginal distributions,
dependence model, scenario mechanism, and validation system.

| Feature | Strong precedents | What is now practical | CLIGEN position |
|---|---|---|---|
| Low-frequency/interannual variation | WeaGETS spectral correction (AB-09/10), Steinschneider–Brown wavelet-AR (AB-12), AWE-GEN annual AR (AB-22), `swxg` GMHMM (AB-18) | Explicit annual/monthly process conditioning daily generation | Output deficit measured; an explicit state is missing but not uniquely established as the cause |
| Precipitation tails and multi-day extremes | GWEX E-GPD + temporal/spatial dependence (AB-13), AWE-GEN/Bartlett–Lewis (AB-22/24/25) | Tail-aware margins plus dependence across aggregation scales | Limited monthly transform and one-day occurrence state |
| Cross-variable dependence | Richardson/Parlange–Katz (AB-01/04), AWE-GEN family with physically linked variables rather than directly fitted cross-correlations in its precursor (AB-21/22), Rglimclim (AB-16), MSTWeatherGen (AB-17) | Wet/dry-conditioned or joint latent/copula/GLM residual models | Sparse/hard-coded; radiation independent of wetness |
| Spell/weather-regime persistence | higher-order WeaGETS (AB-10), LARS series (AB-07), weather regimes (AB-29/30) | Higher-order, semi-Markov, HMM/regime, or block-resampled sequences | First-order two-state occurrence only |
| Parameter uncertainty | BayGEN (AB-15), Bayesian GAMLSS/SBI (AB-19) | Posterior parameter draws propagated into ensembles | Fixed point estimates |
| Subdaily storm process | AWE-GEN, hybrid Bartlett–Lewis, STORM v.2 (AB-21–26) | Minute/hourly intensity-duration-consistent rainfall, sometimes spatial | Scalar event descriptors only |
| Multisite/gridded coherence | GWEX, BayGEN, MSTWeatherGen, California WGEN (AB-13/15/17/30) | Spatially coherent daily fields and regional extremes | Single station |
| Controlled nonstationarity | Steinschneider regimes, California WGEN, SBI matching (AB-19/29–31) | Separate mean, variance, tail, thermodynamic, and dynamic changes | Fixed stationary monthly climate |
| Global automated parameterization | Published CLIGEN station/gridded parameter products (AB-45–48), EGGS-WG (AB-20) | Observation/reanalysis-derived parameters with lower operator burden | Regional databases plus published global and continental parameter products; coverage is expanded, but weather trajectories are not spatially coherent |
| Generative spatial downscaling | CorrDiff, spateGAN, consistency models (AB-36–38) | Ensembles conditioned on coarse trajectories | No external high-resolution forcing contract yet |

Two findings should temper “SOTA” claims:

- Recent systems still report important failures. EGGS-WG reports problems at
  the most extreme precipitation values; MSTWeatherGen overstates some
  precipitation–radiation/temperature correlations; CorrDiff lacks guaranteed
  small-scale temporal coherence; the 2026 SBI generator reports weak upper
  precipitation tails. Newness is not evidence of universal superiority.
- Data and calibration burden are part of model quality. AWE-GEN-2d or a
  regional latent-Gaussian field may be scientifically attractive but cannot
  be identified from a legacy station `.par` file.

## 4. Ranked gaps for the `cligen-rs` portfolio

The ranking combines expected WEPP value, evidence, feasibility, and
prerequisite risk. It ranks what should be investigated next, not abstract
scientific sophistication. For a project focused exclusively on rare
storm-scale erosion, ranks 2–4 could reasonably move ahead of general daily
meteorology after their data prerequisites exist.

### Enabling priority 0 — modern schema, provenance, fitting, and typed I/O

This is not a climate-model improvement, but it is the prerequisite for every
declared extension.

- **Evidence:** **Structural.** The legacy `.par` is fixed-column and f32; its
  fields cannot distinguish observed targets, fitted latent parameters,
  covariance, source periods, or estimator lineage. `RunOutput` is primarily
  rendered text rather than a reusable typed row stream.
- **Feasibility:** high; moderate architectural work.
- **Required work:** `StationModel` discriminant; lossless
  `.par -> FixedMonthly5323` conversion; unit-explicit modern schema;
  provenance object; typed row sink feeding `.cli` and Parquet renderers;
  external fitting artifact contract; fail-closed model/profile validation.
  The active `.cli` quality path must still parse the rendered bytes so it
  prices formatting quantization and remains equivalent to post-hoc/Fortran
  measurement; a Parquet-native quality path requires a versioned spec change.
- **Critical rule:** schema version, station-model variant, and generation
  profile are separate axes. Faithful mode must reject rather than ignore
  annual-state fields.

### Rank 1 — low-frequency/interannual deficit and explicit climate state

- **Evidence:** **Measured + Published.** Repository underdispersion agrees
  with the long-standing overdispersion literature (AB-02/03/09). That
  literature identifies both daily precipitation structure and low-frequency
  conditioning as remedies; several current architectures implement the
  latter (AB-12/18/22/24).
- **WEPP value:** very high. Drought/pluvial sequencing affects vegetation,
  runoff, soil state, and erosion across months and years.
- **Feasibility:** high for a rank-one diagnostic; moderate for fitted
  multi-coefficient or hidden-state models.
- **Required work:** expand metrics; build hash-pinned observed targets;
  compare declared candidate models plus a daily precipitation-structure
  counterfactual; add profile-owned `YearClimateState`; use a dedicated
  domain-separated RNG; adjudicate across stations, burns, and 30/100-year
  horizons.
- **Main risk:** observed monthly/annual SD is an output target, not the latent
  anomaly SD to add. Baseline daily variation and QC already contribute to the
  target variance.

### Rank 2 — tail-aware and temporally clustered precipitation extremes

- **Evidence:** **Structural + Published.** CLIGEN lacks explicit tail and
  amount-memory components. GWEX shows that omitting temporal dependence can
  underestimate 3-day extremes even when daily extremes are adequate (AB-13).
- **WEPP value:** very high because runoff and detachment respond nonlinearly
  to intense and multi-day rainfall.
- **Feasibility:** moderate for a point daily E-GPD/mixture plus amount-state
  model; moderate–high when coupled to occurrence and storm descriptors.
- **Required work:** seasonal tail/threshold fitting; uncertainty estimates;
  wet-day amount autocorrelation; 1/3/5-day return levels; explicit decision
  whether annual anomalies alter occurrence, amount, or both; downstream
  runoff/erosion tests.
- **Main risk:** improving one marginal tail can damage monthly totals, wet-day
  fractions, spell behavior, and depth–duration–time-to-peak–peak-ratio
  dependence.
- **Coordination:** investigate daily tails, amount memory, and rank-6
  occurrence/spell persistence in one precipitation-structure study. Do not
  promote independently fitted components that have not been evaluated
  jointly.

### Rank 3 — fitted cross-variable and compound-event dependence

- **Evidence:** **Structural.** Faithful radiation is independent of
  precipitation, wind is not joint with storm state, and temperature/dew point
  use fixed algebra rather than fitted covariance. The actual magnitude of the
  deficit still needs observed measurement.
- **WEPP value:** high for evapotranspiration, snow/rain context, vegetation,
  drying, and compound hot/dry or wet/low-radiation periods.
- **Feasibility:** high for a wet/dry-conditioned radiation pilot; moderate–high
  for a joint discrete/continuous copula, GLM, or latent residual system.
- **Required work:** broaden group C to precipitation–temperature/dew/radiation/
  wind conditional statistics; add a profile-specific daily context after
  occurrence is resolved; preserve dew-point and Tmax/Tmin physical
  constraints.
- **Main risk:** a simple correlation target is insufficient for mixed
  zero-inflated precipitation, heteroscedasticity, and tail dependence.

### Rank 4 — a true subdaily precipitation process

- **Evidence:** **Structural + Published.** CLIGEN emits daily depth plus three
  event descriptors, not one or more continuous intra-day hyetographs.
  CLIGEN-specific evaluations report duration, intensity, and descriptor-
  dependence deficiencies for earlier versions/configurations (AB-40–42 and
  AB-44),
  while AB-43 supplies hourly-data fitting evidence; exact vendored 5.32.3
  behavior still requires repository measurement. AB-28 identifies short-
  duration maximum intensity as an important erosion driver, while AB-24–27
  provide subdaily process and hazard-model precedents.
- **WEPP value:** very high for event runoff and detachment through WEPP's
  descriptor-derived hyetograph. EI30 and R-factor are erosivity-validation
  metrics and inputs to RUSLE-type consumers, not direct WEPP inputs.
- **Feasibility:** moderate for a fitted point-process runtime with external
  calibration; low-to-moderate for a complete native spatial storm engine.
- **Required work:** begin with a lower-cost descriptor-level replication
  against breakpoint or 15-minute observations: daily depth, duration,
  time-to-peak fraction, peak-intensity ratio, and their joint dependence.
  Use that result to distinguish descriptor recalibration from the larger
  true-hyetograph project. Then specify a timestamped subdaily output/forcing
  contract, high-resolution gauge/radar corpus, multi-scale calibration, event
  segmentation, Bartlett–Lewis/STORM/AWE-GEN benchmark, aggregation/mass-
  conservation rules, and WEPP consumer decision on hyetographs versus
  derived descriptors.
- **Main risk:** daily station data cannot identify a subdaily model. A
  plausible-looking hyetograph without source and fitting lineage is not an
  improvement.
- **Coordination:** the subdaily process must either consume the daily/monthly
  precipitation model as its conditioning hierarchy or supersede it while
  reproducing the coarser targets. It must not become a second incompatible
  production precipitation profile by accident.

### Rank 5 — controlled nonstationarity and scenario-neutral forcing

- **Evidence:** **Structural + Published.** All CLIGEN station parameters
  repeat annually. Modern systems separate thermodynamic distribution changes,
  dynamic regime changes, and scenario targets (AB-19/29–31).
- **WEPP value:** high for climate-change sensitivity and stress testing.
- **Feasibility:** high for provenance-stamped monthly parameter trajectories;
  moderate for coherent distributional changes; very low (very high
  complexity) for circulation regimes.
- **Required work:** define `SimulationForcing`; distinguish preprocessing
  mutation from runtime trajectories; record baseline period/model/member;
  validate constraints and extrapolation; add trend/rolling-climatology
  metrics.
- **Main risk:** a delta to monthly means does not specify changes in
  occurrence, variance, tails, persistence, or storm intensity.

### Rank 6 — flexible spell persistence and weather states

- **Evidence:** **Structural + Published.** The first-order occurrence chain
  has only one-day state. Higher-order, semi-Markov, HMM, and regime systems
  can represent longer persistence (AB-07/10/29).
- **WEPP value:** medium–high for drought, antecedent moisture, vegetation, and
  clusters of erosive days.
- **Feasibility:** moderate; integration touches occurrence, amount masks,
  monthly totals, and storm generation.
- **Required work:** full seasonal spell distributions including year
  boundaries; transition-order/HMM comparison; a profile-owned `PrecipState`;
  new station-model variant if legacy probabilities are insufficient.
- **Main risk:** longer spells can improve persistence while biasing wet-day
  fraction and amount totals unless fitted jointly.
- **Coordination:** this is the occurrence-state leg of the rank-2
  precipitation-structure study, not an independent promotion track.

### Rank 7 — fitted-parameter and structural uncertainty

- **Evidence:** **Structural + Published.** CLIGEN draws weather from one
  fixed parameter set. BayGEN and the SBI generator propagate posterior
  uncertainty (AB-15/19).
- **WEPP value:** medium–high for honest risk intervals, especially with short
  station records and tail fits.
- **Feasibility:** moderate if fitting stays external and runtime consumes
  explicit ensemble members; high complexity for in-crate Bayesian inference.
- **Required work:** separate realization seed from fit/member identity;
  parameter posterior/ensemble schema; provenance hashes; decompose weather,
  parameter, scenario, and structural uncertainty.
- **Main risk:** mixing parameter uncertainty into the ordinary RNG without an
  explicit ensemble identity makes results irreproducible and uninterpretable.

### Rank 8 — multisite/spatial coherence

- **Evidence:** **Structural + Published.** The entire CLIGEN state is one
  station. Current systems can reproduce spatial occurrence, dependence, and
  regional extremes (AB-13/15/17/29–32).
- **WEPP value:** contextual: very high for coherent watershed/regional
  ensembles, lower for independent hillslope runs.
- **Feasibility:** low-to-moderate; a major project.
- **Required work:** concrete WEPPcloud use case/scale; station network or
  gridded corpus; shared regional state and domain-separated site RNG;
  covariance/PSD validation; site/member-aware output; spatial quality groups.
- **Main risk:** independent point simulations cannot be made spatially
  coherent post hoc without altering event and areal extremes.

### Integration watchlist — global fitting and generative ML

Global reanalysis fitting (EGGS-WG) and generative downscaling (AB-20/36–38)
can eventually expand coverage and subdaily forcing. The feasible near-term
work is an external-producer contract carrying timestamps, variables, units,
grid/site identity, model and weights hashes, ensemble member, and exact
aggregation semantics. It must support complete supplied meteorology and
optional subdaily precipitation through an explicit bypass/derivation layer;
the legacy observed seam substitutes only precipitation and Tmax/Tmin and
would discard the producer's multivariate coherence. Porting GPU networks or
a global atmosphere model into Rust would add a separate platform with little
benefit to CLIGEN's station generator.

Published global and continental CLIGEN parameter datasets (AB-45–48)
demonstrate that external fitting and localization are already feasible at
large scale. They expand geographic coverage but do not resolve the ranked
stochastic-structure gaps or produce spatially coherent trajectories.

## 5. The first interannual candidate study

The modern station schema should record canonical observed targets separately
from fitted model parameters. For each variable and calendar month, target
metadata must name the aggregation: for example,
`interannual_sd_monthly_total` for precipitation and
`interannual_sd_monthly_mean` for temperature. Legacy daily SD fields must not
be reused.

At minimum, compare these candidates:

| Candidate | State and parameters | Strength | Diagnostic limitation |
|---|---|---|---|
| Monthly-SD baseline | 12 monthly loadings per variable plus a declared cross-month/cross-variable covariance approximation | Auditable and easy to fit | Independent draws are jagged; one annual draw is rank-one; marginal SD alone is incomplete |
| Low-rank Fourier/EOF | A small coefficient vector, 12-month loadings, coefficient covariance, constraints, and fit error | Smooth seasonal anomalies; compact | Coefficients alone add no randomness; raw harmonic SD reconstruction can be negative |
| Vector AR(1) | Annual/seasonal coefficient vector plus transition matrix and innovation covariance | Adds year-to-year persistence; close to AWE-GEN concept | Short records weakly identify persistence/covariance; AWE-GEN also needs rejection/rescaling to enforce annual rainfall targets |
| Gaussian-mixture HMM | Climate-state transition matrix plus state means/covariances | Represents dry/wet/pluvial regimes; close to `swxg` | More parameters, label/fit uncertainty, and state-count selection |
| Spectral random-phase correction | Empirical monthly/yearly spectrum, phase randomization, and iterative daily post-adjustment | Direct WeaGETS benchmark for variance/autocorrelation | Requires full-spectrum/record-length semantics, leaves occurrence unchanged, and can damage cross-variable dependence |
| Daily precipitation-structure counterfactual | Higher-order occurrence plus declared amount classes/autocorrelation, without an annual state | Tests whether daily misspecification explains aggregate variance before adding a latent process | Does not address cross-variable annual anomalies or persistent external climate predictors |

A useful first runtime diagnostic is a rank-one seasonal annual latent:

1. draw a correlated `(z_precip, z_tmax, z_tmin)` vector once per year;
2. map it through 12 fitted seasonal loadings;
3. apply additive temperature anomalies and mean-one positive precipitation
   factors at a declared occurrence/amount seam;
4. use a dedicated RNG with a fixed draw budget per year;
5. draw the same state in observed mode regardless of missingness and apply it
   only to generated fields;
6. explicitly rule whether dew point receives a joint anomaly and whether
   storm parameters are recomputed.

This is a low-cost falsifiable model, not a promotion recommendation. Its
rank-one cross-month covariance should be reported as a limitation and tested
against the richer candidates.

## 6. Architecture and implementation seams

New profiles should compose around, not accumulate branches inside, the
faithful port:

```text
station source
  -> versioned StationModel
  -> selected GenerationProfile engine
       -> run/year state provider
       -> precipitation state/model
       -> daily multivariate context/model
       -> event model
  -> typed DailyRow / optional subdaily stream
       -> legacy .cli renderer
            -> active quality report parses rendered .cli bytes
       -> parquet/netcdf adapter
            -> future versioned native-quality surface, if specified
```

Concrete seams already present in the Rust port:

- place `StationModel::{FixedMonthly5323, ...}` after `ParFile` parsing and
  before the faithful station-parameter state;
- draw profile-owned `YearClimateState` at the year boundary in
  `modes::run_to_cli`, without cumulatively mutating faithful monthly arrays;
- use a separate extension RNG owner; never consume faithful `k1`–`k10`;
- replace first-order occurrence only through a profile-owned `PrecipState`,
  because occurrence, refill masks, amount availability, and storm output are
  coupled;
- expose wetness/regime context to profile-specific temperature/dew/radiation/
  wind components after precipitation occurrence is known;
- retain typed rows so renderers do not regenerate the climate trajectory;
  preserve the active quality report's deliberate parse of rendered `.cli`
  bytes, and specify any Parquet-native metrics separately;
- keep faithful `GenState`, `clgen`, `ranset`, `windg`, and storm routines as
  the executable legacy specification.

The crosswalk below makes those seams testable rather than treating them as
an architectural sketch. Links identify the present source or gate that a
future package must preserve or deliberately extend.

| Gap | Primary Rust seam | Existing compatibility and quality gates |
|---|---|---|
| Priority 0 schema and I/O | [`par::ParFile`](../../crates/cligen/src/par/mod.rs), [`modes::DailyRow`](../../crates/cligen/src/modes.rs) | [`par_state_identity`](../../crates/cligen/tests/par_state_identity.rs), [`cli_parity`](../../crates/cligen/tests/cli_parity.rs), quality group A |
| Rank 1 interannual state | Year loop in [`modes::run_to_cli`](../../crates/cligen/src/modes.rs), a new `GenerationProfile` | `.cli` parity, quality groups A/B/C/D plus the new low-frequency metrics |
| Ranks 2 and 6 precipitation structure | Private faithful code locations [`daily::gen_precip`](../../crates/cligen/src/daily.rs) and [`rng::draw_ranset_value`](../../crates/cligen/src/rng.rs); a future profile needs an explicit precipitation seam and separate extension RNG rather than cross-module calls to these internals | [`daily_identity`](../../crates/cligen/tests/daily_identity.rs), RNG tap identity, quality groups A/B/D |
| Rank 3 multivariate dependence | Temperature/dew-point stages, private [`daily::gen_radiation`](../../crates/cligen/src/daily.rs), and `windg`; a future profile needs an explicit daily-context seam | `daily_identity`, quality group C |
| Rank 4 subdaily events | [`storm::storm_block`](../../crates/cligen/src/storm.rs), `DailyRow`, and a new subdaily sink | [`storm_identity`](../../crates/cligen/tests/storm_identity.rs), quality groups C/D plus new intensity and erosion gates |
| Rank 5 nonstationarity | `GenerationProfile` and `modes::run_to_cli` | [`runspec_cli`](../../crates/cligen/tests/runspec_cli.rs), `cli_parity`, quality groups A/B plus trend diagnostics |
| Rank 7 fitted uncertainty | Extension RNG, profile, and output provenance | Deterministic quality runs, quality group P, and new fit/member identity gates |
| Rank 8 spatial coherence | New multisite state and output surface | No spatial gate exists; a package must specify one before implementation |
| Complete external forcing | Legacy [`observed::PrnReader`](../../crates/cligen/src/observed.rs) only for its current three variables; new full-meteorology bypass/derivation contract | [`modes_identity`](../../crates/cligen/tests/modes_identity.rs) plus new complete-forcing fixtures |

For single/design-storm modes, the first new profile should fail closed. The
deprecated WEPPcloud single-storm workflow can receive a later companion spec
if it remains necessary.

## 7. Data and calibration requirements

Every fitted extension needs a provenance-bearing fitting artifact, even if
the runtime implementation is compact.

Minimum metadata:

- source dataset and file/object hashes;
- station/grid identity, coordinates, elevation, units, timezone, and calendar;
- baseline period, completeness rules, wet-day threshold, and quality flags;
- detrending/nonstationarity treatment and raw versus detrended targets;
- aggregation, estimator, uncertainty interval, and held-out period/site;
- model family/version, constraints, optimizer/software version, fit seed, and
  diagnostics;
- reconstruction error for Fourier/EOF representations;
- covariance dimensions, ordering, positive-semidefinite checks, and any
  shrinkage/regularization.

Data scale grows sharply by feature:

| Feature | Minimum useful evidence |
|---|---|
| Interannual state | Prefer at least 30 complete years; longer records for spectral/AR/HMM identification; multiple independent observed products |
| Daily multivariate dependence | Complete overlapping precipitation/Tmax/Tmin/dew/radiation/wind records, seasonally stratified |
| Daily tails/persistence | Long wet-day records, declustered/threshold diagnostics, multi-day aggregates |
| Subdaily rainfall | High-resolution gauges and/or radar with event segmentation and instrument/QC lineage |
| Spatial generation | Stable network or gridded product with common calendar and covariance support |
| Future scenarios | Named model/member/baseline and separate thermodynamic/dynamic assumptions |

Reanalysis can extend coverage but is not observation truth, especially for
precipitation extremes. Station and reanalysis fits should remain separately
identified model variants.

## 8. Validation and promotion gates

The existing quality instrument is the correct authority pattern but must be
expanded before implementation.

For the annual-state study add:

- monthly precipitation-total mean, SD, and CV;
- monthly wet-day-count and wet-day-mean-amount interannual SD;
- interannual SD of monthly mean Tmax/Tmin;
- cross-month anomaly covariance or preregistered low-rank summaries;
- precipitation/Tmax/Tmin anomaly correlation and Tmax/Tmin correlation;
- lag-one annual persistence and low-frequency spectral diagnostics;
- monthly precipitation fraction on days with mean air temperature
  `(Tmax + Tmin) / 2 <= 0 °C`, explicitly labeled as a precipitation-phase
  proxy rather than a physical rain/snow partition;
- winter precipitation–temperature co-occurrence and a versioned air-
  temperature freeze–thaw proxy cycle count, with its threshold and transition
  rule declared;
- downstream WEPP snow accumulation/melt, rain-on-snow runoff, winter runoff,
  and soil-loss responses at preregistered snow-dominated sites;
- effects on daily range, dew point, spells, maxima, duration, and peak
  intensity through existing groups C/D.

For precipitation/event profiles later add:

- wet/dry spell distributions across year boundaries;
- wet-day amount autocorrelation and 1/3/5-day extremes;
- maximum 5/10/30/60-minute intensity, event depth and duration, time-to-peak-
  fraction distribution, peak-intensity ratio, antecedent dry time, EI30, and
  R-factor where data allow;
- depth–duration–time-to-peak–peak-ratio dependence and seasonal timing;
- spatial correlation/areal reduction for field models;
- WEPP runoff, peak runoff, soil loss, and their tail/return-level behavior.

For descriptor-only profiles, subdaily intensity and EI30 metrics must be
calculated through a named, versioned WEPP disaggregation implementation.
Native-subdaily profiles use their emitted series directly. Results derived
through different disaggregation rules are not interchangeable without
provenance.

Promotion should retain 30- and 100-year horizons, use multiple independent
burns with uncertainty intervals, and include held-out sites or periods.
Monthly climatology preservation is a gate, not assumed. Distance from faithful
output is compatibility information; scientific promotion follows the
observed-climate and WEPP-response quality vector under ADR-0002.
At snow-dominated sites, a candidate must not degrade the preregistered winter-
process vector beyond its uncertainty bounds without an explicitly accepted
tradeoff. Climate forcing proxies and downstream WEPP snow/frost responses
must remain distinct because CLIGEN does not output snowpack or soil state.

## 9. Recommended work-package sequence

The operator ratified this sequence on 2026-07-12. The canonical
[`ROADMAP`](../ROADMAP.md) records the dependency order and keeps the
station-file schema, station model, generation profile, and typed-output
schema as independent compatibility axes.

1. **Modern fixed-monthly station schema** — behaviorally inert, unit-explicit,
   provenance-bearing, exact legacy conversion, fail-closed variants.
2. **Typed output + provenance** — row stream, `.cli` preservation, Parquet,
   generation/model/fit/source identities.
3. **Quality metrics v3 + observed target corpus** — annual/monthly
   temperature variation, dependence, fuller spells/tails, multiple burns.
4. **Interannual candidate spike** — external fitting plus rank-one,
   Fourier/EOF, vector-AR, HMM, spectral benchmark outputs, and a narrowly
   scoped higher-order occurrence/amount-dependence counterfactual.
5. **Interannual profile adjudication** — promote only an evidence-supported
   versioned model; otherwise record a hold and retain findings.
6. **Daily precipitation structure study** — jointly compare occurrence/spell
   state, point E-GPD/mixture tails, amount persistence, and multi-day
   extremes; promote no component in isolation.
7. **Wet/dry-conditioned radiation pilot**, followed by a broader
   multivariate daily model only if the measured dependence gap warrants it.
8. **Subdaily external benchmark and full-forcing contract** — Bartlett–Lewis,
   STORM/AWE-GEN, high-resolution inputs, complete supplied meteorology,
   hierarchical coarse-target reconciliation, and WEPP metrics.
9. **Scenario forcing**, then **multisite/spatial generation**, as distinct
   later arcs with their own use cases and data.

## 10. Decision summary

- Proceed with file/schema modernization before model changes.
- In the first modern schema, represent current fixed monthly CLIGEN behavior
  exactly; do not add optional annual fields that faithful mode ignores.
- In the next model variant, keep canonical monthly observed targets distinct
  from fitted latent parameters.
- Do not choose between “SD” and “Fourier coefficients” until candidate models
  declare covariance, constraints, and year-to-year evolution and are measured.
- Use WeaGETS as the closest low-frequency benchmark, `swxg` as the strongest
  current annual-state/validation implementation reference, GWEX for daily
  extremes, and AWE-GEN/Bartlett–Lewis/STORM for the later subdaily arc.
- Treat a year-level climate state as a candidate explanation for the measured
  aggregate-variance deficit, not as an established cause; compare it with
  higher-order occurrence and amount-dependence alternatives.
- Keep ML climate systems outside the `cligen` crate. Define an auditable
  external forcing interface when a concrete use case arrives.
