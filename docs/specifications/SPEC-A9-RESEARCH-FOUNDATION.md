# SPEC-A9-RESEARCH-FOUNDATION — successor research artifacts

Status: research-only, revision 1 (A9a); no production runtime surface
Date: 2026-07-15

## Surface

This specification defines the research-only contracts used to implement and
evaluate the A9 stochastic successor family:

- immutable fit artifacts;
- objective registries;
- data-role manifests and their confirmation-access barrier;
- candidate-simulator and optimizer boundaries;
- deterministic simulation identities; and
- append-only evaluation records.

It does not add a station-document revision, station-model identifier,
generation profile, accepted provenance value, or output schema. The first A9
runtime identifier can be proposed only by a later Rust-pilot package.

Machine contracts:

- [fit artifact v1](a9-fit-artifact-v1.schema.json);
- [objective registry v1](a9-objective-registry-v1.schema.json); and
- [data-role manifest v1](a9-data-role-manifest-v1.schema.json).

## Producers and consumers

The A9b external research harness produces and validates these artifacts.
Candidate fitters, simulators, metric implementations, and optimizers are
plugins behind versioned interfaces. A9c consumes fit/development and
gate-calibration roles. A9d alone may consume a sealed confirmation role after
its one-shot access transition. A possible A9e Rust pilot consumes only a fit
artifact and selected candidate specification that survived A9d.

No accepted `cligen` runtime command consumes these research schemas.

## Authority basis

The contract is an extension under ADR-0001 and is governed scientifically by
ADR-0002 and ADR-0004. Its requirement-level traceability is the A9a
evidence-to-requirements ledger. The exact authority and prior-exposure hashes
are package artifacts under
`docs/work-packages/20260715-a9a-successor-family-foundation/artifacts/`.

## Independent identities

The following axes are independent and MUST NOT be inferred from one another:

1. station-document schema;
2. model-family and candidate-class version;
3. fit-artifact schema, fit ID, and content hash;
4. generation profile;
5. optimizer and objective-registry versions;
6. dataset object and normalized logical-record hashes;
7. parameter or uncertainty-member identity;
8. simulation RNG and burn identity; and
9. typed-output and provenance schemas.

A fit artifact does not authorize a profile. A station schema does not imply a
qualified model. An optimizer change does not rename a probability law.

## Canonical representation and hashes

Research JSON is UTF-8, sorted by object key, indented by two spaces, ends in
one LF, and rejects NaN and infinity. A `sha256` field is the lowercase SHA-256
of the exact referenced bytes unless the field explicitly names a canonical
logical-record hash. Self-hashes are computed from the canonical object with
the self-hash field omitted.

Unknown fields fail closed. Schema validation precedes hash validation and any
science computation.

## Fit artifact semantics

Every attempted fit returns exactly one typed state:

- `fit_valid`: parameters and all registered support, exposure,
  identifiability, and moment checks passed;
- `fit_ineligible`: the source record cannot identify the registered model at
  the frozen pooling scope; or
- `fit_failed`: software, optimizer, or numerical execution failed.

Only `fit_valid` may be simulated. Neither other state permits dropping a
month, substituting a site, changing a pooling group, relaxing a threshold, or
selecting a fallback. The first A9 family has no runtime fallback. A future
fallback requires a separate versioned contract and prospective study.

The fit artifact records exact source objects and logical records, variables,
units, calendar and day boundary, time period, missingness, preprocessing,
detrending, pooling, event segmentation, parameter support, optimizer and
software identity, fit seed, objective registry, stopping and resource rules,
effective exposures, diagnostics, uncertainty/member identity, and all hard
checks. Runtime never refits or interprets missing values.

## Data roles and confirmation barrier

The roles are `coefficient_fit`, `development`, `gate_calibration`, and
`confirmation`. A logical record is identified by source product/version,
source-object hash, normalized-record hash, site, variables, calendar/day
boundary, and inclusive period. Logical records in different roles MUST be
disjoint; a fresh download does not create a new record.

All A5--A8 stations, periods, products, generated outputs, metrics, and
candidate outcomes are exposed development evidence. Their hashes are retained
in the A9a exposure manifest. They cannot be declared confirmation.

