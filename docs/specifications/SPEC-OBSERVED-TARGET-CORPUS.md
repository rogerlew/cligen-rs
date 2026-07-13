# SPEC-OBSERVED-TARGET-CORPUS — A5 Observed Climate Targets

Status: active (revision 1)
Surface: `observed-target-corpus-v1.json`, validated by
`observed-target-corpus-v1.schema.json`

## Purpose and version boundary

This specification defines the observed climate target used to compare A5
candidate generators. It is external to station parameters and external to
each generated quality report. Its `observed_target_corpus_schema_version` is
independent of the station-file schema, station-model identifier, generation
profile, output schema, provenance schema, quality-report envelope, and
quality metric-vector version.

The corpus contains observations and derived evaluation targets. It never
contains fitted latent parameters and never activates generation behavior.

## Corpus revision 1

Revision 1 retains the ratified Q3 17-station `us-2015` regime corpus:

- four arid, four North American monsoonal, four humid, four cold, and the
  New Meadows fixture cross-link;
- the exact station parameter file and station-collection payload identities;
- coordinates and elevation from the pinned `us-2015` catalog;
- primary Daymet V4 R1 daily precipitation, Tmax, and Tmin;
- secondary GHCN-Daily precipitation, Tmax, and Tmin when available.

Daymet is a 1-km gridded estimate and GHCN-Daily is point-station data. They
remain separate target products; disagreement is reported and never averaged
away. Neither supplies duration, time-to-peak, peak-ratio, radiation, wind,
dew point, snowpack, soil frost, runoff, or erosion truth.

## Source identity and archival

Every source object records:

- dataset name/version/DOI and exact retrieval URL;
- retrieval date and requested coordinates or station identifier;
- source-byte SHA-256, archived-byte SHA-256, media type, compression, and
  byte length;
- logical SHA-256 of the normalized records inside the fixed evaluation
  window;
- calendar, variables, units, missing-value and quality-flag rules.

Revision 1 archives the exact source bytes under
`references/observed/a5a-v1/`. Daymet CSV is deterministically gzip-compressed
for the repository; both its original CSV hash and archived gzip hash are
recorded. GHCN source objects are retained byte-for-byte in their supplied
gzip representation. Mutable upstream URLs are locators, not identities.

The manifest binds source hashes to the acquisition script hash, target
builder hash, schema hash, and final target-corpus hash. A future upstream
refresh creates a new corpus revision; it does not rewrite revision 1.
The archive documentation and third-party data notice are also hash-bound.
The repository license does not relicense the archived provider data.

## Fixed periods

All revision-1 Daymet products use these closed bounds regardless of data
that upstream may later append:

| Product | Inclusive years | Use |
|---|---:|---|
| `full` | 1980–2025 | descriptive and sensitivity target |
| `fit` | 1980–2009 | candidate fitting only |
| `evaluation` | 2010–2025 | held-out promotion evidence |

GHCN records are restricted to the same bounds. A product is `unavailable`
rather than silently widening its period or filling a missing variable.

## Intake and completeness

- Daymet uses its native 365-day no-leap calendar. Day-of-year 1–365 maps to
  fixed month lengths with February 28 days.
- GHCN uses the proleptic Gregorian date carried by each record. Records with
  a nonblank GHCN quality flag are excluded. Duplicate station/date/element
  records fail the build.
- No missing daily value is imputed. Monthly totals/means require every
  expected source-calendar day for the relevant variable. A complete aligned
  month requires precipitation, Tmax, and Tmin together; a complete aligned
  year requires twelve complete aligned months.
- Univariate precipitation structure may use a complete precipitation span
  when temperatures are absent. A gap terminates a spell and is reported; it
  is never bridged.
- Every metric carries the actual sample size or availability reason.

## Wet-day and temperature conventions

Observed-comparison precipitation metrics use `precipitation_mm >= 1.0`, the
ETCCDI R1mm threshold fixed by Q3. This differs deliberately from Group A's
legacy station-contract predicate (`printed precipitation > 0`). Metrics v3
reports both predicates so the observed join is direct.

Mean air temperature is `(Tmax + Tmin) / 2`. A freezing-air day satisfies
mean air temperature `<= 0 °C`. A freeze/thaw proxy transition occurs when
consecutive available daily mean-air states move between `<= 0 °C` and
`> 0 °C`. It is explicitly an air-temperature proxy, not a rain/snow phase
model, snowpack state, or soil freeze/thaw state.

## Derived target families

For each available source and fixed period, revision 1 derives:

1. annual precipitation total, wet-day count, annual maximum 1-day
   precipitation, and annual mean Tmax/Tmin dispersion;
2. by-calendar-month precipitation-total mean/SD/CV, wet-day-count
   dispersion, wet-day-mean-amount dispersion, and monthly-mean Tmax/Tmin
   mean/SD;
3. cross-month precipitation/Tmax/Tmin anomaly covariance and correlation,
   per-month precipitation–Tmax, precipitation–Tmin, and Tmax–Tmin anomaly
   correlations, annual lag-one correlations, and the metrics-v3
   low-frequency power fraction;
4. R1mm wet/dry spell distributions across month/year boundaries, adjacent
   wet-day amount dependence, wet-day amount distribution, and annual 1/3/5
   day rolling maxima;
5. precipitation fraction on freezing-air days, winter precipitation/mean-
   air-temperature dependence, and air-temperature freeze/thaw proxy counts.

Duration/time-to-peak/peak-ratio targets are marked unavailable. They require
a later breakpoint or subhourly observed corpus and must not be inferred from
daily Daymet/GHCN data.

## Estimators and trends

Estimator definitions are identical to SPEC-QUALITY-REPORT metrics v3:
row-order f64 accumulation, n−1 sample SD/covariance, average-rank Spearman,
and the pinned empirical quantile. Targets carry both raw and OLS-linearly
detrended annual/monthly anomaly sensitivities. Raw values are primary; a
trend is not silently removed.

The low-frequency target calls the same Rust metrics-v3 estimator as generated
reports. Its trigonometric operations use the Cargo-locked `libm` crate. The
corpus manifest binds the helper and estimator source, Cargo inputs, Rust
toolchain file, module wiring, exact compiler identity, and exact `libm`
version/checksum; Python and host-platform metadata are informational
provenance rather than numerical authority.

The target document records point estimates and sample sizes. Campaign
uncertainty is produced from the archived annual vectors by the fixed
resampling procedure in SPEC-A5-EVALUATION; a burn spread is never labeled an
IID confidence interval.

## Canonical bytes

The builder emits UTF-8 JSON with two-space indentation, lexicographically
ordered object keys, shortest round-trippable finite JSON numbers, and one
trailing newline. No timestamp from the build host and no absolute path enters
the target. Rebuilding from the archived sources and pinned builder must be
byte-identical.

## Failure behavior

The builder fails closed on a source/archive hash mismatch, duplicate record,
unknown unit/calendar/variable, out-of-domain value, missing required Daymet
day, station-coordinate mismatch, unsupported schema version, non-finite
result, or target/schema validation failure. Missing optional GHCN coverage is
represented explicitly and is not a build failure.
