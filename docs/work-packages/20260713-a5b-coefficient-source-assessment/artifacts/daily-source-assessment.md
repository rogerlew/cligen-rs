# Daily Time-Series Source for A5b Fourier/EOF Coefficients

Status: **RECOMMENDATION FOR A5b SCAFFOLDING**  
Date: 2026-07-13  
Scope: Daymet V4 R1, PRISM AN daily, and gridMET  
Decision surface: production-format interannual Fourier/EOF coefficients for
precipitation, Tmax, and Tmin

## Decision

Use **Daymet V4 R1 as the primary A5b coefficient-fitting source**.

Use **PRISM AN daily as the first CONUS-only fit-source sensitivity and
terrain-resolved localization benchmark**, if that sensitivity is added
prospectively to the A5b contract before candidate output.

Do **not** use gridMET as the canonical source for the first monthly
Fourier/EOF coefficients. Retain it as an optional daily-sequencing or
operational-forcing sensitivity. In the classic retrospective construction,
gridMET's monthly precipitation totals and monthly Tmax/Tmin means are derived
from PRISM; NLDAS-2 principally supplies the within-month daily sequence.
gridMET therefore adds little independent information for the proposed
monthly interannual coefficient surface.

This recommendation is specific to the A5b experiment. It does not mean that
Daymet is universally superior for every weather-data use, nor that a Daymet
grid cell is point-observation truth.

### Evidence convention

Product spans, domains, construction methods, calendars, revision practices,
and use conditions below are documented facts from the cited provider records
and primary papers. Rankings, statements about suitability for A5b, and
proposed safeguards are project inferences from those facts and the fixed A5
contract. Comparative findings from Diem (2026) are labeled and bounded to
that study's southeastern-US precipitation design.

### Why Daymet wins this decision

1. It exactly spans the frozen **1980–2009** fitting window, providing 30
   annual vectors. PRISM daily starts in 1981.
2. It covers all **17 A5 stations**, including the Alaska station. PRISM and
   the standard gridMET archive cover only the 16 CONUS stations.
3. The repository already contains the exact 17 daily source extracts,
   archived and SHA-256 bound by A5a. No live upstream response is needed for
   the experimental fit.
4. The product has a numbered release, dataset DOI, public data-use statement,
   primary method paper, and a station-level cross-validation product currently
   extending through 2023.
5. Its 1-km, terrain-aware, station-based P/Tmax/Tmin surface is compatible
   with the current station-local A5 design.
6. Its weaknesses are material but governable: changing station networks,
   gridded interpolation, a nonstandard 365-day calendar, append-only updates
   under the same version label, and shared GHCN lineage with one A5
   sensitivity.

The most important caution is that **same-product fitting and evaluation can
favor Daymet-specific structure**. The 1980–2009/2010–2025 split prevents
direct future-data leakage, but it does not make the held-out Daymet target
independent of the fitted product family. The pre-registered GHCN comparison
must remain, and a PRISM fit-source sensitivity is the best next method-level
check among the three products.

## What is being selected

The source is being selected for a sequence like:

1. read complete daily P/Tmax/Tmin years;
2. apply a frozen calendar and monthly aggregation;
3. form one annual monthly anomaly vector per year;
4. transform that vector into a predefined Fourier representation;
5. estimate a low-rank covariance/EOF representation; and
6. serialize zero-mean interannual parameters with complete source and fit
   provenance.

This is not the same decision as selecting:

- the observed target used to score generated climate;
- a source for real-time weather forcing;
- the best product for daily extremes or storm timing;
- a replacement for the existing `.par` monthly climatology;
- the coefficient estimator, retained rank, generation profile, or output
  format.

Those identities must remain independent.

## Fixed A5 context

The existing A5 record fixes:

- primary held-out target: Daymet V4 R1, 2010–2025;
- fitting period: 1980–2009 only;
- source sensitivities: full-period/raw-versus-detrended Daymet and available
  GHCN station records, never pooled;
- 17 stations, comprising 16 CONUS locations and one Alaska location;
- the same station set, horizons, burn trajectories, extension seeds, and
  quality vector for each candidate; and
- no candidate-output inspection before identifiers, estimators, constraints,
  and failure rules are frozen.