Confirmation has these access states:

1. `metadata_only`: station metadata and frozen selection rules may be read;
2. `sealed`: target objects have been acquired by a custodian, hashed, and
   made inaccessible to fit/development commands;
3. `consumed`: the one registered campaign has run; and
4. `invalidated`: integrity, acquisition, or pre-access contract failure ended
   the campaign before a scientific result.

Only the confirmation command may make the atomic `sealed` to `consumed`
transition. It first verifies the complete freeze hash and writes an append-only
access record. Fit, optimize, development-evaluate, and gate-calibrate commands
MUST reject confirmation paths, object hashes, logical hashes, and station-
period keys in every state. After `consumed`, no candidate, fit recipe,
parameter bounds, objective, normalization, threshold, station, period, burn,
or decision rule changes within that campaign.

Before outcome access, a parser or integrity defect may create one documented
successor freeze. After outcome access, the registered terminal is final; no
replacement site or second confirmation is allowed under the same campaign ID.

## Candidate simulator interface

The first comparison has exactly two research class IDs:
`alternating_renewal_marked_v1`, an explicit alternating semi-Markov observed-
spell law with conditional marks, and `latent_regime_marked_v1`, a hidden
semi-Markov regime law with strictly interior wet probability and joint marked
emissions in every state. Their complete state and non-isomorphism rules are
in the A9a model-family envelope. These are research schema values, not
accepted runtime generation profiles or station models.

A candidate plugin receives only:

- a validated `fit_valid` artifact;
- a candidate-class configuration whose schema hash matches the fit;
- a site, start date, and requested 100-year horizon;
- a simulation burn identity; and
- the A9 counter-based random field.

It returns a Gregorian daily stream plus event descriptors and a typed daily
context. It MUST NOT receive observed targets, objective thresholds, candidate
rank, climate-stratum labels, or another candidate's output. Horizon-dependent
parameters and output-selected routing are prohibited. The 30-year evaluation
is the byte-identical prefix of the single paired 100-year stream.

The daily context includes wetness, occurrence/spell state, wet amount and
amount-state/quantile information, event descriptors, seasonal and optional
latent state, and fit/class identity. A candidate declares which meteorological
consumers use each field; unchanged consumers remain explicit rather than
assumed independent of precipitation.

## Randomness and common random numbers

Fit, optimizer proposal, parameter/member, and simulation randomness occupy
separate domains. The common-random-number service uses Philox4x32-10 and the
domain string `cligen-rs/a9-crn/v1\0`. SHA-256 over the domain plus campaign,
candidate-neutral site, burn, component, Gregorian date, and variate-slot
identities supplies the key/counter material. A9b freezes the exact byte
encoding and publishes golden vectors before any observed-data tuning.

Candidate components own stable variate slots. Optional or rejected draws do
not shift another component or later date. Candidate-specific additional draws
use a class-namespaced component and are reported as unpaired. Fitters and
optimizers record their own declared RNG algorithm/version and seed derivation;
they never consume simulation fields or faithful CLIGEN streams.

## Hard constraints and monthly budget

Two wet thresholds are fixed and never tuned. `wet0` is daily precipitation
strictly greater than 0.0 mm and governs the model's positive mass, storm/event
presence, and faithful consumer-context compatibility. `r1mm` is daily
precipitation at least 1.0 mm and is the primary A7-comparable occurrence,
spell, and higher-order diagnostic. The objective registry reports both where
defined; it never substitutes one for the other.

Hard constraints determine whether a parameterization is mathematically and
physically admissible. They are not finite-simulation climate scores. At
minimum they verify:

- probability, duration, tail, covariance, correlation, and matrix support;
- finite nonnegative wet amounts, positive event durations, and registered
  time-to-peak/peak-ratio support;
- fit exposure, scale, identifiability, and pooling eligibility;
- deterministic replay, calendar, context, and provenance invariants; and
- analytic or deterministic-quadrature monthly moments for all Gregorian
  month lengths.

