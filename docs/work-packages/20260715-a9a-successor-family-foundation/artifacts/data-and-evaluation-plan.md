# A9a data and evaluation plan

Status: executed, freeze-ready data/evaluation contract

## Evidence roles

| Role | Permitted use | Prohibited use |
|---|---|---|
| coefficient fit | estimate parameters, pooling, uncertainty, and support | model-class selection on the same held-out objective values |
| development/tuning | debug objectives, tune hyperparameters, compare architectures, set search strategy | confirmatory claims or continued access after being relabeled confirmation |
| gate calibration | faithful-clone/null false-failure, objective normalization, threshold and power planning | candidate-specific tuning or ranking |
| untouched confirmation | one frozen comparison after model, fit recipe, objectives, thresholds, corpus, and seeds are sealed | any feedback into the same campaign's model or thresholds |

Disjointness is defined by registered station, time, source-object, and logical-
record rules. A new download of the same exposed station-period/product does
not create independent confirmation evidence.

### Executable role plan

- **Coefficient fit:** candidate parameters use exact, hash-pinned Daymet V4
  R1 1980--2009 daily objects and a separately frozen USCRN event-development
  site set. The official Daymet civil mapping is used; no confirmation-period
  USCRN target is available to the fitter.
- **Development/tuning:** all assets in `exposure-manifest-v1.json`, including
  the 37 prior station IDs, remain exposed development. A9c may add a
  hash-frozen USCRN development set, but it must be disjoint by station from
  the exact confirmation roster before any series access.
- **Gate calibration:** synthetic same-model/null records and a separately
  frozen USCRN calibration site set are the only target records. They cannot
  be candidate fit or ranking inputs. The exact set and bytes are sealed
  before calibration and disjoint from development and confirmation.
- **Untouched confirmation:** the 18 station identities in
  `confirmation-metadata-selection-v1.json`, Daymet 1980--2009 fit period, and
  USCRN 2010--2025 target period are frozen. Only metadata has been accessed.

A9b implements the manifest validator and role firewall with synthetic records
only. A9c must materialize and hash the fit/development/gate objects before any
candidate tuning. A9d must seal exact confirmation bytes and a complete freeze
before its atomic one-shot access transition. A missing future object hash is
not an optional field once that role is used.

## Exposed development evidence

At minimum, the exposure inventory must include:

- the 17 A5a/A7a stations and their Daymet 1980--2025 objects;
- the eight available GHCN sensitivity records;
- A5b/A5e0 1980--2009 fit and 2010--2025 evaluation targets;
- the A7b 17-station fits and all 204 month cells;
- the A8a metadata inventory, selected 20-station panel, Daymet series, and
  available GHCN records;
- the ten exposed A8b fallback stations and zero-scale El Centro June result;
- the A8c six-station candidate/control outputs, metrics, classifications, and
  all four burns; and
- any station/product overlap in the quality-v3 corpus or later reports.

These assets remain valuable for harness development, regression, failure
fixtures, and model tuning. None is untouched A9 confirmation.

## Climate-regime design

The development and confirmation plans each address, with prospectively
defined membership rules:

- hot arid;
- arid applicability boundary / extremely sparse precipitation;
- monsoonal transition;
- non-monsoonal semi-arid;
- humid/wet; and
- cold/snow-dominated forcing context.

Cold-arid is a required cross-tag spanning the arid-boundary and cold primary
strata, not a seventh primary stratum. At least one site in each of those two
strata must carry it in the metadata crosswalk.

Membership used for corpus design is metadata-derived and frozen before target
series access. Runtime generation does not infer these classes. Confirmation
aggregation reports each registered stratum separately and includes mandatory
boundary cells so broad easy-regime performance cannot conceal sparse-regime
failure.

## Source requirements

### Daily precipitation and temperature

- Existing Daymet V4 R1 objects may support development because of their
  complete 1980--2009 fit coverage, North American domain, and prior archive.
- Daymet is a gridded estimate, uses GHCN-Daily inputs, and has a calendar
  convention that the prior project `noleap_365` transform did not reproduce
  exactly. A9 uses `daymet_official_365_v1`: leap years retain 29 February and
  omit 31 December. No value is shifted or imputed. Month/year completeness is
  evaluated after this exact mapping.
- PRISM AN daily is a useful CONUS method sensitivity, not an automatic
  production source. Its 1981 start, evolving inputs, product distinctions,
  and licensing/redistribution terms must be resolved before archiving or
  distributing derived coefficients.
- gridMET is useful when daily anomaly sequencing or broader energy variables
  matter, but its monthly precipitation and temperature constraints largely
  inherit PRISM. It is not an independent monthly covariance truth surface.
- GHCN point records are a sensitivity and station-data source, but are not
  statistically independent of Daymet where Daymet uses the same observing
  lineage.

### Compound daily context

The overlapping, quality-controlled source inventory covers:

- precipitation;
- Tmax and Tmin;
- humidity/dew point or vapor pressure;
- shortwave radiation; and
- wind speed/direction.