The source decision here preserves those constraints. A PRISM fit beginning in
1981, a 16-station CONUS comparison, or any changed calendar interpretation is
a separately labeled sensitivity and requires a prospective contract amendment
before candidate output. It cannot silently replace the primary matrix.

## Product comparison

| Property | Daymet V4 R1 | PRISM AN daily | gridMET |
|---|---|---|---|
| Current daily span | 1980–2025 for continental North America and Hawaii; Puerto Rico 1950–2025 | 1 Jan 1981–yesterday | 1979–yesterday |
| Standard domain | Continental North America, Hawaii, Puerto Rico as separate domains | CONUS | CONUS; a separate real-time extension reaches southern British Columbia |
| A5 station coverage | **17/17** | **16/17**; no Alaska daily series | **16/17**; no Alaska |
| A5 fit years | **30/30** | **29/30** | **30/30** |
| Spatial grid | 1 km | approximately 800 m native; 4 km also published | 1/24 degree, approximately 4 km |
| P/T source character | GHCN-Daily station interpolation with variable-specific station lists and terrain-aware regression | all available station networks; CAI with physiographic weighting; radar enters central/eastern precipitation from 2002 | PRISM supplies monthly P/T constraints; NLDAS-2 supplies within-month daily anomalies/sequencing in the classic construction |
| Day convention | target is local midnight-to-midnight, with source-dependent time-of-observation corrections | 1200–1200 UTC, labeled by ending date | nominally midnight-to-midnight Mountain Standard Time, ending approximately 07 UTC |
| Calendar | 365 records every year; leap years retain 29 Feb and omit 31 Dec | dated Gregorian archive including leap days | Gregorian time coordinate |
| Low-frequency suitability | direct 30-year fit, but station-network evolution and spatial smoothing can alter covariance | explicit best-estimate-over-consistency design; no daily long-term-consistency product | monthly EOFs are largely PRISM-derived, so it is not an independent low-frequency source |
| Release identity | V4 R1 / 4.1 and DOI; recent years can be appended without changing 4.1 | active D2 analyses; mutable rolling product, nominally stable after eight releases over six months | living semi-operational product; no numbered dataset release or dataset DOI |
| Reproducibility | strong only when exact objects, end year, coordinates, and hashes are pinned | requires exact grid packages, metadata, archive timestamps, access date, hashes, and update status where available; the update-count service does not cover 1981–2009 | requires exact NetCDF bytes and metadata hashes |
| Public reuse | official catalog states openly shared without restriction; cite product and extraction tool | general terms permit reproduction/distribution with attribution, but the 800-m ordering page strictly prohibits commercial use without advance arrangements; clarification is required for production use | CC0 waiver on official product page |
| A5b role | **primary fit source** | **first CONUS sensitivity** | optional daily-sequence/forcing diagnostic, not first monthly coefficient source |

## Dataset assessments

### 1. Daymet V4 R1 — recommended primary

#### Construction and coverage

Daymet provides daily precipitation, 2-m Tmax, and 2-m Tmin on a 1-km grid.
The current V4 R1 guide covers continental North America and Hawaii from 1980
through 2025 and Puerto Rico from 1950 through 2025. Continental North America
includes Alaska, Canada, the conterminous United States, and Mexico. The
product is distributed in separate geographic domains.

The primary inputs are GHCN-Daily stations. Daymet selects station-years and
station lists independently by variable, constructs a variable-specific search
radius and distance weighting for each grid cell, and estimates temperature
with daily three-dimensional regressions that include elevation and horizontal
gradients. Precipitation has separate occurrence and amount procedures. These
methods make Daymet attractive for sparse and complex terrain, but they also
mean that P/T covariance at a cell is the covariance of a modeled grid
estimate, not an observed station record.

The V4 method paper documents changes in station density through time,
including rapid precipitation-station growth after 2000 and more recent
temperature-station declines. Station lists can change at year boundaries.
Consequently, an EOF can contain both real climate structure and source-network
evolution.

#### Fit-period provenance

The current guide records one GHCN-Daily snapshot lineage for 1980–2019. That
makes 1980–2009 a comparatively coherent release block, although the stations
available within the snapshot still vary by station-year. Later held-out years
span multiple GHCN snapshots. Daymet R1 also replaced 2020 and 2021 fields
after missing Canadian January observations were corrected.

