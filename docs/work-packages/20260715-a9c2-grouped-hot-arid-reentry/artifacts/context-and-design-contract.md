# A9c2 context and design contract

Status: scaffolded prospective contract; no A9c2 observed-series access

## Why A9c2 exists

A9c applied the A9a objective registry exactly. Its 2018--2024 hot-arid
development sites contained 136 events at AZ Yuma 27 ENE and 97 at CA
Stovepipe Wells 1 SW. The registry required 150 station events for storm
time-to-peak and peak ratio and 200 station events plus deep support for joint
dependence. It therefore returned 0/2 stations in three mandatory cells and
`HOLD-A9C-GATE-CALIBRATION` before any candidate score.

Those counts correspond to 19.4 and 13.9 events per station-year. No A9
artifact derived the 150/200 floors from hot-arid precision or power. The
operator therefore retained the terminal but rejected the follow-on premise
that each of these dry stations should be made to satisfy those counts. A9c2
increases spatial replication and evaluates storm descriptors at a frozen,
station-balanced group level.

## Immutable predecessor facts

- A9c materialized 40 Daymet and 24 USCRN normalized objects from 180 exact
  USCRN station-years, generated 7,000 candidate-blind null identities and 14
  thresholds, completed five fits, accessed zero candidate development scores,
  and accessed zero confirmation series.
- Every A9c object, partial fit, implementation, correction, and conclusion is
  exposed development evidence. Hash-valid normalized observed objects may be
  reused only as explicitly exposed A9c2 fit/development inputs under the new
  role manifest. No A9c fit, threshold, objective result, or selection
  artifact may be relabeled as A9c2 evidence or become confirmation evidence.
- A9b's schemas, role firewall, deterministic harness, two actual-plugin
  boundary, Philox random-field ownership, Pareto machinery, and selector are
  unchanged.
- The two research classes remain `alternating_renewal_marked_v1` and
  `latent_regime_marked_v1`. The eight-configuration A9c grid is retained
  unless an explicit amendment is frozen before new series access.
- The 18 A9a confirmation sites remain a sealed metadata-only roster. No
  confirmation path, byte, summary, event count, quality result, or source-
  object identity may enter A9c2.
- Faithful generation and the vendored Fortran are untouched. A9c2 remains
  research-only and creates no runtime identifier.

## Role and roster design

### Retained roles

- Retain A9c's Daymet roles: 1980--2009 coefficient fit and 2010--2025 exposed
  development.
- Retain A9c's USCRN periods: 2010--2017 fit and 2018--2024 exposed
  development. A period change requires a pre-access amendment and a complete
  new source/role freeze.
- Retain all 12 A9c USCRN development locations. The ten non-hot-arid sites
  preserve the other five strata; the two hot-arid sites remain included.
- New USCRN objects are allowed only for additional hot-arid development
  locations selected by the rule below.

### Metadata-only selection rule

Before reading a new station-year series:

1. enumerate all active USCRN sites commissioned by the frozen 2010 fit-period
   start from one hash-pinned station listing;
2. apply one hash-pinned climate-zone/seasonality crosswalk and the same
   primary `hot_arid` semantics to every site;
3. exclude the 18 locked confirmation station IDs and any site that violates
   the prospectively frozen confirmation-separation rule;
4. exclude a site only for metadata-known source-period absence, not for event
   frequency or candidate behavior;
5. retain Yuma and Stovepipe Wells and accept every remaining eligible site;
   do not rank eligible sites or cap the roster after five; and
6. require at least five distinct accepted hot-arid locations. Fewer returns
   `HOLD-A9C2-HOT-ARID-ROSTER` before series access.

The execution freeze must publish all included and excluded sites with the
single applicable reason. The A9a 75 km development-to-confirmation partition
separation is the default rule. It does not establish independence among hot-
arid development sites. Execution publishes all within-group distances and
freezes a spatial-dependence treatment for uncertainty. If metadata show that
the partition rule makes five sites impossible, execution holds and requests
an operator decision; it may not silently weaken the partition or replace a
confirmation station.

### Support-only boundary

After the roster and all transformations are frozen, a separately authorized
support-only stage may acquire the entire accepted roster and compute source
completeness, valid event/deep-event counts, station-year distribution, and
nondegeneracy diagnostics. It may not read candidate outputs. No accepted site
may be removed or downweighted because of those results. The stage either
calibrates the complete design or returns `HOLD-A9C2-GROUP-POWER`.

## Grouped storm-objective amendment

The amendment applies to `storm_duration`, `storm_time_to_peak`,
`storm_peak_ratio`, and `storm_joint_dependence` in the hot-arid stratum. It
does not silently change event segmentation, precipitation amount, daily
occurrence, conditional context, other objective families, or the five other
strata. Execution writes a complete `a9c2-objective-registry-v1.json` and a
versioned SPEC-A9 grouped-evaluation amendment; it never edits or relabels
A9a's registry or SPEC-A9 revision 1.

### Station-balanced empirical law

For a stratum with `S` stations and `n_s` valid events at station `s`, each
station receives weight `1/S` and each event at that station receives weight
`1/(S*n_s)`. The observed and generated sides use identical weights and
transforms. Thus a wetter station contributes more information to its own
empirical distribution but cannot contribute more total stratum mass.