No single prior product supplies every field with equal authority. Source and
day-boundary decisions are variable-specific, and missing variables cannot be
silently scored against station-contract values as though observed.

USCRN `Subhourly01` supplies five-minute precipitation, air temperature,
global solar radiation, relative humidity, wetness, and 1.5 m wind speed.
Daily compound metrics use local standard time, never daylight-saving shifts;
UTC is retained for identity and cross-checking. USCRN has no wind direction,
and its 1.5 m speed is not converted to or described as 10 m airport wind.
Direction is unavailable in the first objective registry. Tmax/Tmin are daily
extrema of valid five-minute air temperature for event-context diagnostics;
Daily01 values provide a product-level sensitivity.

### Storm descriptors and subdaily evidence

Daily gridded precipitation cannot identify duration, time-to-peak, peak ratio,
or true subdaily intensity. A9 resolves the descriptor requirement with NOAA
USCRN `Subhourly01`, format 01 at five-minute resolution. Official source,
format, and station-metadata document hashes are in the confirmation metadata
artifact. The source is public NOAA observational data; A9c/A9d still bind
exact station-year bytes and the applicable precipitation-algorithm/version
lineage.

`a9_uscrn_event_6h_v1` uses 72 consecutive valid zero-precipitation intervals
as separation. Events retain cross-day intervals, use their start local-
standard date for season, and are invalid if either separation window contains
missing precipitation. Duration spans first-interval lower edge through last-
interval upper edge. Time-to-peak uses the midpoint of the earliest maximum
five-minute rate, divided by duration. Peak ratio is maximum five-minute rate
divided by event-mean rate. Cold events retain temperature context without a
phase label.

This supports descriptor-only fitting and validation. It does not authorize a
continuous hyetograph, native subdaily output, EI30, rainfall phase, or single-
storm generation. A later native-subdaily model requires another data/output
contract.

## Data sufficiency and fit applicability

Each candidate class defines minimum evidence for:

- wet days and dry days by season;
- adjacent wet pairs and spell-duration/state exposures;
- wet amounts above body/tail thresholds;
- nonzero monthly/seasonal scales;
- event counts and descriptor coverage;
- overlapping compound-variable days; and
- years for persistence/low-frequency estimation.

The fitter reports effective sample counts and uncertainty. Failure yields
`fit_ineligible`; it does not drop a month, lower the threshold, pool after
seeing failure, or substitute a nearby station. Pooling rules and group
membership are frozen before candidate fitting.

The first numeric minima are fixed in the model-family envelope and objective
registry. In particular, a zero-scale month remains present; amount metrics
may be unavailable while zero-month and occurrence metrics remain evidence.
A fit may borrow amount-memory or event-descriptor parameters only under the
pre-fit hierarchical rule. Failure after fitting cannot change membership.

`wet0` (daily precipitation greater than 0.0 mm) defines model positive mass,
events, and wetness passed to consumers. `r1mm` (at least 1.0 mm) is the primary
A7-comparable spell/occurrence threshold. Both are fixed and reported; neither
is a fit hyperparameter.

### Completeness

- A daily value is valid only when every required source field is present and
  passes its registered product QC; variables are evaluated separately.
- A month is complete with at least 90% valid expected days and no missing run
  longer than three days. No rescaling to a full month occurs.
- An annual aggregate requires all 12 complete months. A winter spans December
  of the preceding year through February and requires all three months.
- A five-minute event requires valid precipitation throughout both six-hour
  separation windows. Compound event metrics additionally require the named
  variable's good flag; failure does not invalidate precipitation-only event
  metrics.
- Observed annual/extreme metrics require the registry's record-length floor.
  Unsupported spectral objectives are reported unavailable rather than
  extrapolated.

## Evaluation vector

### Engineering invariants

- strict parse and fail-closed model/profile/fit combinations;
- deterministic replay and domain-separated RNG ownership;
- calendar, date continuity, row count, finite value, and support checks;
- exact 30-year prefix only where the candidate contract claims nesting;
- complete provenance and fit/source hashes; and
- faithful golden identity for unchanged faithful paths.

### Distributional climate objectives

1. **Occurrence and spells** — monthly/seasonal wet frequency, wet/dry spell
   distributions across year boundaries, higher-order residuals, transition
   and duration diagnostics.
2. **Wet amounts** — mean, SD/CV, quantiles, threshold exceedance, upper-tail
   fit, adjacent-wet dependence, and dry-gap-conditioned memory.
3. **Aggregates** — zero-month probability, monthly total mean/SD/CV,
   cross-month covariance, annual total variation, lag-one persistence, and
   low-frequency spectral summaries where record length supports them.
4. **Extremes** — annual 1/3/5-day maxima and return-level/tail diagnostics with
   uncertainty and adequate record-length qualification.
5. **Storm descriptors** — duration, time-to-peak fraction, peak ratio, their
   marginal and joint distributions, and dependence on depth, season,
   antecedent dry time, and cold context.