This asymmetry is acceptable for an out-of-time stress test and is already
part of the A5a target. It reinforces the need to keep the fitter physically
restricted to 1980–2009 and to report performance by held-out subperiod as a
report-only diagnostic. Frozen adjudication remains over the complete
2010–2025 held-out period.

#### Cross-validation and independence

Daymet publishes station-level input and leave-one-out prediction records for
P/Tmax/Tmin through 2023. This can help diagnose grid-estimate error and
elevation mismatch, but the records are at Daymet input-station locations, not
arbitrary A5 pixels. A5b must establish explicit station-ID/location matching
before using them for an A5 diagnostic, and 2024–2025 currently lack companion
cross-validation. The product is not validation of a joint 36-component
monthly covariance matrix or its EOF eigenvalues; A5b must construct that
diagnostic explicitly if it wants it.

The A5 GHCN sensitivity is valuable as a **point-record versus gridded-product
sensitivity**, but it is not an independent observing system: GHCN-Daily is
Daymet's primary station input. The report and later A5 analysis should avoid
calling the Daymet/GHCN comparison statistically independent.

#### Calendar and A5 normalization

The official Daymet calendar has 365 records in every year. In leap years it
retains 29 February and discards 31 December. The archived single-pixel files
provide `year` and ordinal `yday`, not a civil date.

A5a currently converts every `yday` through a fixed no-leap calendar. In a
leap year, that normalization labels the official 29 February value as 1 March
and shifts monthly membership at subsequent month boundaries through the end
of the year. This is a deterministic, versioned A5 target convention; it is
not identical to the official Daymet civil-date interpretation.

Before a production coefficient fit, A5b must name a
`calendar_transform_id`. The least disruptive primary path is:

- reproduce the existing A5a no-leap transform exactly for the fixed primary
  comparison; and
- add a report-only official-calendar aggregation sensitivity, with no
  imputation of the absent 31 December.

If the official calendar is to replace the current primary convention, the A5
specification, corpus, hash pins, and baseline must be revised prospectively
before any candidate output. This report does not make that change.

#### Release and reuse

Daymet has a dataset DOI and a numbered V4 R1/4.1 identity, but the version
label alone is not an immutable content identifier. ORNL has appended later
years while retaining 4.1, and R1 demonstrates that historical correction can
occur. Production fitting must therefore bind exact bytes, product end year,
access date, extraction metadata, and hashes.

The official catalog states that the dataset is openly shared without
restriction under NASA Earthdata guidance. The repository already carries a
third-party notice and canonical citations for the A5a extracts. Derived
coefficient files should retain those citations and must not imply that the
repository's Apache-2.0 license relicenses the source data.

#### A5b consequence

Daymet is the only product of the three that can run the fixed primary fit
without a coverage or period exception. Its source-specific structure must be
measured rather than ignored, but its limitations do not prevent a controlled
A5b fit.

### 2. PRISM AN daily — recommended CONUS sensitivity

#### Construction and strengths

PRISM provides daily precipitation, Tmax, and Tmin for CONUS from 1 January
1981. It uses climatologically aided interpolation and weights stations by
physiographic similarity. The approximately 800-m product is particularly
attractive for terrain localization; a 4-km product is also available.

For daily precipitation, the current D2 product uses CAI throughout the record
in the West. Central and eastern CONUS use CAI for 1981–2001 and a CAI/radar
hybrid from 2002 onward. Daily and monthly precipitation are reconciled: in
mountainous western areas the daily values are percentage-adjusted to the
monthly total and, in limited cases, wet days can be added. These operations
are beneficial for monthly water balance but show why the daily series is a
modeled product rather than untouched gauge interpolation.

#### Temporal-consistency mismatch

PRISM's current documentation explicitly distinguishes `AN` from its monthly
`LT` product. `AN` uses all available networks to obtain the best estimate at
each time step, at the expense of temporal consistency. There is no daily LT
product. PRISM also warns about inhomogeneities from equipment and station
changes, network openings/closures, observation-time differences, and product
revisions.

That design is excellent for reconstructing a particular day's local weather,
but it is a direct risk for a low-frequency covariance estimator: method and
network transitions can appear as eigenmodes. The 2002 precipitation-method
change falls inside the A5 fit window.

