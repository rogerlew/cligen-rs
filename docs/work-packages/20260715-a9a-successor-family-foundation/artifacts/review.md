# A9a consolidated foundation review

Verdict: `ACCEPT`
Open P1 findings: 0
Open P2 findings: 0
Reviewed: 2026-07-15

## Scope

This review covers authority traceability, prior-evidence exposure, model-
family completeness, candidate-class independence, fit/pooling/failure
semantics, source feasibility, data-role leakage, confirmation access,
objective/gate calibration, RNG/numerical contracts, resource bounds, schema
validity, public-interface isolation, and consistency with the roadmap and
work-package catalog. It does not review an implemented harness, fitted model,
coefficient, generated climate, or production profile because A9a creates none.

## Review method

The review read all 25 files in `authority-manifest-v1.json`, checked their
current byte lengths and SHA-256 identities, and traced every RQ requirement to
accepted evidence. It independently inspected the 10 exposed source records,
37-station union, and 14 retired/exposed model identifiers. It validated the
three Draft 2020-12 schemas and the 31-entry objective registry, recomputed
roster distances and stratum counts, checked local links, scanned production
crates for research identifiers, and verified the dispatch commit and A8c1
terminal.

The scientific pass used six lenses: accuracy/authority, model validity,
non-isomorphism/identifiability, data leakage, numerical contract, and cross-
document consistency. Repository gates were run after the corrective edits.

## Findings and dispositions

No P1 or P2 finding remains open.

### REV-A9A-001 — wet-threshold ambiguity (`P2`, resolved)

The first draft used positive precipitation for all daily occurrence metrics,
while accepted A7 structure evidence used 1.0 mm and faithful consumer/event
branches use positive precipitation. Conflating them would have weakened both
A7 comparability and A8c downstream-context traceability.

Disposition: the specification, data plan, fit schema, and objective registry
now freeze `wet0` (strictly greater than 0.0 mm) for model positive mass,
events, and consumer context, and `r1mm` (at least 1.0 mm) for the primary
A7-comparable spell/higher-order surface. Both are reported and neither is
tunable.

### REV-A9A-002 — pooling hierarchy incomplete (`P2`, resolved)

The scaffold specified eligibility and declared pooling but did not select the
hierarchical levels. That left an outcome-time path to switch pool scope after
an arid failure.

Disposition: both class slots now use station parameters nested in one of six
frozen primary-stratum hyperdistributions, nested in one global family
hyperdistribution. Group membership and shrinkage are fixed on coefficient-fit
data; cold-arid is only a cross-tag; runtime consumes a materialized station fit
and never classifies or pools. Exact station/group exposure minima and
`fit_ineligible` behavior are frozen.

### REV-A9A-003 — confirmation state wording (`P2`, resolved)

One draft described target series as “sealed,” although only metadata had been
read and target objects do not yet exist locally. That overstated the evidence
state.

Disposition: all records now say `metadata_only`. A future custodian must
acquire/hash target bytes and atomically create a sealed freeze. Fit,
development, optimization, and gate-calibration commands reject confirmation
paths, hashes, logical identities, and station-period keys before and after
that transition.

## Review conclusions by lens

### Accuracy and traceability

PASS. Twenty-five authority files reproduce exactly. Quantitative A5--A8
claims remain attributed to accepted records, while D01--D09 are explicitly
labeled prospective design decisions rather than empirical results. The
exposure manifest includes the known A5/A7 17-site corpus, A8a panel, A8b
stations, A8c pilot, fixed periods, source records, and candidate identifiers.
It does not relabel any exposed target as confirmation.

NOAA source claims match the retrieved official documentation: Subhourly01 has
five-minute precipitation, temperature, solar radiation, relative humidity,
wetness, and 1.5 m wind, with local-standard/UTC timestamps, missing values, and
documented QC. The contract correctly marks wind direction absent and refuses
to interpret 1.5 m wind as 10 m wind.

### Scientific validity and family completeness

PASS. Both class slots jointly cover occurrence/spells, amount body/tail/
memory, event descriptors, and daily context. Monthly wet fraction, wet amount,
total mean/variance, covariance contributions, zero-month behavior, and all
Gregorian month lengths are reconciled at the distribution level. Realized
months are not repaired. No scalar annual state is presumed; a later low-
frequency state requires residual evidence and a new prospective class.