6. **Daily compound context** — wet/dry/event-conditioned Tmax, Tmin, humidity
   or dew point, radiation, and wind behavior; physical ordering and bounds;
   compound wet/cold and hot/dry frequencies where observed support exists.
7. **Winter proxies** — precipitation on freezing-context days, winter
   precipitation/temperature dependence, and air-temperature freeze-transition
   counts, explicitly not physical snowpack or soil freeze/thaw state.

Metrics remain climate statistics, not exact finite-trajectory gates.

## Horizons, burns, and uncertainty

- Retain both 30- and 100-year horizons.
- Screening uses two burns, full development four, final Pareto replay eight,
  and one-shot confirmation twelve. Each identity is domain-separated from a
  future campaign hash.
- Pair candidates and baselines through common random numbers where the
  stochastic contracts make pairing meaningful.
- Report station, regime, horizon, and pooled summaries with uncertainty.
- Distinguish trajectory variability, observed-sample uncertainty, fit
  uncertainty, parameter-member uncertainty, and structural/model-class
  uncertainty rather than merging them into one interval.

## Gate calibration

Before candidate confirmation:

- faithful-clone or same-model independent simulations estimate gate
  false-failure and finite-sample variability;
- observed resampling rules state the resampling unit, dependence assumptions,
  replicate count, and unavailable-cell minimum;
- baseline-zero metrics use an absolute or two-part rule fixed in advance;
- hard feasibility constraints are separated from statistical noninferiority
  or improvement objectives;
- familywise and regime-mandatory rules are explicit; and
- thresholds, aggregation, missingness, and power/resource tradeoffs are
  frozen without candidate confirmation output.

The exact rule is 500 paired same-model/null replicates per horizon, familywise
alpha 0.05, and a within-family/horizon maximum-statistic quantile bounded by
the objective's absolute floor. Candidate access begins only after the numeric
threshold artifact is hashed. Unavailable cells do not enter a denominator;
fewer than two available stations in any mandatory stratum fails availability.

## Confirmation selection and access

1. Use the already frozen 18-site metadata roster: three sites in each of hot-
   arid, arid-boundary, monsoonal-transition, non-monsoonal semi-arid, humid,
   and cold strata; every site is active CRN, at least 75 km from an exposed
   target site, and within-stratum separation exceeds 150 km.
2. Before series access, bind a hash-pinned metadata-only climate-zone/
   seasonality crosswalk and validate every primary label. Any mismatch holds;
   no station is replaced.
3. Acquire Daymet fit objects for 1980--2009 and USCRN Daily01/Subhourly01
   target objects for 2010--2025 through a custodian. Record source URLs and
   exact bytes without producing target summaries.
4. Freeze object and normalized logical hashes, fit recipe, selected A9c
   candidate/class/schema, parameters, objective registry, calibrated numeric
   gates, twelve burn identities, and the A9d terminal rule.
5. Atomically change the confirmation manifest from `sealed` to `consumed`, run
   one nested 100-year campaign per station/burn, evaluate the first 30 years
   as its prefix, and close on the registered pass or stop.

An acquisition failure may record a source as unavailable but cannot select a
replacement station after target exposure.

Confirmation passes only if all engineering invariants pass, every mandatory
stratum has the required availability, no mandatory family materially
degrades at either horizon, monthly mean/variance and storm descriptors remain
noninferior, and at least two priority families materially improve at both
horizons. Failure is final for that candidate and campaign; it does not reopen
tuning.

## Downstream and production boundary

This A9 sequence intentionally excludes openWEPP and WEPPcloud integration.
Climate success can authorize an internal Rust profile pilot and later
climate-corpus confirmation. It cannot authorize a public default or production
promotion. ADR-0004's downstream-response and intervention criteria require a
separate future roadmap decision after the climate family is stable enough to
justify that investment.

## Source references

- NOAA NCEI. [USCRN basic products and documentation](https://www.ncei.noaa.gov/access/crn/qcdatasets.html).
- NOAA NCEI. [`Subhourly01` format, fields, quality flags, and revision notes](https://www.ncei.noaa.gov/pub/data/uscrn/products/subhourly01/README.txt).
- NOAA NCEI. [USCRN station listing](https://www.ncei.noaa.gov/access/crn/station-listing).
- Palecki, M. A., et al. (2015). *U.S. Climate Reference Network Processed
  Data from USCRN Database Version 2*. DOI
  [10.7289/V5MS3QR9](https://doi.org/10.7289/V5MS3QR9).
- Thornton, M. M., et al. (2022). *Daymet: Daily Surface Weather Data on a
  1-km Grid for North America, Version 4 R1*. DOI
  [10.3334/ORNLDAAC/2129](https://doi.org/10.3334/ORNLDAAC/2129).

Retrieved NOAA document identities and the target-access statement are frozen
in `confirmation-metadata-selection-v1.json`; later station-year bytes require
their own object and logical hashes.