The available full record has additional documented seams outside that fit:
`AN81d` uses Norm81m predictors through 2020, while `AN91d` begins in 2021 with
Norm91m predictors and later M4-normal changes affect data from July 2022.
Precipitation radar guidance also changed from Stage 2 to MRMS in July 2020.
These do not affect a 1981–2009 sensitivity, but they require explicit
diagnostics before any post-promotion full-record refit.

#### A5 incompatibilities

PRISM daily misses:

- 1980, leaving 29 rather than 30 fit years; and
- the Alaska station, leaving 16 rather than 17 A5 stations.

Substituting monthly PRISM for 1980 and daily PRISM afterward would mix product
surfaces and is not recommended. A clean PRISM sensitivity should instead use
1981–2009 at the 16 CONUS stations and be labeled non-primary. That design must
be fixed before candidate output because it differs from the pre-registered
period and corpus.

#### External temporal-stability evidence

A 2026 peer-reviewed comparison examined precipitation products across the
southeastern United States from 1980–2024. It detected product-specific
inhomogeneities, with the principal PRISM AN discontinuity centered on 2002,
the Daymet discontinuity on 2012, and the gridMET discontinuity on 2016. It
also found that changing station networks affected Daymet and PRISM AN trends.

That study is regional, precipitation-only, and evaluates temporal consistency
rather than local multivariate covariance or day-level accuracy. It does not
prove one national product is best. It does provide direct evidence that the
source-transition concern is observable and that every fitted source needs
stability diagnostics.

#### Release and reuse

PRISM remakes a current daily grid several times and calls it stable after the
eighth release, roughly six months after the date, subject to later major
reanalysis. The release-date/update-count service begins in April 2014 and
cannot establish update count for the proposed 1981–2009 sensitivity. That
historical fit must instead bind exact D2 archive bytes, metadata, archive
modification timestamps, access date, and hashes, while recording update
status as unavailable.

Current general terms allow website data to be reproduced and distributed
with PRISM name, URL, and access date while PRISM retains copyright. The
current 800-m ordering page separately states that commercial use is strictly
prohibited without advance arrangements. Because those statements are not a
clear production-use grant when read together, obtain written PRISM
clarification before commercial or WEPPcloud production use or redistribution
of PRISM-derived production coefficients.

#### A5b consequence

PRISM is scientifically useful because it changes the interpolation method,
terrain treatment, day definition, and product lineage relative to Daymet. It
is the best of these three for a source-method sensitivity, but it cannot
replace the fixed primary fit without changing the experiment.

### 3. gridMET — not recommended as the first monthly source

#### Construction

gridMET is a daily, approximately 4-km CONUS product from 1979 to yesterday.
It blends PRISM's spatial fields with regional-reanalysis temporal information.
In the founding retrospective method:

- daily precipitation is the NLDAS-2 fraction of a month's precipitation,
  multiplied by that grid cell's PRISM monthly total; and
- daily Tmax and Tmin are NLDAS-2 daily departures from their monthly means,
  added to the corresponding PRISM monthly means.

Thus a monthly annual vector of precipitation totals and Tmax/Tmin means is
primarily a PRISM-derived vector. NLDAS-2 determines the daily ordering and
within-month anomalies. A monthly covariance or EOF fit to gridMET should not
be described as an independent blend of PRISM and NLDAS low-frequency
information.

#### Strengths

gridMET does cover the complete 1980–2009 fit period, and that period is
especially favorable because it sits within the original 1979–2010
retrospective construction. The product has a broad daily meteorological
variable set, easy NetCDF access, a documented nominal day ending at
approximately 07 UTC, and an explicit CC0 waiver.

These strengths make gridMET useful for later daily sequencing, energy
balance, fire-weather, or operational forcing studies. They do not add an
independent monthly interannual target for the first P/T Fourier/EOF model.

#### Limitations

The standard archive excludes Alaska. The product is living and
semi-operational rather than a numbered release. Its official documentation
records changed near-real-time sources, historical reprocessing, format/grid
changes, and inhomogeneities inherited from changing NLDAS-2 precipitation
inputs. It explicitly cautions users about precipitation intensity and
frequency trends.

Those daily-source changes matter most if the model fits wet-day ordering,
spell structure, or storm descriptors. For monthly aggregates, the larger
issue is simpler: gridMET largely duplicates PRISM's monthly signal at coarser
resolution and with a more complex lineage.

#### A5b consequence