For duration, time-to-peak, and peak ratio, equal station weighting is applied
inside each registered season cell before season-to-stratum aggregation. A
station-season with zero valid descriptor events remains explicitly
unavailable and is never replaced; calibration evaluates the complete frozen
contributor mask. Joint dependence retains station-to-stratum aggregation,
with season remaining a component of the joint rank vector rather than a
silently added outer aggregation.

The original duration log-energy, time-to-peak Cramer--von Mises plus boundary-
mass, peak-ratio log-energy, and joint rank-space energy distances remain the
starting estimators. Execution must specify the weighted formulas, tie/
boundary rules, missingness, zero-event behavior, deep-event definition, and
deterministic numeric implementation before support-only access.

Fit-side descriptor rules are versioned at the same boundary. The former
50/150/1,000 event hierarchy cannot remain as an implicit precondition after
the evaluation rule changes. Both candidate classes instead use one frozen
hierarchical identifiability and convergence rule, with station, group, and
global contributions published. Its fixtures and numerical criteria must be
ratified before support-only access and applied symmetrically to both classes.

### Heterogeneity guards

Grouping cannot hide a bad station. Every objective publishes:

- the station-balanced group distance and interval;
- every station's descriptive distance and interval, even when wide;
- leave-one-site-out group distances;
- the maximum site contribution and its identity; and
- a pre-frozen heterogeneity statistic comparing between-site and within-site
  variation.

The candidate-blind calibration must set a guard for catastrophic single-site
failure. It must not recreate the rejected 150/200 per-site availability
floor. A site with sparse observations remains represented with uncertainty.

### Resampling and availability

- Use two-stage resampling: sample stations uniformly, then sample complete
  local-standard station-years/event blocks within station. Events crossing a
  year boundary stay with their registered start year.
- Preserve spatial replication with station clusters and leave-one-site-out
  layers rather than treating all events as independent; include the frozen
  spatial-dependence adjustment.
- Retain 500 paired candidate-blind identities per objective family and
  horizon and the existing familywise alpha 0.05 maximum-statistic structure.
- Calibrate the grouped design at the actual station/year/event and deep-event
  pattern. Availability is based on finite estimator behavior, interval
  stability, controlled same-law false failure, and power against newly
  justified, predeclared candidate-neutral material perturbations.
- Require at least 0.80 power for each material perturbation. The exact
  perturbation formulas and normalized precision limit are unresolved
  scaffold decisions that must be explicitly ratified in the design freeze;
  they cannot be selected after support or candidate access. A9a's 0.02
  time-to-peak normalization floor is not treated as a power alternative, and
  no nonexistent peak-ratio or joint-distance floor is inferred.
- Freeze the perturbations, precision/power criteria, Monte Carlo error rule,
  and all numeric thresholds before candidate development scoring.
- Publish the full calibration curve over station and event subsamples so the
  eventual support decision is auditable. Do not infer a universal sample-size
  floor from a single pass point.

## Fresh campaign requirement

A9c2 receives a new campaign ID, RNG domains, role manifest, source/access
manifest, fit identities, null thresholds, optimizer ledger, and selection
trace. All eight registered configurations are refit. All seven objective
families at 30 and 100 years receive new 500-replicate candidate-blind null
calibration. The complete six-stratum comparison is rerun because changing a
mandatory objective's aggregation can change survival, Pareto dominance, and
the lexicographic selection result.

The five non-hot-arid strata retain their A9c station-level evaluation rules.
This asymmetry is explicit: grouped evaluation is a prospective sparse-regime
measurement design, not a global post-outcome relaxation.

A9c research code may be repaired or extended prospectively, but source hashes
and every correction boundary are recorded. An A9c partial fit may seed a
deterministic optimizer only if the initialization rule is frozen for every
configuration before new development access; it can never be reported as the
A9c2 fit itself.

## Resource contract

The A9c ceilings are the initial bound: two classes, 4,096 analytic proposals
per class, 256 short-screen configurations per class, 64 full configurations
per class, eight Pareto replays, eight workers, 12 GiB RSS, 24 hours per stage,
72 hours per campaign, and 50 GiB retained. Before series access, execution
must estimate the effect of the larger roster and either freeze these ceilings
or record an operator-approved prospective revision. Resource exhaustion is a
hold, never permission to prune a dry site or favor a candidate.

Evidence at or above 10 MiB uses Git LFS. Raw third-party annual objects are
hash-ledgered and may be discarded after deterministic normalization; public
retention follows source licensing and existing A9 practice.

## Selection and downstream boundary

After every upstream gate passes, A9c2 reuses
`a9_lexicographic_pareto_v1`: reject incomplete/ineligible/degraded candidates,
then maximize worst mandatory regime/family improvement, maximize improved
family count, minimize median distance, minimize effective parameters, and
tie-break by candidate-class ID. Group results and heterogeneity guards are
mandatory inputs, not advisory plots.

Only `CANDIDATE-FROZEN-READY-A9D` may make a separately dispatched A9d
possible. It does not itself authorize confirmation access. Every other
terminal leaves A9d and A9e unauthorized.
