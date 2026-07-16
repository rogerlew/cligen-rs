# A10 Neural Point-Weather Successor Feasibility Study Plan

Status: `PLANNING — INDEPENDENTLY REVIEWED`
Date: 2026-07-16
Study class: research-only stochastic climate-generator feasibility study
Expected execution record:
`docs/work-packages/YYYYMMDD-a10-neural-point-weather-successor/`
Production effect: none; `faithful_5_32_3` remains the default
Review: [independent review and disposition](a10-study-plan-review.md)

## Executive decision

A10 pivots from hand-designed parametric successor rescue to a compact neural
point-weather generator. The pivot is justified by the combined A7--A9 record:

- A7 measured daily precipitation-structure gaps, but its two analytic
  candidates did not cover the complete development surface.
- A8 showed that changing precipitation occurrence without jointly generating
  conditioned meteorology damages temperature, radiation, wind, storm, and
  monthly-budget behavior.
- A9 established a useful joint family and evaluation harness, but neither the
  renewal nor latent class passed the frozen selector. The stronger renewal
  finalist retained only three material degradations, all in hot-arid
  aggregate/extreme precipitation rows; the latent finalist retained 17.
- A9's final failure was not a shortage of storm events. The actual-frequency
  grouped storm estimators were finite, and storm descriptors improved. The
  earlier event-count hold and the A7 Death Valley boundary must not be carried
  forward as the explanation for A9d.

A10 will combine three ideas in one coherent study:

1. a neural stochastic state-space model supplies the new generator family;
2. station/regime conditioning and hierarchical shrinkage supply partial
   pooling across data-rich and data-poor climates; and
3. a prospectively declared applicability envelope allows a candidate to earn
   use in supported regimes while explicitly assigning `faithful_5_32_3` as
   the research fallback outside that envelope.

Operational feasibility is co-equal with climate quality. Candidate generation
must remain below 10× the faithful stochastic-generation runtime on the frozen
CPU benchmark. A ratio of 5× or greater is a warning that survives selection
and confirmation; a ratio of 10× or greater is a hard failure regardless of
climate score.

This is not a post-hoc relaxation of A9d. A10 receives a new model identity,
new hypotheses, a new candidate-blind selector, and a new development record.
The applicability rule, fallback semantics, corpus roles, and confirmation
firewall must be frozen before development output is accessed.

A10 is one substantive work package with internal gated milestones. Passing a
milestone authorizes the next ordinary stage of that package; it does not
create A10a/A10b/A10xyz administrative packages. A new operator decision is
needed only if execution would materially expand the scientific question,
license exposure, external cost, public interface, or production scope.

## 1. Why the campaign is pivoting

### 1.1 What has been learned

The faithful Rust port remains the exact compatibility baseline and source-
authority implementation. Under
[ADR-0002](../decisions/0002-quality-metrics-authority.md), however, observed-
climate quality rather than similarity to faithful output governs extensions.
Faithful behavior is a comparator and fallback, not the scientific target.

The campaign has already tested increasingly rich parametric structures:

- scalar and low-rank annual-state candidates;
- higher-order and semi-Markov precipitation occurrence;
- an integrated routed daily candidate;
- alternating-renewal and latent-regime joint occurrence/amount/event models;
- bounded Gaussian, lognormal, and logit-normal context laws; and
- hierarchical station/stratum/global fitting with a broad objective vector.

These experiments produced useful mechanisms and evidence, but repeated
manual additions created brittle interactions. Precipitation occurrence,
amounts, extremes, storm descriptors, temperatures, radiation, humidity, and
wind are not separable once a new daily trajectory is generated. A flexible
joint conditional model is now a simpler scientific experiment than another
sequence of hand-authored marginal repairs.

### 1.2 Correct interpretation of the final A9 evidence

The accepted
[A9d report](../reports/a9d-successor-development-confirmation-report.md)
records an 18/4/2 development funnel. Both classes fit, remained structurally
distinct, and produced complete retained-cell evidence. The renewal replay
candidate failed these three hot-arid rows:

| Family | Horizon | Candidate minus faithful | Frozen threshold |
|---|---:|---:|---:|
| Aggregate precipitation | 30 years | 0.793122 | 0.658426 |
| Aggregate precipitation | 100 years | 0.675787 | 0.392334 |
| Extreme precipitation | 100 years | 0.454491 | 0.403397 |

Storm descriptor and winter-proxy families counted as improved. The result is
therefore a bounded near miss, not proof that modern stochastic generation is
impossible, that hot-arid climates must always use faithful CLIGEN, or that
Bayesian storm pooling alone would solve the final defect.

The A9d selector also required zero material degradation across every retained
family/stratum/horizon row. That was a valid prospective A9 rule but is not the
only defensible promotion policy. It turned one maximum-row exceedance into a
whole-campaign rejection even though its 14 thresholds were not a single
campaign-wide error-rate guarantee. A10 will replace that rule prospectively
with regime-level applicability plus a small set of hard safety and climate-
quality guards.

### 1.3 Why neural generation is now feasible

The July 12
[state-of-the-art review](../lit-reviews/sota-climate-generator-gap-analysis.md)
kept global emulators and generative downscalers outside the immediate
`cligen` implementation because they were computationally and conceptually
misaligned with an arbitrary-length point generator. Priority access to the
I-CREWS GPU nodes changes the compute feasibility, but not that conceptual
boundary.

A10 will not port GenCast, CorrDiff, spateGAN, or a global atmosphere model
into Rust. Those systems require coarse trajectories, initial conditions, or
gridded boundary forcing. A10 instead tests a compact point-weather neural
state-space model trained externally in Python and evaluated through the
existing climate-quality harness. Rust integration is a later decision only
if a frozen candidate passes independent confirmation.

## 2. Study question, objectives, and non-objectives

### 2.1 Primary question

Can a compact, station-conditioned neural stochastic generator produce stable
arbitrary-length point weather that improves observed-climate quality over
both `faithful_5_32_3` and A9's renewal finalist across a prospectively
sufficient climate-regime envelope, while preserving explicit physical
support, reproducibility, fallback semantics, and acceptable generation
runtime?

### 2.2 Objectives

| ID | Objective |
|---|---|
| O1 | Build a leakage-safe, role-explicit regional corpus large enough for neural fitting while preserving the existing development and locked-confirmation firewalls. |
| O2 | Establish a pinned, restartable, offline GPU training environment on the I-CREWS `gpu-volatile` nodes. |
| O3 | Implement one compact neural state-space family with exact mixed discrete/continuous output support and stable long-horizon state evolution. |
| O4 | Test whether hierarchical partial pooling improves sparse-climate generalization relative to an otherwise identical complete-pooling, transferable-descriptor-only ablation. |
| O5 | Compare the neural family against faithful CLIGEN and `renewal-p010-q090` using 30- and 100-year nested streams and the existing climate-quality vocabulary. |
| O6 | Define and execute a prospective regime-level applicability rule with an explicit faithful fallback for unsupported fits. |
| O7 | Seal at most one complete model, weight set, preprocessing contract, and applicability policy before any locked confirmation target is read. |
| O8 | If and only if a candidate seals, execute one independent confirmation and return one final study terminal without feedback into training. |
| O9 | Demonstrate that candidate generation on a deployable CPU path remains below the prospective 10× faithful-runtime failure boundary, with 5× or greater treated as an explicit performance warning. |

### 2.3 Non-objectives

A10 does not:

- change faithful generator code or its byte-parity gates;
- create a production Rust generation profile;
- integrate with openWEPP or WEPPcloud;
- implement a global forecast model, gridded downscaler, or spatially coherent
  watershed generator;
- select a model from confirmation outcomes;
- infer climate regime or fallback from generated output;
- manufacture exact monthly totals through scaling, clipping, rejection, or
  repair;
- claim future-climate nonstationarity or climate-change scenario skill;
- treat the public repository license as relicensing Daymet, USCRN, gridMET,
  or any derived third-party data; or
- create intermediate A10 work packages merely to authorize ordinary study
  milestones.

A10 does require a research CPU-inference/export prototype and controlled
generation benchmark. This is feasibility evidence, not a production Rust
profile or authorization to integrate the model with a consumer.

## 3. Study objects and identities

Every object below must receive a stable identifier, canonical metadata, and a
SHA-256 content identity before it can enter a scored stage.