For daily precipitation `Y_t = I_t X_t` and monthly total
`S_n = sum(Y_t)`, every candidate reports `E[S_n]` and
`Var(S_n) = sum Var(Y_t) + 2 sum_{s<t} Cov(Y_s,Y_t)`. The reported occurrence,
amount, and covariance contributions MUST reconcile to those totals within the
registered quadrature tolerance. Agreement with observed monthly climate is an
objective with null-calibrated uncertainty, not an output-repair instruction.
Realized monthly totals are never forced by rejection, scaling, clipping, or
conditioning.

## Objective registry and selection

Every objective defines its statistic, units, estimator, direction,
normalization, aggregation, minimum support, missing/unavailable behavior,
baseline-zero rule, uncertainty, selection role, and applicable horizons.
Unavailable is neither zero nor pass.

A9c first reports the complete objective vector and Pareto frontier. It then
uses this frozen lexicographic rule:

1. reject hard-infeasible, incomplete, or mandatory-stratum-ineligible fits;
2. reject any candidate with a familywise null-calibrated material degradation
   in a mandatory metric family, stratum, or horizon;
3. maximize the minimum regime-by-mandatory-family standardized improvement;
4. maximize the number of familywise material improvements;
5. minimize the median normalized distance across available cells;
6. minimize fitted effective parameter count; and
7. break an exact tie by ascending candidate-class ID.

Gate calibration sets noninferiority and improvement thresholds from the
paired same-model/null distribution before candidate ranking. Each metric uses
the registered maximum-statistic 95th percentile within its family and horizon,
with an absolute measurement floor. A baseline zero uses the registry's
absolute or two-part rule and never divides by zero.

A9d is one shot. It passes only if every engineering invariant passes, every
mandatory stratum meets availability, no mandatory family materially degrades
at either horizon, monthly mean/variance reconciliation is noninferior, storm
descriptor support is noninferior, and at least two of occurrence/spell,
wet-amount, aggregate/extreme, storm, or compound/winter families materially
improve at both horizons. Otherwise its registered stop is final.

## Event and compound-observation boundary

The first descriptor-level source is NOAA USCRN `Subhourly01`, five-minute
periods ending at reported UTC and local-standard-time timestamps. It supplies
precipitation, air temperature, solar radiation, relative humidity, wetness,
and 1.5 m wind speed. Missing derived precipitation is invalid; QC flags other
variables as 0 good, 1 overflow, or 3 erroneous. Wind direction is absent and
the 1.5 m speed is not interchangeable with 10 m airport wind.

The event rule is `a9_uscrn_event_6h_v1`. An event begins with the first
positive five-minute precipitation interval
after 72 consecutive valid zero intervals and ends with the last positive
interval before the next 72 valid zero intervals. Missing intervals in either
separation window invalidate the event. Depth is the interval sum; duration is
from the first interval's lower edge to the last interval's upper edge;
time-to-peak is the midpoint of the earliest maximum-rate interval divided by
duration; peak ratio is maximum five-minute rate divided by event-mean rate.
Events retain their full cross-day path and are assigned season by start time.
Cold-context events remain labeled by air temperature and are not called rain,
snow, or a physical phase partition.

These descriptors support a descriptor model and validation. They do not
support a continuous hyetograph, EI30, native subdaily output, or single-storm
mode. Such claims require another specification and high-resolution output.

## Numerical and failure semantics

- No NaN, infinity, coercive default, or unknown enum is accepted.
- All units and conversions are explicit; source values are retained before
  conversion.
- Deterministic quadrature records method, order, tolerance, and software.
- Optimization exhaustion, timeout, memory exhaustion, simulator failure, and
  nonconvergence are typed incomplete outcomes, never favorable scores.
- A production Rust pilot remains no-fast-math, `#![forbid(unsafe_code)]`,
  faithful-stream isolated, and subject to the repository coverage/CRAP gate.
- Faithful mode and the vendored Fortran are untouched by this research
  contract.

## Provenance obligations

Every fit, evaluation, freeze, and confirmation record carries exact source and
logical hashes, periods, units, calendar/day boundary, missingness,
preprocessing, code commit and dirty state, schema/registry versions, candidate
class, optimizer/configuration, fit and simulation RNG identities, parameter
member, resource budget/use, and parent artifact hashes. Research artifacts do
not reuse accepted runtime profile or station-model identifiers.