Do not spend the first A5b implementation budget on a gridMET monthly fit. If a
later candidate uses daily anomalies or conditional sequencing, gridMET can be
added with exact 1980–2009 NetCDF byte pins, source-break diagnostics, and an
explicit CONUS-only scope.

## Statistical feasibility independent of source choice

The frozen fit provides only 30 annual vectors for Daymet and gridMET and 29
for a clean PRISM daily fit. If the uncompressed feature vector contains 12
months for each of P, Tmax, and Tmin, it has 36 dimensions.

After centering:

- a 30-year sample covariance has rank at most 29; and
- a 29-year PRISM covariance has rank at most 28.

An unconstrained 36 × 36 sample covariance is therefore singular by
construction. Higher spatial resolution or a different source cannot solve
this. A production Fourier/EOF contract must predeclare:

- monthly feature definitions and precipitation transformation;
- Fourier basis, normalization, and retained harmonics;
- detrending rule and whether raw and detrended fits are separate artifacts;
- covariance estimator and any shrinkage or regularization;
- positive-semidefinite repair and tolerance;
- retained EOF rank and explained-variance reporting;
- deterministic eigenvalue ordering and eigenvector sign convention;
- tie handling and numerical precision;
- fit failure rules; and
- reconstruction-error and coefficient-stability diagnostics.

Held-out performance cannot choose these rules after the fact.

## Recommended A5b source contract

### Primary fit

| Field | Recommendation |
|---|---|
| Product | Daymet V4 R1 / dataset version 4.1 |
| Dataset DOI | `10.3334/ORNLDAAC/2129` |
| Input objects | the 17 already archived `references/observed/a5a-v1/daymet/*.csv.gz` objects |
| Variables | `prcp`, `tmax`, `tmin` in source units |
| Fit period | 1980–2009 inclusive, enforced by the fitter |
| Held-out exclusion | the fitter must reject or ignore records after 2009 by explicit contract; no fitted quantity may depend on 2010–2025 |
| Spatial selection | requested coordinates plus returned x/y, tile, grid elevation, and software version are present in each hash-pinned CSV header; A5b must parse, validate, and promote them into structured coefficient lineage; no silent lapse-rate or interpolation adjustment |
| Calendar | exact A5a no-leap transform for the primary comparison, with a separately named official-Daymet-calendar sensitivity |
| Missingness | fail closed on a missing day, nonfinite value, sentinel, duplicate ordinal day, or incomplete year |
| Source identity | source-object SHA-256, retrieval date, product end year, header versions, and canonical citations |
| Output | zero-mean interannual coefficient payload; do not replace existing `.par` monthly means unless a separate candidate explicitly studies that change |

The fitter should open only the fit-period slice or enforce a maximum accepted
year before it computes any statistic. Merely promising not to use later rows
is weaker than a structural read boundary.

### Sensitivities

1. **Existing GHCN sensitivity:** preserve it and label it point-record versus
   grid-product evidence, not independent upstream data.
2. **PRISM source sensitivity:** if adopted before output, fit stable D2 800-m
   P/Tmax/Tmin grids for 1981–2009 at the 16 CONUS stations. Record the changed
   period/domain and test 4-km extraction as a resolution diagnostic.
3. **gridMET:** defer unless A5b adds a question about daily sequencing. If
   used, freeze the classic 1980–2009 annual NetCDF files and verify monthly
   aggregates against their PRISM constraints.

Products must never be pooled into one fit merely to fill coverage. A missing
product/station combination remains explicitly unavailable.

## Production-ready coefficient provenance

Every coefficient payload or content-addressed sidecar should bind at least:

### Source lineage

- source product, DOI where available, version/release, product end date, and
  retrieval date;
- raw object URL or acquisition endpoint and SHA-256;
- requested station coordinates and elevation;
- returned grid centroid/tile, grid elevation, separation, and extraction
  rule;
- variables, units, fill values, scale/offset decoding, calendar, and day
  boundary;
- fit period and an explicit held-out exclusion; and
- provider citation, attribution, and third-party-data notice.

### Fit lineage

- coefficient-payload schema version;
- fit-recipe ID and implementation commit;
- feature order and monthly aggregation transform ID;
- precipitation and temperature transforms;
- detrending model and training-only normalization;
- Fourier basis convention and retained harmonics;
- covariance/regularization method and parameters;
- EOF eigenvalues, loadings, deterministic sign/order convention, and retained
  rank;