The objective registry retains 30/100-year horizons and includes wet/dry
spells, higher-order occurrence, amount mean/CV/memory/tail, zero-month and
monthly/annual dispersion, cross-month dependence, 1/3/5-day extremes, storm
duration/time-to-peak/peak ratio/joint dependence, compound temperature/
humidity/solar/wind context, and winter cold-wet/freeze-transition/dependence
proxies. Winter metrics do not claim snowpack, precipitation phase, or soil
freeze/thaw.

### Candidate-class non-isomorphism and identifiability

PASS as a foundation contract. The alternating-renewal slot has observable
spell state and no hidden regime. The latent slot has hidden semi-Markov state,
strictly interior wet probability in every state, and joint marked emissions;
observed spells emerge and may cross state boundaries. Degenerate support that
maps hidden state to observed spell state is excluded. Cross-fit synthetic
recovery and an implementation-level factorization audit must still pass before
A9c; failure returns `MODEL-CLASS-EQUIVALENCE` rather than a ranking.

### Data leakage and applicability

PASS. The exact 18-site roster was selected from official station metadata
without reading target series. It contains three active CRN sites in each of
six primary strata, every nearest exposed-site distance is at least 75 km, and
the minimum within-stratum distance is above 150 km. Labels require a hash-
pinned metadata-only climate crosswalk before target acquisition. A mismatch,
source failure, or insufficient availability holds without substitution.

Fit, development, gate-calibration, and confirmation roles are separately
identified and must become exact hash manifests before use. A new download of
the same logical record cannot cross roles. Confirmation is one shot and cannot
feed selection, gates, fit, stations, periods, or burns back into the campaign.

### Numerical, RNG, and optimization contract

PASS. The monthly variance identity includes covariance terms and requires
analytic or deterministic-quadrature certification. Nonfinite values, invalid
support, zero scales, and resource exhaustion fail closed. Fit, optimizer,
parameter-member, and simulation RNG identities are distinct. Counter-based
Philox component/date/slot indexing supports common random numbers without
draw-shift coupling and does not consume faithful streams.

The full objective vector and Pareto frontier precede the selection rule. The
500-replicate, familywise-alpha-0.05 maximum-statistic null is candidate-blind;
baseline-zero rules are finite; unavailable values are not passes. Resource
stages, workers, memory, time, retained bytes, retries, and checkpoint/hash-
chain behavior are bounded prospectively.

### Interface and repository consistency

PASS. SPEC-A9 and the schema registry label all new IDs research-only. No A9
identifier appears under `crates/`; neither `crates/` nor
`reference/cligen532/` differs from dispatch. No station schema, accepted
profile, station model, provenance enum, default, candidate coefficient,
generated climate, or downstream consumer surface was created. A9b is a
freeze-ready handoff but remains unscaffolded and unauthorized.

## Residual uncertainty and future holds

- USCRN is a living product. A9c/A9d must bind exact station-year bytes,
  processing/version lineage, normalized records, and completeness; this
  review establishes source feasibility, not target quality.
- The metadata-only stratum labels have not yet been crosswalk-validated. The
  no-substitution hold makes this uncertainty explicit rather than silently
  repairing the roster.
- The 2010--2025 confirmation period supports mandatory 12-year annual metrics
  but not the 20-/30-year lag/covariance/spectral objectives at every site.
  Those objectives are secondary/report-only with explicit unavailable rules;
  the core 30-/100-year simulation horizons remain mandatory.
- Descriptor fitting is limited by five-minute resolution and the six-hour
  event definition. It cannot substantiate native hyetographs or EI30.
- Structural class independence is specified but must be demonstrated against
  the actual A9b/A9c implementations. The contract intentionally holds if the
  implementations collapse.
- Resource ceilings are prospective and unbenchmarked. They may be reduced
  before candidate outcomes, never enlarged outcome-time.

These are registered downstream checks, not open defects in the A9a
foundation.

## Verdict

A9a satisfies `EXECUTED-COMPLETE` and returns `FOUNDATION-READY-A9B`.
This authorizes no A9b work without a separate operator dispatch and no climate
generation, runtime pilot, production promotion, openWEPP integration, or
WEPPcloud integration.