| Object ID | Object | Required identity |
|---|---|---|
| S01 | Study design | plan version, work-package dispatch, source commit, hypotheses, stage limits, resource bounds |
| S02 | Corpus manifest | source product/version, access date, role, station/grid identity, period, variables, units, calendar, transformations, notices, content hashes |
| S03 | Partition manifest | fit, internal validation, development, confirmation-metadata, and locked confirmation memberships plus spatial/temporal exclusion rules |
| S04 | Normalization contract | field definitions, missingness, day boundary, transformations, masks, scaling statistics, fit-only derivation rules |
| S05 | Model specification | architecture ID, parameter count, state semantics, output distributions, support transforms, conditioning inputs, reset/year-boundary behavior |
| S06 | Training recipe | optimizer, schedule, batch/window rules, loss terms and weights, early stopping, seed, mixed precision, distributed semantics |
| S07 | Environment receipt | operating system, Python, framework, CUDA, cuDNN, driver, compiler, dependency lock, container/environment hash |
| S08 | Checkpoint | model/optimizer/scheduler/scaler/RNG/data-cursor state, training step, parent checkpoint, exact weight hash |
| S09 | Candidate bundle | frozen model spec, preprocessing, weights, portable CPU-inference/export object, generation seed contract, fit corpus, software/environment, applicability policy |
| S10 | Generated stream | candidate/baseline identity, station, member/burn, start date, horizon, exact RNG/member identity, output hash |
| S11 | Evaluation | objective registry, thresholds, missingness policy, stream manifest, complete climate and runtime scores, selector trace, resources |
| S12 | Applicability map | separate station technical eligibility, regime climate applicability, and derived routing evidence; never a runtime classifier inferred from output |
| S13 | Confirmation seal | candidate bundle, target metadata/acquisition-request manifest, burns, evaluation rule, and atomic sealed-to-consumed transition with post-access target hashes |
| S14 | Public report | accepted result, claim-evidence ledger, review, manifests, limits, and final terminal |

The station-document schema, neural model ID, fit/checkpoint schema, generation
profile, and typed-output schema remain independent version axes.

## 4. Candidate family

### 4.1 Family identity

Working research identifier: `neural_point_weather_state_space_v0`.

The identifier is provisional until the work package freezes the model
specification. `v0` is research-only and must not appear as a public production
profile.

### 4.2 Architectural envelope

The first A10 candidate is a compact conditional neural state-space model, not
an unrestricted Transformer or image-style diffusion network.

Required components:

1. **Calendar/seasonal context**
   - civil date, day-of-year harmonic features, month, leap-day identity;
   - no implicit calendar conversion;
   - declared year-boundary behavior.
2. **Stable latent state**
   - a bounded recurrent, state-space, finite-regime, or hybrid transition;
   - optional annual/seasonal latent innovation with an explicit law;
   - no unbounded context window or hidden-state drift left untested;
   - exact reset, initialization, and stationary/warm-up semantics.
3. **Spatial/station conditioning**
   - continuous latitude, longitude, elevation, and climate descriptors;
   - a complete-pooling path using only transferable descriptors;
   - for the partial-pooling candidate, shared global/regime components and
     regularized fit-station deviations;
   - an explicit unseen-station rule that uses transferable descriptors and
     the prior/global-regime mean, never a missing station embedding;
   - no runtime lookup of a mutable training database.
4. **Precipitation occurrence**
   - explicit dry mass through a Bernoulli/categorical/hurdle head;
   - spell/regime persistence represented in latent state;
   - exact zero precipitation on dry days.
5. **Positive precipitation amount**
   - positive-support body distribution plus a tail-capable component, such as
     a monotone spline flow or body/tail mixture;
   - declared amount memory and dry-interval reset behavior;
   - no realized-month rescaling or fixed-count search.
6. **Daily meteorological context**
   - joint or conditionally coupled Tmax, Tmin, vapor pressure/RH, radiation,
     and wind heads;
   - precipitation state, amount quantile, season, latent state, and station
     context available to each declared consumer;
   - constraints such as Tmin <= Tmax represented structurally or through a
     transformed parameterization rather than output repair.
7. **Storm descriptors**
   - duration, time-to-peak fraction, and peak ratio conditional on positive
     precipitation, season, amount, and latent state;
   - correct positive/interior supports and explicit unavailable-data masks;
   - no claim of a true subdaily hyetograph.

The initial model should remain small enough for inference on one 48-GB L40
and for deterministic 100-year research generation without distributed
inference. The planning target is at most 50 million trainable parameters;
the work package must justify a larger model before training it. This
parameter cap is subordinate to the generation-runtime gate: a smaller model
that still reaches the 10× failure boundary is not operationally feasible.

### 4.3 Output distributions and support

The model specification must state every output's statistical support before
training. At minimum:

| Variable | Required support treatment |
|---|---|
| Precipitation | hurdle distribution: exact zero or finite positive amount |
| Tmax/Tmin | joint transformed representation that enforces Tmin <= Tmax |
| Vapor pressure or RH | positive vapor pressure or strictly interior bounded RH, consistent with declared field |
| Solar radiation | nonnegative/positive law with explicit night/day semantics |
| Wind speed | nonnegative law with calm-wind mass addressed explicitly |
| Wind direction | circular distribution or categorical direction conditional on positive/non-calm wind |
| Storm duration | finite positive support |
| Time-to-peak fraction | strict unit interval unless endpoint mass is explicitly modeled |
| Peak ratio | finite positive support with declared physical convention |

Clipping, NaN replacement, post-generation reordering, and monthly repair are
hard failures. Numerically stable transform implementations may bound internal
logits before evaluating an inverse transform only if that numerical policy is
specified and does not alter the declared distributional support.

### 4.4 Stochastic and reproducibility contract

Training reproducibility and generation reproducibility are different claims.

- Each training run records framework seeds, data order, distributed rank,
  deterministic-kernel settings, and every acknowledged nondeterministic
  operation.
- Architecture screening may use one registered training seed. Every finalist
  must be refit with at least three frozen training seeds to measure training
  instability before candidate selection.
- Generation uses a separately specified counter-based or stateless random-
  field contract. It must not depend on GPU batch size, worker count, training
  seed, or evaluation order.
- The same candidate/station/member identity must reproduce the same generated
  values in the frozen environment.
- A 30-year result is the exact prefix of the corresponding 100-year stream.
- The candidate bundle records weights and environment, not merely a model
  class name.

Bit identity across different GPU architectures is not assumed. Cross-device
reproducibility is measured and reported. Eventual Rust implementation would
require a separately specified numeric contract.

### 4.5 Generation-performance contract

Generation performance is a prospective feasibility criterion, not a later
runtime-implementation concern. A scientifically superior candidate cannot
seal if representative stochastic generation takes 10× or more of the
`faithful_5_32_3` elapsed time under the normative benchmark.

#### Normative comparison

The work package freezes a representative station manifest spanning all six
primary regimes before candidate timing. Each workload generates the same
date range and number of daily fields through both systems. The primary
workload is a 100-year single-station stochastic stream; a 30-year stream is
also measured to expose fixed-cost sensitivity. Both systems must complete
the same amount of generation work and materialize an equivalent in-memory
daily record. File serialization and metric evaluation occur outside the
warm-generation timer.

The normative candidate path is a portable CPU inference/export path suitable
for an eventual server or native-runtime integration. The comparison uses:

- the release faithful Rust generator and optimized candidate CPU runtime on
  the same physical host;
- one pinned physical CPU core and one computational thread per process;
- identical CPU affinity and declared thread-control environment;
- model loading, immutable station conditioning, and initial-state construction
  completed before the warm-generation timer, with no generation RNG advance,
  latent transition, requested-date inference, or requested-output
  materialization permitted before timing;
- at least two untimed warm-ups and nine alternating timed samples per
  station, horizon, and implementation;
- a prospectively frozen common repetition count or minimum timed duration,
  machine-quiescence acceptance rule, contamination rejection rule, and one
  deterministic rerun rule applied identically to candidate and faithful
  measurements;
- median elapsed monotonic wall time, with raw samples retained;
- validation that every timed stream is complete, finite, support-valid, and
  has the requested dates and row count; and
- host, CPU, governor/affinity, compiler, binary, model/export, dependency,
  and corpus provenance.

Let `R_gen` be the sum of candidate per-workload median warm-generation times
divided by the sum of the corresponding faithful medians. Let `R_regime` be
the same ratio within each primary regime. Classification uses the worse of
the 30- and 100-year aggregate ratios and the worst `R_regime`:

| Runtime ratio | Classification | Consequence |
|---:|---|---|
| `< 5.0×` | `PASS` | Candidate is within the accepted feasibility envelope. |
| `>= 5.0×` and `< 10.0×` | `WARN` | Candidate may continue, but the warning is prominent in selection, sealing, and the final terminal; runtime optimization is required before consumer integration. |
| `>= 10.0×` | `FAIL` | Candidate is operationally infeasible and cannot seal or access confirmation. |

Thus exactly 5× is a warning and exactly 10× is a failure. Ratios are computed
from unrounded times. A candidate also fails if its CPU export is unavailable,
cannot reproduce the registered stochastic stream under the frozen numeric
tolerance, requires a GPU for generation, or exceeds the benchmark resource
limit.

#### Cold-start and resource safeguards

A second single-station end-to-end benchmark measures process start, model
load, station conditioning, generation, and equivalent output serialization.
It uses the same 30/100-year manifest but is a separately reported deployment
diagnostic. The operator's exact 5× warning and 10× failure rule applies only
to warm stochastic generation. M3 may freeze absolute cold-start,
initialization, memory, and model-size safeguards before candidate timing; it
may not extend the faithful-relative ratio rule to cold start without a new
operator decision.

The benchmark also records peak RSS, export/weight bytes, initialization time,
and generated station-years per second. M3 freezes absolute memory and model-
size limits after measuring the target host, before candidate output. GPU
throughput, batched throughput, and multi-thread CPU throughput are useful
capacity diagnostics but cannot substitute for the normative single-core CPU
gate.

The accepted
[CLI runtime benchmark](../work-packages/20260710-cli-runtime-benchmark/package.md)
provides provenance and alternating-sample patterns, but its end-to-end
process matrix is not reused as a generator-throughput claim. A10 owns a new
equivalent-work benchmark and reports both absolute times and faithful-relative
ratios.

## 5. Baselines and ablations

The development comparison contains at least these four systems:

| ID | System | Purpose |
|---|---|---|
| B0 | `faithful_5_32_3` | compatibility baseline and research fallback |
| B1 | A9d `renewal-p010-q090` | strongest completed parametric successor comparator on inherited common A9 cells; not promoted or relabeled |
| N0 | Complete-pooling neural family | one shared model conditioned only on transferable spatial/climate descriptors; no station/tile identity, embedding, or station deviation |
| N1 | Hierarchical partial-pooling neural family | otherwise identical N0 architecture plus frozen regime hierarchy and regularized fit-station deviations; unseen stations use the declared prior/global-regime mean |

B1 is used only on source objects and scored cells covered by its accepted A9
identity. An expanded-panel renewal fit would be a new comparator with a new
fit/model identity and cannot inherit the B1 label. Missing B1 evidence is
unavailable, never favorable.

Optional ablations must answer a registered question. Permitted examples are:

- remove the annual/seasonal latent innovation;
- remove the storm head while retaining daily generation;
- replace the tail-capable amount head with a simple positive distribution; or
- remove fit-station deviations while retaining transferable location and
  climate descriptors.

The initial screen is capped at one architecture family and a bounded set of
width/depth/state/pooling configurations. Diffusion, GAN, Transformer-only,
and multiple unrelated neural families do not enter the first screen. They may
be proposed later only if the compact family fails with a specific diagnosed
limitation.

## 6. Applicability and faithful fallback

### 6.1 Purpose

A single maximum-row failure will no longer automatically reject improvement
in every climate. Conversely, an average improvement will not hide serious
local failure. A10 will adjudicate a candidate's applicability per frozen
climate regime and then apply a prospectively frozen breadth requirement.

Primary regimes remain:

- hot-arid;
- arid-boundary;
- monsoonal-transition;
- non-monsoonal semi-arid;
- humid; and
- cold.

Cross-tags such as cold-arid remain reporting attributes, not new mutable fit
groups.

### 6.2 Technical and climate dispositions

Station technical eligibility and regime climate applicability are separate
axes.

Every requested station receives exactly one pre-output technical disposition:

- `conditioning_eligible` — required inputs exist and the frozen candidate can
  initialize its declared unseen/known-station conditioning path;
- `fit_ineligible` — required source fields or fit exposure are absent;
- `fit_failed` — fitting, conditioning, export, or numerical validation
  failed; or
- `not_evaluated` — outside the frozen study surface.

Every primary regime receives exactly one development climate disposition:

- `neural_applicable` — the complete frozen regime rule passes at both
  horizons; or
- `faithful_fallback` — the regime does not earn neural applicability.

Station outcomes contribute to the prospectively frozen regime aggregate; they
cannot be used after output to exclude unfavorable stations from an otherwise
applicable regime. A station-level climate exception is prohibited unless its
rule was separately frozen before any development output. Technical
ineligibility/failure remains visible and cannot be relabeled as neural
applicability.

### 6.3 Routing semantics

- Routing is materialized in a signed/hash-bound artifact after development as
  the conjunction of pre-output station technical eligibility and frozen
  regime climate applicability.
- Runtime never infers regime from coordinates, annual precipitation, model
  confidence, generated output, or a failed coefficient calculation.
- A station routes to neural generation only when it is
  `conditioning_eligible` and its regime is `neural_applicable`.
- Every other requested station remains explicitly ineligible for neural
  routing. Where an exact faithful station artifact exists, the routed research
  composition invokes it and declares the technical or regime fallback reason
  in provenance; absence of such an artifact remains unavailable rather than
  inferred.
- A10 evaluates the routed research composition but does not ship it.
- Monsoonal climates are evaluated as a mandatory stratum; they do not receive
  a separate campaign unless evidence shows a distinct unresolved mechanism.

### 6.4 Applicability rule design

The exact rule must be frozen before development candidate output. It should
remain simpler than the accumulated A5/A9 selectors:

1. universal engineering invariants are hard gates;
2. each regime receives one candidate-blind standardized primary climate
   score at each horizon on paired common cells;
3. for candidate `C`, faithful B0, and renewal B1, M3 freezes the lower-is-
   better paired differences `D0 = score(C) - score(B0)` and
   `D1 = score(C) - score(B1)` plus strictly positive material-improvement
   thresholds `delta0 > 0` and `delta1 > 0`; a regime passes the primary rule
   only when `D0 <= -delta0` and `D1 <= -delta1` at both horizons;
4. a small registered set of precipitation aggregate/extreme, winter, and
   physical-context guards requires noninferiority to both baselines under
   candidate-blind margins and prevents catastrophic local degradation;
5. inherited B1 comparison uses only common A9 cells; expanded A10-only cells
   remain visible guards/reporting evidence and cannot compensate for missing
   or unfavorable paired B1 evidence;
6. a regime is applicable only if its complete primary and guard rules pass at
   both horizons without post-output station exclusions;
7. a frozen minimum regime/station breadth is required before any candidate
   can seal; and
8. unsupported regimes remain visible and route to the declared fallback when
   a faithful station artifact exists.

Candidate-blind bootstrap/null evidence must calibrate the primary score and
paired material-improvement thresholds, guard noninferiority margins, and
uncertainty rule. Missing evidence is never zero or favorable. The work package
may ratify exact weights, thresholds, margins, and breadth after corpus
inventory but before candidate output; it may not tune them from development
outcomes.

## 7. Corpus requirements

### 7.1 Source strategy

A10 needs a regional training corpus, not merely the A9 development panel.
The preferred source roles are:

| Source | Primary A10 role | Important boundary |
|---|---|---|
| Daymet V4 R1 | broad daily fit surface for precipitation, Tmax, Tmin, shortwave radiation, vapor pressure, day length, and seasonal/spatial conditioning | gridded estimate; 365 records/year with February 29 retained and leap-year December 31 omitted; no wind field; fit-source lineage is not independent of all station comparisons |
| USCRN | point daily/subhourly fit and evaluation for precipitation, temperature, RH, radiation, wind, and storm descriptors | shorter record, irregular field availability, local-standard-time semantics; confirmation stations remain locked |
| gridMET | optional wind/daily-sequencing auxiliary and sensitivity | not the canonical low-frequency precipitation/temperature truth; its monthly P/T signal is largely PRISM-constrained |
| PRISM AN daily | optional CONUS precipitation/temperature fit-source sensitivity | begins in 1981, licensing and product-update boundaries must be retained |
| Existing synthetic/adverse fixtures | support, calendar, missingness, sparse-climate, restart, and long-horizon failure tests | engineering evidence only, not climate validation |