- explained variance, reconstruction error, and any PSD correction;
- fit warnings/failures and usable-year count; and
- canonical serialized-payload SHA-256.

### Independent version axes

| Identity | What it versions |
|---|---|
| station-file schema | syntax and structural validation of the augmented station file |
| station-model ID | scientific meaning of the station parameters |
| coefficient-payload schema | names, shapes, units, and invariants of coefficients |
| fit-recipe ID | transforms, estimator, regularization, and deterministic conventions |
| source-snapshot ID | product/version/period/cells and raw hashes |
| generation-profile ID | runtime behavior consuming the payload |
| output/provenance schema | serialized run identity and downstream evidence |

Advancing one identity must not silently advance the others. In particular, a
new Daymet annual append does not automatically change a station-model ID, and
a coefficient refit does not change the station-file grammar unless the
payload structure changes.

## Meaning of “production ready” during A5b

A5b should use the **production serialization and deterministic fitting
pipeline** while retaining the 1980–2009 experimental split. That makes the
files operationally realistic without contaminating evaluation.

If A5c later promotes a model, a deployment fit may use a longer stable record.
That refit must receive a new source-snapshot and coefficient-content identity
and cannot be used to revise the already completed A5b score. “Production
ready” must not become a reason to fit through the held-out years before the
model is selected.

An augmented station file also requires a declared extension model. The legacy
`.par` contract must remain unchanged, and faithful generation must not
silently consume or ignore an unversioned coefficient appendix. Whether the
modern station file embeds coefficients or references a content-addressed
sidecar belongs in the later interface specification.

## Required gates before the first candidate run

### Source and preprocessing

- all 17 primary source hashes match the A5a manifest;
- each station has 30 complete fit years and no post-2009 contribution;
- station-to-cell identity matches the archived extraction metadata;
- units, ordinal days, and finite values validate with fail-closed behavior;
- the named calendar transform reproduces a golden monthly vector;
- raw versus detrended artifacts have separate IDs and hashes; and
- a source-lineage manifest rebuilds byte-for-byte.

### Coefficient numerics

- feature ordering and Fourier reconstruction pass golden vectors;
- covariance is symmetric within a stated tolerance;
- all accepted eigenvalues satisfy the PSD tolerance;
- retained-mode ordering/sign conventions reproduce byte-identically across
  repeated fits;
- singular/rank-deficient inputs follow the predeclared regularization path;
- parameter counts, retained variance, and reconstruction error are reported;
  and
- mutation tests catch transposed variables, reordered months, altered source
  hashes, a post-2009 row, and changed eigenvector signs.

### Station file and runtime

- the new station schema is specified before implementation and registered in
  `docs/specifications/README.md`;
- faithful/legacy files and output remain byte-identical;
- extension files declare station-model, payload, fit, source, and profile
  identities;
- malformed or missing coefficients fail closed; and
- any new production functions pass the repository format, clippy, test,
  coverage, and CRAP gates.

## Work required for A5b

| Work item | Effort/risk | Result |
|---|---|---|
| Ratify calendar treatment | small implementation, high semantic importance | one primary transform ID and one optional sensitivity ID |
| Freeze feature/fit contract | medium, high statistical importance | prospective Fourier/EOF estimator and failure rules |
| Reuse A5a Daymet inputs | small | offline, hash-verified 17-station fit corpus |
| Implement deterministic fitter | medium | source-limited, repeatable coefficient payloads and diagnostics |
| Specify augmented station surface | medium | independently versioned schema/model/payload contract |
| Integrate extension profile | medium-to-large | explicit runtime behavior without faithful-stream perturbation |
| Execute A5b climate matrix | large but already bounded | fixed multi-station/horizon/replicate comparison |
| Add PRISM sensitivity | medium plus acquisition/licensing work | 16-station, 1981–2009 method-level robustness check |
| Add gridMET sensitivity | low-to-medium acquisition; low first-study value | daily-sequencing evidence only if required |

The source decision removes the need for new primary-data acquisition. The
statistical contract and extension interface, not downloading Daymet, are the
critical path.

## Pre-fit decisions for the A5b scaffold

The A5b kickoff should resolve these before any candidate climate is generated:

1. ratify the primary calendar transform and whether the official Daymet civil
   calendar is a report-only sensitivity;
2. freeze the exact monthly feature vector and precipitation transform;
3. freeze Fourier harmonics, covariance regularization, EOF rank, and
   deterministic conventions;
4. choose embedded payload versus content-addressed sidecar for the modern
   station surface;
5. decide whether the PRISM 16-station/1981–2009 sensitivity warrants a
   prospective A5 contract amendment; and
6. state that any post-promotion full-record refit is a new production artifact,
   not A5b evidence.

None of these decisions requires changing faithful CLIGEN.

## Sources

Sources were accessed 2026-07-13. Product-page dates and spans below reflect
the current official records, which can change after this report.

### Daymet

- Thornton, M. M., Shrestha, R., Wei, Y., Thornton, P. E., and Kao, S.-C.
  (2022). *Daymet: Daily Surface Weather Data on a 1-km Grid for North America,
  Version 4 R1*. ORNL DAAC. DOI:
  [10.3334/ORNLDAAC/2129](https://doi.org/10.3334/ORNLDAAC/2129).
- [Official Daymet V4 R1 daily-data guide](https://daac.ornl.gov/DAYMET/guides/Daymet_Daily_V4R1.html),
  documentation revision 2026-05-22.
- Thornton, P. E., Shrestha, R., Thornton, M., Kao, S.-C., Wei, Y., and
  Wilson, B. E. (2021). *Gridded daily weather data for North America with
  comprehensive uncertainty quantification*. DOI:
  [10.1038/s41597-021-00973-0](https://doi.org/10.1038/s41597-021-00973-0).
- Thornton, M. M., Shrestha, R., Wei, Y., Thornton, P. E., and Kao, S.-C.
  (2022). *Daymet: Station-Level Inputs and Cross-Validation for North America,
  Version 4 R1*. DOI:
  [10.3334/ORNLDAAC/2132](https://doi.org/10.3334/ORNLDAAC/2132).
- Thornton, M. M. and Devarakonda, R. (2011). *Daymet Single Pixel Extraction
  Tool*. DOI:
  [10.3334/ORNLDAAC/2361](https://doi.org/10.3334/ORNLDAAC/2361).
- [NASA Earthdata Data Use and Citation Guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance).

### PRISM

- PRISM Climate Group. [PRISM time-series data](https://prism.oregonstate.edu/data/).
- PRISM Climate Group. [*Descriptions of PRISM Spatial Datasets for the
  Conterminous United States*](https://prism.oregonstate.edu/documents/PRISM_datasets.pdf),
  revised February 2026.
- PRISM Climate Group. [Terms of use](https://prism.oregonstate.edu/terms/),
  [800-m availability and ordering terms](https://prism.oregonstate.edu/orders/),
  and [known-data-issues ledger](https://prism.oregonstate.edu/issues/).
- Daly, C., Halbleib, M., Smith, J. I., Gibson, W. P., Doggett, M. K.,
  Taylor, G. H., Curtis, J., and Pasteris, P. P. (2008). *Physiographically
  sensitive mapping of climatological temperature and precipitation across the
  conterminous United States*. DOI:
  [10.1002/joc.1688](https://doi.org/10.1002/joc.1688).
- Daly, C., et al. (2021). *Challenges in observation-based mapping of daily
  precipitation across the conterminous United States*. DOI:
  [10.1175/JTECH-D-21-0054.1](https://doi.org/10.1175/JTECH-D-21-0054.1).

### gridMET and comparative evidence

- Climatology Lab. [Official gridMET documentation, access, update history,
  caveats, and CC0 notice](https://www.climatologylab.org/gridmet.html).
- Abatzoglou, J. T. (2013). *Development of gridded surface meteorological
  data for ecological applications and modelling*. DOI:
  [10.1002/joc.3413](https://doi.org/10.1002/joc.3413).
- NASA Land Data Assimilation Systems.
  [NLDAS-2 forcing documentation](https://ldas.gsfc.nasa.gov/nldas/v2/forcing).
- Diem, J. E. (2026). *Temporal inhomogeneities in high-resolution gridded
  precipitation products for the southeastern United States*. DOI:
  [10.5194/hess-30-1999-2026](https://doi.org/10.5194/hess-30-1999-2026).
