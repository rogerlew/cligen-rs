# A9a data and evaluation plan

Status: scaffolded plan; exact corpus, sources, thresholds, and burns remain
open until A9a execution

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
- cold arid;
- monsoonal transition;
- non-monsoonal semi-arid;
- humid/wet; and
- cold/snow-dominated forcing context.

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
  exactly. A9 must name either the official civil-date mapping or a separately
  versioned project transform.
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

A9a must inventory overlapping, quality-controlled sources for:

- precipitation;
- Tmax and Tmin;
- humidity/dew point or vapor pressure;
- shortwave radiation; and
- wind speed/direction.

No single prior product supplies every field with equal authority. Source and
day-boundary decisions are variable-specific, and missing variables cannot be
silently scored against station-contract values as though observed.

### Storm descriptors and subdaily evidence

Daily gridded precipitation cannot identify duration, time-to-peak, peak
ratio, or true subdaily intensity. A9a must either:

- identify a hashable breakpoint, hourly, or finer gauge/radar corpus with
  event segmentation, timezone/day boundary, QC, and rights sufficient for a
  descriptor-level candidate; or
- close `EXECUTED-HOLD-DATA-PARTITION` for the event component and prevent a
  model implementation that invents plausible-looking storm parameters.

Descriptor-only evaluation may use named, versioned WEPP disaggregation for
diagnostics, but it is not interchangeable with observed subdaily validation.

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
- Use multiple predeclared, domain-separated burns; determine counts through
  gate-calibration and power/resource analysis rather than inheriting eight by
  habit.
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

## Confirmation selection and access

1. Define metadata-only candidate station/site inventory and exclusions.
2. Freeze deterministic selection, geographic separation, strata, source
   products, periods, and no-substitution rules.
3. Record source URLs/object identifiers and acquire without inspecting target
   summaries beyond registered integrity/QC checks.
4. Freeze exact hashes, normalized logical records, candidate/model/fit recipe,
   objectives, thresholds, burns, and decision rule.
5. Run one confirmation campaign and close on its registered terminal.

An acquisition failure may record a source as unavailable but cannot select a
replacement station after target exposure.

## Downstream and production boundary

This A9 sequence intentionally excludes openWEPP and WEPPcloud integration.
Climate success can authorize an internal Rust profile pilot and later
climate-corpus confirmation. It cannot authorize a public default or production
promotion. ADR-0004's downstream-response and intervention criteria require a
separate future roadmap decision after the climate family is stable enough to
justify that investment.