The existing
[daily-source assessment](../work-packages/20260713-a5b-coefficient-source-assessment/artifacts/daily-source-assessment.md)
remains authoritative for its A5 low-frequency question: Daymet is primary,
PRISM is a sensitivity, and gridMET is not an independent monthly signal. A10
adds a new daily multivariate question, so gridMET may be considered for wind
and sequencing only under a distinct source identity.

### 7.2 Data roles and firewall

Every normalized object has exactly one role:

| Role | Permitted use |
|---|---|
| `candidate_fit` | gradient updates, fit-only normalization, station/regime representations |
| `fit_validation` | early stopping, bounded M5 configuration screening, ablation comparison, and training diagnostics; never final candidate comparison |
| `development` | M6 full finalist comparison and applicability adjudication only |
| `confirmation_metadata` | station identity, coordinates, stratum, availability planning; no target values |
| `confirmation_locked` | one-shot final evaluation only after candidate and confirmation seals |
| `source_sensitivity` | robustness reporting; cannot silently replace the primary target |
| `synthetic_fixture` | engineering and numerical tests only |

No object may change role after target access. Derived windows inherit the
role of their source object. Training statistics, embeddings, normalization,
imputation models, and learned tokenizers are fitted only from
`candidate_fit` objects.

### 7.3 Spatial and temporal partitioning

The corpus manifest must prevent easy spatial leakage from gridded products.

- Daymet locations are grouped into spatial tiles before role assignment.
  Adjacent pixels and near-duplicate climate surfaces cannot be split across
  fit and development/confirmation roles.
- The primary Daymet fit period remains 1980--2009 where available. Existing
  development targets remain 2010--2025 under their accepted calendar and
  source identities.
- The broad neural fit should sample many spatial tiles, not dense neighboring
  pixels that inflate row count without independent climate information.
- USCRN station roles are station-disjoint. Development and confirmation
  stations are excluded from USCRN gradient fitting even when earlier years
  exist, unless a prospectively specified fit-at-site/target-in-time design is
  separately justified.
- The existing 18-site confirmation roster remains metadata-only until the
  candidate seal. Its station-year targets are not used for normalization,
  architecture selection, early stopping, thresholds, or diagnostics.
- Source sensitivities use independently named partitions and cannot feed the
  primary optimizer after development access.

M1 must freeze a `calendar_transform_id` for every source before sharding.
Daymet's official calendar retains February 29 and omits December 31 in leap
years; it is not a generic 365-day no-leap calendar. The transform contract
must state:

- how February 29 and the absent leap-year December 31 are represented in
  training masks and civil-date features;
- which civil month owns every source record;
- whether any inherited A5 relabeling is used only as a separately identified
  sensitivity;
- how monthly and annual aggregations treat unavailable civil days; and
- how the fitted model produces complete Gregorian generation calendars
  without fabricating an observed Daymet value.

Silent post-February relabeling, silent observation fabrication, or mixing two
calendar transforms under one corpus identity is prohibited.

### 7.4 Coverage requirements

Milestone M1 must produce counts rather than assume sufficiency. The fit corpus
must demonstrate:

- all six primary regimes represented by multiple spatial tiles;
- Daymet coverage sufficient to separate tile, station, year, and window
  effects;
- all required variables have recorded availability and missingness by source,
  regime, month, and year;
- USCRN actual storm/event frequencies retained without arbitrary minimum
  floors or dropped zero-event seasons;
- the training loss can balance regimes and stations without treating dense
  gridded pixels as independent votes;
- enough held-out fit-validation tiles/stations exist to measure overfitting;
- the development and confirmation roles retain the accepted A9 identities;
  and
- every source has terms, citation, access date, download identity, and public-
  repository disposition.

The initial planning target for Daymet is at least 1,200 fit locations, with a
target of at least 200 spatially separated locations per primary regime where
the source supports that classification. These are corpus-design targets, not
claimed statistical minimum sample sizes. Failure to meet a target triggers a
documented redesign of sampling/weighting before training, not silent regime
dropping.

For USCRN, all eligible non-development/non-confirmation stations should be
inventoried and used according to actual field availability. No new 150/200-
event gate is introduced. The model and evaluation must expose uncertainty and
missingness at the observed event frequencies.

### 7.5 Required fields

The normalized daily record should provide, where sourced:

- date, declared calendar/day boundary, and `calendar_transform_id`;
- precipitation amount and measurement completeness;
- Tmax, Tmin, and any source temperature summaries;
- vapor pressure and/or relative humidity with derivation identity;
- solar radiation and day length;
- wind speed and direction;
- snow/winter proxy fields when available;
- storm duration, time-to-peak, peak ratio, antecedent dry time, and event
  source identity;
- latitude, longitude, elevation, source grid/station ID, climate stratum, and
  reporting cross-tags; and
- source quality flags and per-field availability masks.

No target field is inferred from a different product without a named derived-
field specification. Mixed-source daily vectors require explicit time-zone,
calendar, elevation, and aggregation reconciliation.

### 7.6 Corpus artifacts

Before GPU training, retain:

- source inventory and third-party notices;
- exact download/acquisition receipts;
- normalized schema and field glossary;
- canonical source/normalized manifests with hashes;
- spatial-tile and role-partition manifests;
- calendar-transform contract and transform sensitivity identities;
- variable/regime/month/year availability cube;
- leakage audit;
- training-shard index and per-shard hashes;
- fit-only normalization statistics;
- confirmation-metadata/acquisition-request seal and target-access state,
  without unread target-byte hashes; and
- an offline transfer manifest for the cluster.

Raw third-party data and routine training shards do not belong in Git. Small
manifests, schemas, and receipts are committed. Large approved public
artifacts use Git LFS only when their size and redistribution terms make the
repository appropriate; otherwise the repository stores an immutable external
object identity and retrieval procedure.

## 8. GPU cluster environment and operating requirements

### 8.1 Available hardware

The C3+3 documentation, checked 2026-07-16, lists the I-CREWS priority
`gpu-volatile` nodes:

| Node | GPUs | Host memory | CPU threads/cores |
|---|---:|---:|---:|
| `node03` | 2 × NVIDIA L40 | 512 GB | 64 |
| `node04` | 2 × NVIDIA L40 | 512 GB | 64 |

NVIDIA specifies 48 GB GDDR6 ECC memory per L40. Two GPUs on one node
therefore provide 96 GB aggregate device memory for distributed training, not
one unified 96-GB allocation. The published L40 interface is PCIe and does not
provide NVLink. The first A10 implementation should avoid cross-node training;
one- and two-GPU jobs on a single node are sufficient for the intended compact
model.

Sources:

- [C3+3 GPU-node instructions](https://docs.c3plus3.org/docs/workshops/Cluster/GPU_Nodes.html)
- [C3+3 Lemhi user guide](https://docs.c3plus3.org/docs/help/Getting_Started/)
- [NVIDIA L40 specifications](https://www.nvidia.com/en-in/data-center/l40/)
- [NVIDIA L40 datasheet](https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/support-guide/NVIDIA-L40-Datasheet-January-2023.pdf)

### 8.2 Operational constraints

- The partition is volatile. Jobs may be interrupted at any time, including
  for I-CREWS priority scheduling. Checkpointing is a correctness requirement,
  not an optimization.
- Compute nodes do not have internet access. Data, packages, model code,
  pretrained assets if any, and documentation must be staged before submission.
- Lemhi uses Slurm. Batch scripts and exact resource requests are committed.
- The documented user storage allowance is up to 25 TB on the Lustre file
  system. A10 must still impose a much smaller study-specific retention budget.
- GPU nodes have local drives. Shard staging and scratch cleanup behavior must
  be measured rather than assumed; `$SLURM_TMPDIR` availability is a readiness
  check.
- Account, allocation/QOS, partition access, wall-time policy, requeue support,
  and filesystem paths must be verified on the live system before production
  jobs.

### 8.3 Software environment

Preferred research stack: pinned Python plus PyTorch and CUDA, selected after
the live compatibility smoke test. The plan does not pin incidental current
versions before seeing the installed driver.

The environment must include:

- a lockfile or fully resolved package manifest;
- offline wheel/conda package cache or a verified Apptainer image if supported;
- recorded CUDA driver/runtime, cuDNN, NCCL, compiler, and GPU identities;
- deterministic-kernel configuration and a list of acknowledged exceptions;
- data, training, generation, and evaluation entry points that require no
  network access; and
- a fresh-environment reconstruction test.

The environment receipt hashes the lock/image, source tree, build commands,
package inventory, and smoke-test output. User credentials, tokens, SSH keys,
home-directory paths, and cluster account names never enter public artifacts.

### 8.4 Job classes

| Class | Intended resource | Purpose |
|---|---|---|
| CPU preparation | regular CPU partition or staging host | normalization, shard creation, manifest verification, lightweight metrics |
| GPU smoke | 1 L40, 8 CPUs, <= 64 GB host RAM, <= 2 hours | framework/device, data-loader, forward/backward, checkpoint and generation tests |
| Single-GPU screen | 1 L40, 8--16 CPUs, 64--128 GB host RAM | independent bounded configurations and ablations |
| Two-GPU training | 2 L40 on one node, 24--32 CPUs, <= 256 GB host RAM | finalist fits using data-parallel training |
| GPU evaluation | 1 L40 unless measured otherwise | deterministic long-stream generation and neural diagnostics; not the normative runtime gate |

The package records requested and measured GPU-hours, wall time, maximum host
RSS, peak device memory, data-loader throughput, samples/second, checkpoint
size/time, and restart overhead.

The normative generation-runtime benchmark runs separately on a documented
CPU host with one pinned physical core. Cluster GPU speed cannot make an
otherwise CPU-infeasible generator pass.

### 8.5 Checkpoint and interruption contract

Every resumable checkpoint contains:

- model weights;
- optimizer, scheduler, and mixed-precision scaler state;
- epoch/step and exact data-shard cursor;
- framework CPU/GPU RNG states and distributed sampler state;
- accumulated metric state required for exact continuation;
- parent checkpoint hash and training-recipe hash; and
- atomic completion marker written only after content verification.

Requirements:

- checkpoint at a fixed maximum interval of 15 minutes during screening and
  finalist training;
- also checkpoint at epoch, validation, and preemption-signal boundaries;
- write to a temporary path, fsync/verify as supported, then atomically publish;
- retain the latest two valid rolling checkpoints plus registered milestone
  checkpoints;
- resume only when code, environment, corpus, partition, and recipe identities
  match;
- fail closed on partial, corrupt, or incompatible checkpoints; and
- demonstrate one deliberate interruption/restart whose final weights and
  training trace match an uninterrupted control within the frozen
  reproducibility rule.

Whether Slurm automatic requeue is available must be verified. If it is not,
the runbook must support deterministic manual resubmission from the latest
valid checkpoint.

### 8.6 Data staging

1. Build and hash normalized shards off the compute node.
2. Copy the immutable shard set and environment assets to Lustre.
3. Verify every shard against the transfer manifest.
4. At job start, optionally stage assigned shards to node-local storage.
5. Verify local copies before training.
6. Write checkpoints and compact metrics to durable Lustre paths, never only
   local scratch.
7. Remove local scratch at normal exit and leave a cleanup marker after
   interruption recovery.

Training code must tolerate a missing local cache by reading verified Lustre
objects. It must not redownload or regenerate a different shard inside a GPU
job.

### 8.7 Initial resource bound

The work package may ratify a smaller bound before training. Any expansion
beyond this planning envelope requires a recorded justification before the
additional jobs:

- environment/smoke/restart work: 20 GPU-hours;
- bounded single-seed architecture and ablation screen: 200 GPU-hours;
- three-seed finalist refits and development generation: 400 GPU-hours;
- conditional confirmation generation: 100 GPU-hours;
- contingency: 80 GPU-hours;
- total A10 ceiling: 800 L40 GPU-hours;
- retained durable study artifacts: 2 TB, excluding upstream source data that
  already has a managed project home; and
- retained Git content: manifests, source, compact analyses, and only approved
  final weights/checkpoints, using LFS where appropriate.

Intermediate checkpoints, caches, and redundant generated streams are deleted
after their hashes and required analyses are sealed. Scientific evidence
needed for replay is retained or reproducibly regenerable from an immutable
candidate bundle.

## 9. Training and development design

### 9.1 Training windows

The fit recipe must declare:

- training window length and overlap;
- state warm-up and loss-mask length;
- whether windows can cross year boundaries;
- station/tile sampling weights;
- missing-variable masks and loss normalization;
- tail/event oversampling, if any, and how it is corrected in the likelihood;
- distributed sharding and epoch definition; and
- validation cadence and early-stopping statistic.

Sampling must not allow dense Daymet pixels or wet climates to dominate solely
through row count. The preferred first design samples regimes, then spatial
tiles/stations, then valid windows, with recorded weights.

### 9.2 Loss design

The primary fit objective should be a proper likelihood or proper scoring
rule for the declared mixed output distributions. Auxiliary losses may target
longer-scale behavior, but they must be frozen and cannot directly force an
exact realized month.

Permitted auxiliary targets include:

- wet/dry spell survival;
- monthly expected precipitation mean and finite-window variance;
- adjacent-wet amount dependence;
- annual/seasonal aggregate dispersion;
- precipitation-conditioned temperature, humidity, radiation, and wind
  relations;
- storm descriptor dependence; and
- hidden-state stability/regularization.

Every loss term records units, normalization, weight, missingness rule, and
gradient contribution. The work package must demonstrate that an auxiliary
loss does not dominate through scale alone.

### 9.3 Bounded configuration search

Before development output, freeze:

- one architecture family;
- a bounded grid or optimizer budget over state dimension, width/depth,
  pooling strength, tail head, and loss weights;
- a maximum number of configurations entering the GPU screen;
- one screen training seed;
- internal validation promotion ordering;
- at most two configurations per pooling class entering full development; and
- at most one partial-pooling and one complete-pooling finalist entering
  all-burn replay.

Development data may select among frozen configurations but may not generate
new hyperparameter proposals. If all configurations fail for an engineering
reason, the package may correct the defect before scored output with a recorded
access boundary. Outcome-driven architecture rescue ends the study terminal.

### 9.4 Long-horizon stability

Teacher-forced validation is insufficient. Before climate scoring, each
candidate must generate unforced sequences that include:

- 1-year smoke trajectories;
- 30-year exact prefixes;
- 100-year full streams;
- adverse hot-arid structural-zero months;
- long dry and wet spells;
- leap years and year boundaries; and
- repeated initialization/warm-up checks.

Hard failures include NaN/Inf, invalid support, state explosion/collapse,
nonterminating sampling, date drift, non-nested prefixes, provenance mismatch,
or dependence on batch/evaluation order.

## 10. Evaluation and decision rules

### 10.1 Authority

The quality-metric vector remains the extension authority. Distance to
faithful output is reported as compatibility information and as a baseline-
relative climate comparison, never as a parity requirement for the neural
candidate.

### 10.2 Evaluation population

- horizons: 30 and 100 years;
- nested streams: each 30-year output is the exact prefix of its 100-year
  member;
- regimes: all six primary regimes;
- baselines: B0 everywhere supported and accepted B1 only on inherited common
  A9 cells; any expanded-panel renewal refit receives a new identity;
- candidates: bounded N0/N1 configurations;
- training-seed robustness: at least three refits for finalists;
- generation members/burns: frozen before scored output and sufficient to
  separate training instability from weather realization variability; and
- development stations/objects: inherited accepted A9 identities unless the
  pre-output corpus milestone records a justified expansion.

### 10.3 Climate-quality families

Retain, at minimum:

- occurrence and wet/dry spell structure;
- wet-amount mean, dispersion, dependence, and tail;
- monthly/seasonal/annual aggregates and low-frequency variation;
- 1/3/5-day extremes;
- storm duration, time-to-peak, peak ratio, and joint dependence;
- wet/dry/event-conditioned temperature, humidity, radiation, and wind;
- temperature range and cross-variable dependence;
- winter/rain-snow/freeze-thaw proxies supported by the observed fields;
- physical support and calendar/provenance invariants; and
- applicability/fallback coverage.

The accepted A9c4 92-cell surface is a minimum continuity surface, not a reason
to preserve every A9 exclusion indefinitely. M1 may add newly supported cells
before output. It cannot remove an available unfavorable cell after output.

### 10.4 Neural-specific diagnostics

Report:

- fit/validation likelihood or proper score by source, regime, variable, and
  period;
- calibration of predictive probabilities/quantiles;
- hidden-state occupancy, persistence, and collapse diagnostics;
- station/tile embedding norms and shrinkage contribution;
- complete-pooling versus partial-pooling generalization;
- train/validation/development gap;
- training-seed variance;
- long-run marginal/state stability;
- tail-event effective sample sizes and uncertainty;
- inference throughput, device memory, and CPU fallback feasibility; and
- sensitivity to source-product choice where registered.

These diagnostics do not replace climate-quality gates.

### 10.5 Generation-runtime evaluation

Execute the frozen Section 4.5 benchmark for every configuration promoted to
full development and repeat it for the exact candidate bundle before sealing.
The evaluation publishes:

- raw and median warm-generation times for both implementations;
- `R_gen` and every `R_regime` at 30 and 100 years;
- normative warm-generation `PASS`, `WARN`, or `FAIL` from unrounded ratios;
- separately labeled cold-start times/ratios and absolute-safeguard results,
  with no 5×/10× classification;
- timed duration/repetition counts, quiescence/contamination decisions,
  measurement dispersion, and any deterministic rerun trace;
- peak RSS, model/export size, initialization time, and station-years/second;
- CPU and GPU capacity diagnostics kept distinct from the normative result;
  and
- completeness/support checks for every timed output.

A normative warm-generation runtime `FAIL` is a hard candidate rejection. A
normative runtime `WARN` is not hidden by superior climate scores and remains
attached to any development or confirmation success terminal. Cold-start
diagnostics are adjudicated only by separately frozen absolute safeguards.

### 10.6 Candidate selection

The candidate-blind selector must be finalized at M3. Its required ordering is:

1. reject engineering invariant, provenance, or generation-runtime failures;
2. reject corpus/firewall violations;
3. reject candidates with incomplete required evidence;
4. assign per-regime applicability using both horizons, paired material
   improvement over B0 and B1 on common cells, and the frozen noninferiority
   guards;
5. reject candidates below the frozen applicability breadth;
6. order survivors by applicable-regime breadth, then primary climate score,
   then runtime class (`PASS` before `WARN`), training-seed stability, exact
   runtime ratio, model size, and stable configuration ID; and
7. select at most one exact candidate identity for M7 sealing.

Fallback cells remain in the published matrix. They are not scored as neural
improvements and cannot inflate the neural candidate's applicability score.
The routed composition is reported separately from the neural-only surface.

### 10.7 Confirmation firewall

Before confirmation target access, seal:

- exact candidate model/spec/weights/environment;
- fit and development corpus identities;
- station preprocessing and applicability map;
- confirmation roster and metadata/acquisition-request manifest (station IDs,
  period, source/version, expected fields, retrieval rule, and access
  procedure), without unread target-byte hashes;
- burns/members and horizons;
- evaluation code, objectives, thresholds, missingness, and final rule;
- target custodian and atomic access procedure; and
- terminal vocabulary.

If M6 selects no candidate, confirmation remains metadata-only and A10 closes
at its development hold. If M6 selects a candidate but M7 cannot seal it, A10
closes at `HOLD-A10-CONFIRMATION-SEAL` without target access. If M7 seals one
candidate, confirmation may be consumed once. A scientific failure is final
for that candidate; confirmation cannot tune weights, thresholds,
preprocessing, or applicability.

## 11. Hypothesis registry

Exact quantitative thresholds are frozen in the work package before relevant
output access. The planning hypotheses are:

| ID | Provenance | Hypothesis |
|---|---|---|
| H1 | prospective | The expanded corpus satisfies role, leakage, variable, regime, calendar, and source-identity gates without accessing locked confirmation targets. |
| H2 | prospective | The pinned GPU environment can train, checkpoint, interrupt, resume, and reproduce registered generation streams within the resource bound. |
| H3 | prospective | At least one neural configuration passes all hard engineering gates, remains below the 10× faithful generation-runtime failure boundary, and generates stable nested 30/100-year climates. |
| H4 | prospective | Hierarchical partial pooling improves held-out spatial generalization over the otherwise identical complete-pooling, transferable-descriptor-only ablation under the frozen comparison rule. |
| H5 | prospective | At least one candidate earns the frozen minimum applicability breadth and outperforms both faithful CLIGEN and the A9 renewal comparator under the registered regime-level climate rule. |
| H6 | prospective | The selector chooses at most one exact candidate identity for M7 sealing and publishes every unsupported/fallback regime. |
| H7 | prospective | Confirmation target data remain scientifically unread unless the candidate and confirmation seals are complete. |
| H8 | conditional prospective | If a candidate seals, the one-shot confirmation returns exactly one pass or final-failure terminal without feedback into training. |

Failure to support H4 does not automatically reject a neural candidate if the
complete-pooling version independently satisfies H5. It does reject the claim
that hierarchical partial pooling supplied the improvement.

## 12. Gated milestones

All milestones live inside the single A10 work package. Artifacts are retained
at each boundary so an interruption does not erase the scientific chronology.

### M0 — Dispatch and predecessor freeze

Entry:

- operator authorizes execution of the single A10 study package from a named
  commit/branch.

Work:

- freeze this plan, A7--A9 accepted authorities, source commit, study scope,
  data roles, initial hypotheses, resource ceiling, and confirmation firewall;
- confirm no production code change is in scope.

Artifacts:

- execution dispatch;
- predecessor manifest;
- planning/design freeze;
- initial risk and access register.

Gate:

- every predecessor hash and terminal verifies;
- no confirmation target series is loaded.

Failure terminal: `HOLD-A10-PREDECESSOR-INTEGRITY`.

### M1 — Corpus inventory, acquisition, normalization, and role freeze

Entry:

- M0 passes.

Work:

- inventory Daymet, USCRN, optional gridMET/PRISM, existing A9 objects, and
  fixtures;
- define spatial tiles and role partitions;
- acquire permitted fit data;
- normalize fields/calendars without reading confirmation targets;
- freeze and test each source's `calendar_transform_id`, including Daymet leap-
  year February 29/absent December 31 behavior and complete Gregorian
  generation semantics;
- build shards, manifests, notices, availability cube, and leakage audit;
- determine whether optional sources are scientifically and legally needed.

Artifacts:

- source and normalized manifests;
- partition/role freeze;
- normalized schema and glossary;
- calendar-transform contract and test vectors;
- coverage/availability analysis;
- leakage audit;
- training-shard and transfer manifests;
- third-party notices.

Gate:

- six-regime fit coverage is explicit;
- every required field has source/units/calendar/missingness;
- every source calendar transform is explicit, Gregorian generation is
  complete, and no missing Daymet civil day is fabricated as an observation;
- spatial and role leakage checks pass;
- actual event frequencies are preserved;
- locked confirmation remains metadata-only;
- every source is permitted for its intended retained/public use.

Failure terminal: `HOLD-A10-CORPUS` or `HOLD-A10-DATA-RIGHTS`.

### M2 — Cluster and restartability readiness

Entry:

- M0 passes; M1 may prepare in parallel, but production training shards must be
  frozen before M4.

Work:

- verify allocation/partition/QOS, driver, L40 identity, filesystem, local
  scratch, wall-time, signals, and requeue behavior;
- build the offline pinned environment;
- run one-GPU and two-GPU framework/collective smoke with a small synthetic
  environment harness;
- measure storage-level checkpoint write/read and execute a synthetic
  Slurm/signal forced-interruption restart drill; this proves environment,
  storage, and job-control behavior, not A10 model-state equivalence;
- reconstruct the environment from its lock/image.

Artifacts:

- cluster inventory receipt;
- environment lock/image manifest;
- Slurm scripts and runbook;
- smoke benchmarks;
- interruption/restart evidence;
- resource telemetry schema.

Gate:

- one- and two-GPU tests pass;
- offline reconstruction passes;
- the synthetic environment/storage harness survives an actual interruption;
- durable/local storage behavior is understood;
- no credential or operator-specific path appears in public artifacts.

Failure terminal: `HOLD-A10-COMPUTE-ENVIRONMENT`.

### M3 — Model, training, generation, and selector freeze

Entry:

- M1 coverage is known and M2 capability is known;
- no scored development output exists.

Work:

- finalize model architecture envelope and bounded configuration grid;
- freeze normalization, training recipe, RNG/member contract, checkpoint
  schema, long-horizon invariants, objective registry, thresholds,
  applicability rule, stage promotion, burns/members, generation-runtime
  benchmark/hosts/limits, and resources;
- freeze paired common-cell improvement estimands against B0/B1, strictly
  positive improvement thresholds, noninferiority guards, and B1 identity/
  availability rules;
- freeze benchmark repetition/minimum-duration logic, machine-quiescence and
  contamination rules, deterministic rerun behavior, warm initialization
  boundary, and separate absolute cold-start/resource safeguards;
- implement schemas/specifications for every new interface surface.

Artifacts:

- model and fit schemas;
- training/generation contract;
- generation-performance benchmark contract and representative workload
  manifest;
- candidate-blind calibration;
- paired-baseline and comparator-identity registry;
- objective/applicability registry;
- design freeze and test vectors.

Gate:

- all schemas fail closed;
- selector arithmetic and missingness behavior pass synthetic tests;
- paired B0/B1 differences, improvement thresholds, noninferiority guards, and
  missing-comparator behavior pass synthetic tests;
- exact configuration and resource bounds are finite;
- the runtime ratio arithmetic classifies exactly 5× as `WARN` and exactly
  10× as `FAIL`;
- confirmation rule is conditional and inaccessible.

Failure terminal: `HOLD-A10-DESIGN-INCOMPLETE`.

### M4 — Local and single-GPU implementation qualification

Entry:

- M1--M3 pass.

Work:

- implement data loaders, model, distributions, training, checkpoints,
  generation, CPU inference/export, provenance, runtime benchmark, and
  evaluators;
- train on small deterministic fixtures and a bounded real-data subset;
- exercise structural-zero months, missing fields, extremes, year boundaries,
  and support transforms;
- generate 1/30/100-year smoke streams;
- verify nested prefixes and batch/order-independent generation identity;
- execute an actual A10 model/optimizer/scheduler/scaler/RNG/sampler/data-
  cursor forced-interruption resume and compare it with the uninterrupted
  control under the frozen equivalence rule;
- run the normative CPU benchmark against faithful generation for the
  qualified architecture on the bounded real-data subset.

Artifacts:

- research source and tests;
- fixture checkpoints/streams;
- support and long-horizon audit;
- A10 interruption/resume equivalence receipt;
- preliminary CPU generation-performance receipt;
- qualification receipt.

Gate:

- unit/integration tests pass;
- all hard invariants pass;
- no clipping/repair path exists;
- authoritative A10 interruption/resume equivalence and generation identities
  pass;
- the CPU export exists and the preliminary normative ratio is below 10×;
- a 100-year stream completes within measured resource bounds.

Failure terminal: `HOLD-A10-IMPLEMENTATION` or
`HOLD-A10-LONG-HORIZON-STABILITY` or `HOLD-A10-GENERATION-RUNTIME`.

### M5 — Bounded GPU architecture and pooling screen

Entry:

- M4 passes;
- configuration grid, screen seed, internal validation, and promotion rule are
  frozen.

Work:

- train every registered N0/N1 configuration once;
- record every attempt, checkpoint, failure, and resource trace;
- compare fit-validation proper scores, support, stability, training
  diagnostics, and complete-/partial-pooling generalization;
- benchmark generation runtime for every configuration eligible for
  promotion;
- promote only under the frozen rule.

Artifacts:

- immutable fit/checkpoint manifests;
- complete screen results;
- pooling ablation;
- configuration-level generation-performance matrix;
- resource and failure inventory;
- promotion trace.

Gate:

- at least one valid configuration remains;
- at least one promotable configuration is below the 10× runtime failure
  boundary, with any 5× warning retained;
- no role/firewall violation;
- training and generation remain within resource limits;
- promotion uses `fit_validation`, not development outcomes.

Failure terminal: `HOLD-A10-NO-VALID-NEURAL-FIT`,
`HOLD-A10-GENERATION-RUNTIME`, or `HOLD-A10-RESOURCE-BOUND`.

### M6 — Full development and applicability adjudication

Entry:

- M5 promotes bounded configurations;
- development corpus and burns are still unchanged.

Work:

- refit/promote finalists using the frozen seed rule;
- generate nested 30/100-year streams for B0, B1, N0, and N1;
- execute complete engineering, climate, neural-diagnostic, and resource
  evaluation;
- execute the final normative CPU generation benchmark for every finalist;
- assign per-regime applicability and explicit fallback;
- replay finalists over all registered members;
- publish every retained, unavailable, and fallback cell.

Artifacts:

- baseline/candidate stream manifests;
- complete evaluation;
- final generation-performance receipt;
- applicability map;
- Pareto/selector trace;
- training-seed stability analysis;
- development decision.

Gate:

- zero or more candidates may meet hard gates, minimum applicability breadth,
  the paired-both-baselines climate rule, stability rule, and the below-10×
  generation-runtime rule;
- if multiple candidates qualify, the frozen deterministic ordering selects
  exactly one and all survivor results remain published;
- a 5× or greater runtime warning remains explicit and influences ordering;
- unsupported regimes remain explicit;
- no confirmation target has been read.

Development terminals:

- `CANDIDATE-SELECTED-READY-A10-SEAL`; or
- `HOLD-A10-NO-APPLICABLE-CANDIDATE`.

The latter closes the scientific study at development. It does not trigger an
automatic rescue or another A10-suffixed package.

### M7 — Candidate and confirmation seal

Entry:

- M6 selects exactly one candidate under the frozen ordering.

Work:

- freeze the exact candidate bundle, station conditioning/preprocessing,
  CPU inference/export and runtime receipt, applicability map, fallback
  policy, environment, confirmation roster, metadata/acquisition-request
  manifest, members, objectives, thresholds, final rule, and access procedure;
- verify that no target value influenced any frozen object.

Artifacts:

- candidate freeze;
- confirmation seal;
- access-state manifest;
- independent firewall verification.

Gate:

- all candidate and confirmation-metadata/acquisition identities complete and
  immutable; unread target-byte hashes are neither required nor claimed;
- exactly one candidate;
- target remains sealed/unread;
- candidate weights can be reconstructed and generated.

M7 terminals:

- `CANDIDATE-SEALED-READY-A10-CONFIRMATION`; or
- `HOLD-A10-CONFIRMATION-SEAL`.

### M8 — One-shot confirmation

Entry:

- M7 passes.

Work:

- atomically transition target state from `sealed` to `access_in_progress`
  before opening target bytes; transition to `consumed` as soon as any target
  data byte is read, even if later acquisition, hash, parsing, or execution
  checks fail;
- acquire/verify the exact target objects against the sealed metadata/request
  and record their content hashes in the consumed-target manifest;
- generate the frozen confirmation streams;
- run the frozen final rule once;
- prohibit any feedback into training or applicability.

Artifacts:

- consumed-target manifest;
- target-access state and operational-attempt receipt;
- confirmation streams/identities;
- complete confirmation evaluation;
- final decision.

Final scientific terminals:

- `CONFIRMATION-PASS-READY-A10-PRODUCTION-IMPLEMENTATION-STUDY`; or
- `CONFIRMATION-FAIL-A10-FINAL`.

An acquisition, identity, environment, or execution failure before a valid
scientific score returns `HOLD-A10-CONFIRMATION-EXECUTION`, not a scientific
failure. An `access_in_progress` attempt may roll back to `sealed` only when a
verifier proves that no target data byte was opened; if any byte was read or
access is uncertain, the terminal state is conservatively `consumed`. Its
receipt records the proof and terminal access state; no terminal may leave
`access_in_progress` unresolved. The hold authorizes neither tuning nor an
automatic retry. No terminal changes production by itself.

### M9 — Report, review, cleanup, and handoff

Entry:

- any terminal hold from M0--M8 or an M8 final scientific decision exists.

Work:

- author the public scientific report under the repository report standard;
- conduct independent accuracy, scientific-validity, and consistency/public-
  safety review;
- verify artifact/LFS/external-object identities for artifacts actually
  reached and record every unreached artifact class as `not_reached`;
- if M4 or later was reached, verify the applicable performance classification
  and reproduce the latest valid benchmark from its manifest; otherwise record
  performance evidence as `not_reached` rather than pass/unavailable;
- remove nonretained cluster caches/checkpoints;
- reconcile roadmap/catalog state;
- record the smallest evidence-supported next action without automatically
  creating another package.

Artifacts:

- accepted report and manifest;
- claim-evidence ledger;
- consolidated review;
- gate/resource/cleanup receipts;
- final package terminal and handoff.

Gate:

- zero open P1/P2 review findings;
- package/report verifiers pass;
- repository gates pass;
- source data and confirmation access reached by the study remain license-safe
  and auditable, with exact target-access state if M8 began;
- conditional evidence requirements agree with the highest completed
  milestone and use `not_reached` for later stages; and
- cluster cleanup, when cluster work occurred, preserves required replay
  evidence.

## 13. Repository and cluster layout

Expected repository layout:

```text
docs/planning/a10-study-plan.md
docs/work-packages/YYYYMMDD-a10-neural-point-weather-successor/
  package.md
  artifacts/
    design-*.json
    corpus-*.json
    environment-*.json
    fits/
    evaluations/
    review.md
    gate-results.md
docs/specifications/
  <new fit/model/generation schemas as required>
research/a10/
  corpus/
  model/
  training/
  generation/
  evaluation/
  cluster/
  tests/
```

Expected cluster project layout, with operator-specific roots supplied through
environment variables rather than committed paths:

```text
${A10_PROJECT}/
  env/
  source/
  data/source/
  data/normalized/
  data/shards/
  manifests/
  runs/<run-id>/
    config/
    checkpoints/
    metrics/
    logs/
    generated/
  retained/
  scratch-index/
```

Public receipts use logical object IDs and content hashes, not usernames or
absolute home paths.

## 14. Verification gates

Every A10 package closure runs the repository gates:

```text
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

Research-specific gates additionally include:

- Python formatting/lint/type/test commands pinned in the package;
- strict schema and duplicate/nonfinite JSON checks;
- corpus hash and role verification;
- leakage audit;
- environment reconstruction;
- one-/two-GPU smoke;
- checkpoint interruption/resume drill;
- deterministic generation replay;
- exact nested 30/100-year prefix;
- normative single-core CPU generation benchmark with exact 5× warning and
  10× failure boundary tests;
- physical support and calendar checks;
- complete attempt and resource inventory;
- candidate/confirmation firewall verifier;
- report verifier and independent review; and
- Git LFS pointer/object or external-object hash checks.

Coverage/CRAP gates apply if production functions under `crates/` are changed.
The intended A10 study changes no production Rust function, so those gates
should not be triggered during feasibility work.

## 15. Risks and controls

| Risk | Consequence | Control |
|---|---|---|
| Dense gridded-pixel leakage | inflated spatial generalization | spatial-tile partitions, buffer/near-duplicate audit, station-disjoint targets |
| Product imitation rather than climate truth | model learns Daymet/gridMET artifacts | retain product identity, USCRN point sensitivity, PRISM/gridMET as named sensitivities, bounded claims |
| Sparse extremes | smoothed or unstable tails | explicit tail head, actual-frequency evidence, uncertainty, extreme guards, no arbitrary favorable imputation |
| Neural mode/state collapse | unrealistic persistence or variance | state occupancy/persistence diagnostics, multiple training seeds, 100-year unforced tests |
| Autoregressive drift | long climates diverge from training support | bounded/stationary state design, explicit resets, 30/100-year stability gates |
| Cross-variable incoherence | repeats A8 context failures | joint conditional heads and wet/dry/event-conditioned evaluation |
| Mixed-source day/calendar mismatch | spurious dependence | explicit source-specific calendars/day boundaries and reconciliation spec |
| Pooling hides local failure | broad average masks a regime | per-regime applicability and published station/regime uncertainty |
| Fallback hides model gaps | routed composition looks better than neural model | report neural-only and routed results separately; fallback does not count as neural improvement |
| Development overfitting | selected model fails confirmation | bounded grid, internal fit validation, frozen development rule, locked one-shot confirmation |
| GPU nondeterminism | irreproducible weights/results | environment receipt, deterministic settings, multi-seed stability, exact generation RNG contract |
| Volatile-node interruption | lost progress or corrupted state | 15-minute atomic checkpoints, forced-restart gate, durable Lustre state |
| No compute-node internet | failed job/environment drift | offline environment and wheel/image cache, preflight completeness test |
| Storage growth | unmanageable evidence/cost | 2-TB retention cap, shard manifests, rolling checkpoints, cleanup receipt |
| Model too large or slow for deployment | research success cannot transfer | <=50M planning target, portable CPU export, single-core faithful-relative benchmark, 5× warning, 10× hard failure |
| GPU benchmark masks deployment cost | candidate appears fast only on scarce hardware | GPU throughput is diagnostic only; normative generation gate uses one pinned CPU core |
| Confirmation leakage | invalid final evidence | metadata-only roster, custodian seal, hash-chained one-shot transition |
| Premature Rust integration | hardens an unvalidated family | external Python research only until confirmation passes |

## 16. Success, hold, and handoff semantics

A10 is successful only if the evidence supports the claimed level:

- **Compute success** means the cluster workflow is reproducible and
  restartable; it says nothing about climate quality.
- **Fit success** means a neural model trains and generates valid streams; it
  says nothing about superiority.
- **Development success** means one candidate earns the frozen applicability
  breadth, climate rule, and below-10× runtime rule; it authorizes sealing,
  not production. A 5× or greater warning remains attached.
- **Confirmation success** means the frozen candidate passes independent
  confirmation; it authorizes a separately planned production-runtime
  implementation study, not immediate public-default change.

No climate-quality result overrides a runtime `FAIL`. A confirmation terminal
cannot be reached by a candidate at or above 10× faithful generation time.

A hold preserves the evidence and closes the study at the reached boundary.
It is not automatically followed by selector relaxation, new architectures,
or intermediate packages. The public report must distinguish:

- unsupported neural regimes;
- explicit faithful fallback;
- unavailable evidence;
- fit failure;
- development rejection; and
- confirmation failure.

## 17. Definition of ready for GPU production training

A10 is ready for its first bounded full-corpus GPU screen only when all items
below are true:

- M0 predecessor/design freeze passes;
- fit, validation, development, confirmation-metadata, and locked roles are
  immutable;
- normalized corpus and shard hashes verify;
- leakage and coverage audits pass;
- third-party use/retention/publication is documented;
- model, distributions, training recipe, configuration grid, resource bound,
  and selector are frozen;
- the representative performance workload, CPU host controls, ratio
  arithmetic, 5× warning, 10× failure, and absolute resource limits are
  frozen;
- local/small-data tests pass;
- the portable CPU inference/export path and benchmark harness pass the M4
  preliminary below-10× gate;
- offline environment reconstructs on the live node;
- one-GPU and two-GPU smoke tests pass;
- node-local/Lustre staging is measured and verified;
- forced interruption and resume pass;
- checkpoint interval and cleanup behavior pass;
- telemetry and complete attempt inventory are enabled;
- confirmation target remains unread; and
- a dry-run Slurm submission produces the expected environment, resource, and
  artifact receipts.

Once these gates pass, ordinary training, screening, development evaluation,
candidate sealing, and conditional confirmation proceed autonomously inside
the single dispatched work package under their frozen rules.

## 18. References and governing records

Repository evidence:

- [A9d accepted report](../reports/a9d-successor-development-confirmation-report.md)
- [A9d work package](../work-packages/20260715-a9d-successor-development-confirmation/package.md)
- [A9 model-family envelope](../work-packages/20260715-a9a-successor-family-foundation/artifacts/model-family-envelope.md)
- [A9 tuning-harness contract](../work-packages/20260715-a9a-successor-family-foundation/artifacts/tuning-harness-contract.md)
- [A9 data and evaluation plan](../work-packages/20260715-a9a-successor-family-foundation/artifacts/data-and-evaluation-plan.md)
- [A7a daily precipitation-structure report](../reports/a7a-daily-precipitation-structure-report.md)
- [A8c routed-daily pilot](../work-packages/20260715-a8c-routed-daily-pilot/package.md)
- [State-of-the-art gap analysis](../lit-reviews/sota-climate-generator-gap-analysis.md)
- [State-of-the-art annotated bibliography](../lit-reviews/sota-climate-generator-annotated-bibliography.md)
- [Daily source assessment](../work-packages/20260713-a5b-coefficient-source-assessment/artifacts/daily-source-assessment.md)
- [ADR-0001 source authority](../decisions/0001-source-code-authority-port.md)
- [ADR-0002 extension-quality authority](../decisions/0002-quality-metrics-authority.md)
- [Faithful CLI runtime benchmark](../work-packages/20260710-cli-runtime-benchmark/package.md)

External infrastructure references, checked 2026-07-16:

- C3+3. [Using GPU resources on C3+3](https://docs.c3plus3.org/docs/workshops/Cluster/GPU_Nodes.html).
- C3+3. [Lemhi user guide](https://docs.c3plus3.org/docs/help/Getting_Started/).
- NVIDIA. [L40 data-center GPU specifications](https://www.nvidia.com/en-in/data-center/l40/).
- NVIDIA. [L40 datasheet](https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/support-guide/NVIDIA-L40-Datasheet-January-2023.pdf).

Literature references for the ML boundary and candidate comparison remain in
the repository's annotated bibliography. A10's work package must refresh any
model-specific literature needed for the frozen architecture rather than
claiming that forecast/downscaling papers directly validate a point-weather
generator.
