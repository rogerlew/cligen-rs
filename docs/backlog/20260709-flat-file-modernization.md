# Flat-File Modernization: `.par.yaml` and `.cli.parquet`

Status: Backlog design proposal
Date: 2026-07-09
Owner: cligen-rs
Target roadmap items: A1 (provenance and `.cli.parquet`), A4 (parameter
database and mutation utilities), with enabling work after faithful-mode port
closure

## Summary

Modernize CLIGEN's public file surfaces without weakening the faithful port:

- introduce `.par.yaml` as the canonical human-authored, schema-versioned
  station-parameter representation;
- support explicit `si-v1` and `cligen-legacy-v1` parameter unit profiles,
  including SI names such as `mean_daily_mm`;
- introduce `.cli.parquet` as the canonical typed, analytical climate-series
  representation;
- retain the legacy `.par` reader/canonical writer and `.cli` reader/writer
  indefinitely as frozen compatibility adapters;
- use the same typed domain models behind legacy and modern formats so format
  support cannot create two generator semantics;
- have cligen-rs own the `.cli.parquet` specification for both parametric and
  breakpoint precipitation, even though the pinned CLIGEN 5.32.3 Fortran
  neither generates nor consumes breakpoint climate records.

The modern formats are augmentations, not part of reference-source fidelity.
Faithful generation remains defined by the vendored Fortran and continues to
prove itself through legacy `.par` inputs, byte-identical legacy `.cli`
outputs, and full-stream fixture gates. Modern-format paths must project onto
the same typed inputs and outputs and demonstrate equivalent behavior.

The names are intentional:

- `station.par.yaml` identifies both the CLIGEN parameter domain and YAML
  syntax;
- `run.cli.parquet` identifies both the CLIGEN/WEPP climate domain and Parquet
  storage;
- Parquet bytes must never be written under a bare `.cli` extension, because
  `.cli` has an established meaning as formatted text.

## Motivation

The legacy formats are effective machine interfaces but poor long-term data
contracts.

The `.par` format is fixed-column text whose semantics depend on record number,
column position, implied-DO ordering, skipped fields, and legacy Fortran
blank/decimal behavior. It has no schema identifier or provenance surface.
Humans can read individual values, but comparing related monthly values or
reviewing a mutation requires knowledge of the record layout.

The `.cli` format combines file metadata, monthly climatology, and a daily
table in one formatted stream. In breakpoint mode, a daily record is followed
by a variable number of two-column records, so the file is not a rectangular
table. Units are present only in human-readable headers, provenance is largely
embedded in free text, and downstream tools repeatedly implement custom
parsers.

The intended outcomes are:

- explicit, versioned schemas;
- unit-bearing field names and documented nullability;
- fail-closed parsing and validation;
- compact month-to-month review of station parameters;
- efficient projection, filtering, compression, and aggregation of climate
  series;
- first-class provenance and generation-profile identification;
- lossless representation of breakpoint hyetographs;
- direct Arrow-compatible interchange for Rust, Python, R, DuckDB, Polars,
  and similar consumers;
- continued operation of existing WEPP and CLIGEN workflows.

## Authority and ownership boundaries

### Faithful generator behavior

[ADR-0001](../decisions/0001-source-code-authority-port.md) remains
normative. `reference/cligen532/cligen.f` defines faithful computation,
precision, RNG consumption, legacy `.par` intake, and legacy `.cli` rendering.
Neither YAML nor Parquet can redefine faithful generator behavior.

The Fortran writes the WEPP climate header's breakpoint position but always
sets the flag to zero. It has no `nbrkpt`, `timem`, or `pptcum` data path and
always writes parametric `prcp/dur/tp/ip` daily records. Its lone comment about
calibration "based on break-point data" documents an empirical constant, not
breakpoint file support.

Consequently:

- faithful CLIGEN output has `precipitation_representation = parametric`;
- faithful output has null breakpoint lists;
- breakpoint import/export is an interoperability extension;
- any future breakpoint *generation* algorithm requires a separately
  versioned generation profile and scientific specification.

### Modern format ownership

cligen-rs owns and versions:

- the `.par.yaml` schema and canonical YAML rendering;
- the `.cli.parquet` physical and logical schema;
- the mapping between modern formats and cligen-rs typed models;
- the legacy-to-modern and modern-to-legacy conversion contracts;
- breakpoint representation, validation, and conversion in
  `.cli.parquet`;
- provenance keys required of cligen-rs outputs.

This ownership makes cligen-rs the schema authority, not the scientific
authority for every producer represented in the schema. Imported breakpoint
files retain their producer and source-format lineage. WEPP's interpretation
of a breakpoint hyetograph remains governed by the relevant WEPP contract;
cligen-rs specifies how those source values are represented and validated in
Parquet.

Cross-repository implementation belongs to each repository, but the target
roles are fixed here:

- cligen-rs specifies `.cli.parquet` and produces it directly;
- WEPPpy upgrades its existing `climate/wepp_cli.parquet` sidecar to the
  cligen-rs schema;
- openWEPP consumes conforming `.cli.parquet` files directly into its typed
  climate runtime.

Both consumers bind to an explicit cligen-rs schema version rather than infer
conformance from a `.parquet` suffix. Schema evolution is initiated and
versioned in cligen-rs, then adopted through repository-local work packages.

## Architectural principle: one model, multiple adapters

Legacy and modern formats must not become parallel implementations of the
generator.

```text
legacy .par  ─┐
              ├─> typed station-parameter model ─> generator
.par.yaml    ─┘

generator/importer ─> typed climate records ─┬─> legacy .cli writer
                                             └─> .cli.parquet writer
```

The typed models own meaning, units, widths, optionality, and invariants.
Format adapters own syntax, physical types, and compatibility behavior. A
generation algorithm must never branch on whether its station parameters came
from `.par` or `.par.yaml`.

## `.par.yaml` design

### Semantic level

Version 1 represents the physical quantities consumed from records 1-83 of
the legacy `.par` file, before `sta_parms` performs derived-state
transformations. The YAML document may express those quantities in either the
legacy CLIGEN units or an SI-oriented unit profile; it does not encode
already-derived common-block state.

This boundary is essential: `.par` and both `.par.yaml` unit profiles project
into one typed raw-parameter model and then enter the same `sta_parms`
transformation path. SI conversion occurs once at that input boundary, with a
specified rounding/quantization contract. Encoding derived state in YAML or
allowing SI values to bypass `sta_parms` would create a second generator.

Fields skipped by the Fortran fixed-column formats and records after record 83
are not generator parameters. A legacy-to-YAML conversion records the source
file hash and may retain an external reference to the legacy artifact, but v1
does not embed an opaque copy of the unread tail. Therefore:

- legacy `.par` byte round-trip remains the responsibility of `ParFile`'s
  retained lexemes;
- `.par` -> legacy-unit `.par.yaml` -> canonical `.par` promises semantic/bit
  equivalence of consumed values, not reproduction of producer-specific
  whitespace or unread tail text;
- `.par` -> SI `.par.yaml` -> generator promises the equivalence class defined
  by the SI conversion contract; integer and fixed-width legacy fields may
  require explicit quantization and cannot claim arbitrary raw-value
  invertibility;
- applications requiring archival byte identity keep the original `.par`
  alongside the YAML file and verify its recorded hash.

### YAML profile

The syntax is a constrained profile of
[YAML 1.2](https://yaml.org/spec/1.2.2/), chosen to keep implementations
predictable and safe:

- UTF-8 text with LF line endings in canonical output;
- YAML 1.2 core/JSON-compatible scalar behavior;
- mappings, sequences, strings, booleans, integers, finite decimal numbers,
  and null only;
- duplicate mapping keys are errors;
- unknown keys are errors except beneath an explicit `extensions` mapping;
- custom tags, anchors, aliases, merge keys, and executable/object tags are
  forbidden;
- implicit timestamps are forbidden; date-like values remain strings;
- non-finite floats (`NaN`, positive infinity, negative infinity) are
  forbidden;
- every document carries a required schema identifier;
- parsers enforce resource limits for nesting depth, aliases (which should be
  zero), scalar length, and total document size.

Within a selected unit profile, only one representation is accepted for each
concept. In particular, v1 does not accept both monthly arrays and
`month: value` mappings, nor multiple unit-suffixed aliases from different
profiles. Undiscriminated spellings would complicate validation,
canonicalization, documentation, and diff review without adding information.

### Unit profiles and SI authoring

Every document has a required `units_profile` discriminator:

```yaml
units_profile: si-v1
```

V1 defines two mutually exclusive profiles:

- `si-v1` is preferred for newly authored parameters and uses SI or established
  SI-compatible meteorological units;
- `cligen-legacy-v1` uses the units and numeric interpretation of the legacy
  CLIGEN `.par` records and is the lossless evidence/conversion profile.

Unit-bearing field names are part of each profile. Yes, the SI profile uses
`mean_daily_mm`:

```yaml
schema: org.openwepp.cligen.station-parameters/v1
units_profile: si-v1

station:
  elevation_m: 1179.576

generator:
  maximum_6_hour_precip_mm: 58.674

precipitation:
  mean_daily_mm: [...]
  standard_deviation_mm: [...]
  skew: [...]
  wet_after_wet: [...]
  wet_after_dry: [...]

temperature:
  maximum_mean_c: [...]
  maximum_standard_deviation_c: [...]
  minimum_mean_c: [...]
  minimum_standard_deviation_c: [...]

solar_radiation:
  mean_mj_m2_day: [...]
  standard_deviation_mj_m2_day: [...]

dew_point:
  mean_c: [...]

storm_shape:
  maximum_half_hour_intensity_mm_h: [...]
  time_to_peak_cdf: [...]
```

The corresponding legacy profile uses `elevation_ft`,
`maximum_6_hour_precip_in`, `mean_daily_in`, temperature/dew-point `_f`,
solar-radiation `_langley_day`, and storm-intensity `_in_h` fields. Wind speed
is already m/s; direction degrees, probabilities, percentages, skew, and CDF
values retain their domain conventions in both profiles.

A document cannot mix profiles. For example, `mean_daily_mm` and
`standard_deviation_in` in the same document are an error, as is supplying both
`mean_daily_mm` and `mean_daily_in`. The parser never infers units from numeric
magnitude and never selects one alias by precedence.

Conversions use specification-pinned constants and evaluation order, including
exact definitions where available (`1 in = 25.4 mm`, `1 ft = 0.3048 m`, and
the ratified temperature and Langley conversions). SI decimals are converted
at the boundary and rounded once to the target faithful width. The canonical
legacy-to-SI converter emits enough decimal digits to reproduce the declared
post-conversion value and verifies that property before publishing the file.
Non-invertible cases, particularly integer elevation or values outside a
legacy field's representable range, must either:

- carry an explicit, provenance-recorded quantization accepted by the caller;
  or
- fail closed when exact faithful/legacy projection was requested.

Parsing never assigns a default unit profile. New-authoring tools may default
their *creation command* to `si-v1`, while `.par` conversion defaults to
`cligen-legacy-v1` unless the caller explicitly requests SI output.

### Monthly arrays

Station parameters are grouped by physical variable and statistic. Every
monthly value is a fixed 12-element array ordered January through December.
The month order is part of the schema and cannot be overridden in a document.

Arrays were selected because the dominant human task is scanning a variable's
annual shape and comparing adjacent months:

```yaml
schema: org.openwepp.cligen.station-parameters/v1
units_profile: cligen-legacy-v1

station:
  name: NEW MEADOWS
  state_code: 10
  station_code: 6388
  latitude_deg_north: 44.97
  longitude_deg_east: -116.28
  elevation_ft: 3870
  observed_years: 44

generator:
  wind_et_flag: 0
  single_storm_type: 2
  maximum_6_hour_precip_in: 2.31

precipitation:
  mean_daily_in:       [2.31, 1.98, 1.87, 1.42, 1.19, 0.82, 0.51, 0.62, 0.91, 1.31, 2.05, 2.44]
  standard_deviation_in: [1.02, 0.91, 0.87, 0.73, 0.61, 0.45, 0.30, 0.34, 0.49, 0.68, 0.94, 1.08]
  skew:                [1.10, 1.04, 0.98, 0.91, 0.88, 1.02, 1.21, 1.17, 1.06, 0.97, 1.01, 1.08]
  wet_after_wet:       [0.48, 0.46, 0.44, 0.39, 0.34, 0.25, 0.18, 0.20, 0.27, 0.35, 0.43, 0.49]
  wet_after_dry:       [0.22, 0.21, 0.20, 0.17, 0.14, 0.09, 0.05, 0.06, 0.10, 0.15, 0.19, 0.23]

temperature:
  maximum_mean_f: [...]
  maximum_standard_deviation_f: [...]
  minimum_mean_f: [...]
  minimum_standard_deviation_f: [...]

solar_radiation:
  mean_langley_day: [...]
  standard_deviation_langley_day: [...]

dew_point:
  mean_f: [...]

storm_shape:
  maximum_half_hour_intensity_in_h: [...]
  time_to_peak_cdf: [...]
```

The final schema will use complete arrays in examples and normative fixtures;
the ellipses above only abbreviate this backlog illustration.

Validation errors identify both the zero-based implementation index and human
month, for example:

```text
precipitation.mean_daily_in[6] (July): expected finite f32 value
```

Every monthly array must contain exactly 12 values. Sparse arrays and null
elements are invalid.

### Wind representation

Wind remains variable-first while direction names make the 16-bin axis
explicit. Each direction maps to a January-December array:

```yaml
wind:
  calm_percent: [...]

  occurrence_percent:
    n:   [...]
    nne: [...]
    ne:  [...]
    ene: [...]
    e:   [...]
    ese: [...]
    se:  [...]
    sse: [...]
    s:   [...]
    ssw: [...]
    sw:  [...]
    wsw: [...]
    w:   [...]
    wnw: [...]
    nw:  [...]
    nnw: [...]

  speed_mean_m_s:
    n: [...]
    # all 16 required directions

  speed_standard_deviation_m_s:
    n: [...]
    # all 16 required directions

  speed_skew:
    n: [...]
    # all 16 required directions

  interpolation_sources:
    - {slot: 1, station: "", weight: 0.0}
    - {slot: 2, station: "", weight: 0.0}
    - {slot: 3, station: "", weight: 0.0}
```

The schema fixes the direction-name-to-bin mapping and requires all 16 keys in
every wind distribution. A document cannot provide a mutable direction-angle
array whose order could drift away from its values. Canonical rendering uses
the order shown above.

`interpolation_sources` is a fixed three-element array corresponding to the
three ordered record-83 `site`/`wgt` slots actually consumed by the reference
program. Every element carries an explicit `slot` value 1-3. Blank station
names and zero weights remain values rather than causing an element to be
omitted, so unusual sparse combinations and slot identity round-trip exactly.
Text in the unread legacy tail is not promoted into typed parameters without a
future schema revision and an explicit consumer.

### Numeric widths and units

Unit suffixes are part of public field names. The unit profile selects the
allowed names and the conversion contract; it does not change the physical
meaning of a parameter or the precision required by its consumer.

The normative schema assigns each numeric leaf its intended width:

- source `INTEGER` values map to bounded integer fields;
- `cligen-legacy-v1` values corresponding to source `REAL*4` parse directly to
  f32-equivalent values;
- `si-v1` values parse through the schema's exact-decimal conversion rule and
  round once to the same target f32-equivalent parameter;
- a future native-only parameter must be explicitly typed f64 by its schema
  revision;
- no implementation may parse all YAML numbers to an incidental host f64,
  apply unconstrained unit conversions, and then silently double-round them to
  f32.

JSON Schema may describe structure and broad ranges, but executable fixture
tests remain authoritative for f32 conversion and faithful projection. Domain
constraints beyond source-proven requirements require corpus characterization
before adoption; the modern reader must not reject a legitimate legacy corpus
merely because an intuitive range was invented during schema writing.

### Provenance

Every converted or mutated file carries provenance:

```yaml
provenance:
  source_format: cligen-par-5.32.3
  source_sha256: "..."
  source_name: id106388.par
  produced_by: cligen-rs
  produced_by_version: "..."
  transformations: []
```

Mutation operations append versioned transformation records rather than
overwriting lineage. Deterministic conversion does not inject a wall-clock
timestamp by default; a caller may request one when its workflow requires it.
Unit-profile conversion records the source/target profiles, pinned conversion
revision, and every explicit quantization decision.

## `.cli.parquet` design

### Logical record model

The primary table has one row per simulation day. Simulation years are not
assumed to be contemporary civil years: year 1 is valid. The core schema uses
the established wepppyo3 calendar names `year`, `month`, and `day_of_month`
rather than forcing a timestamp. `year` is the CLIGEN/WEPP output year under
the declared simulation calendar.

Proposed common columns:

| Field | Arrow logical type | Nullability | `units` metadata | `description` metadata |
|---|---|---|---|---|
| `sim_day_index` | int32 | required | `day` | 1-indexed simulation day within the climate record |
| `year` | int32 | required | `year` | CLIGEN/WEPP output year under the declared calendar |
| `month` | int8 | required | `month` | Calendar month, 1-12 |
| `day_of_month` | int8 | required | `day` | Calendar day of month |
| `precip_mm` | float64 | required | `mm` | Total daily precipitation depth |
| `storm_start_h` | float64 | nullable | `h` | Breakpoint storm start time after midnight |
| `storm_end_h` | float64 | nullable | `h` | Breakpoint storm end time after midnight |
| `duration_h` | float64 | required | `h` | Storm duration; zero on dry days |
| `time_to_peak` | float64 | nullable | `unitless` | Parametric ratio of time to peak over storm duration |
| `peak_intensity_ratio` | float64 | nullable | `unitless` | Parametric ratio of peak to mean rainfall intensity |
| `tmax_c` | float64 | required | `deg C` | Maximum daily air temperature |
| `tmin_c` | float64 | required | `deg C` | Minimum daily air temperature |
| `solar_langley_day` | float64 | required | `langley/day` | Daily solar radiation |
| `wind_velocity_m_s` | float64 | required | `m/s` | Daily wind velocity |
| `wind_direction_deg` | float64 | required | `degree` | Daily wind direction clockwise from north |
| `tdew_c` | float64 | required | `deg C` | Daily dew-point temperature |
| `breakpoints` | list of struct | nullable | — (structural) | Ordered cumulative precipitation points |

### Arrow field-metadata contract

The Parquet Arrow schema adopts the wepppyo3 convention directly. Every scalar
field and nested scalar leaf carries metadata entries with the exact keys
`units` and `description`. Unit and description text are normative schema
content, not optional documentation added by a particular writer.

Structural list/struct fields carry `description`; their differently dimensioned
children carry the units. The breakpoint leaves are:

| Nested field | `units` | `description` |
|---|---|---|
| `time_after_midnight_h` | `h` | Breakpoint time after midnight |
| `cumulative_precip_mm` | `mm` | Cumulative precipitation depth at the breakpoint |

The top-level Arrow schema also follows the wepppyo3 dataset-version convention
with `dataset_version`, `dataset_version_major`, `dataset_version_minor`, and
`schema_version` metadata, in addition to the namespaced cligen metadata. The
cligen specification publishes the authoritative field manifest/schema
constructor so cligen-rs, WEPPpy/PyArrow, and openWEPP do not independently
retype or redescribe columns. WEPPpy must attach this Arrow schema explicitly
rather than rely on pandas type inference, which does not establish the
required field metadata contract.

The proposed public name `peak_intensity_ratio` intentionally clarifies the
legacy `.cli`/`SPEC-CLI-DIFF` field named `peak_intensity`; it is a
dimensionless peak-to-mean ratio, not an intensity with physical units. The
final Parquet spec must ratify this rename and amend the legacy-field mapping
and affected APIs explicitly. Derived windowed intensities retain names such
as `peak_intensity_30_mm_h` and cannot reuse the ratio field.

V1 uses the proleptic Gregorian calendar and records
`cligen.calendar = proleptic_gregorian`. The leap-year rule must match the
legacy continuous generator. A future non-Gregorian calendar requires a new
schema revision or a specifically compatible calendar extension; it cannot be
inferred from the rows.

`sim_day_index` is contiguous from 1 with no gaps or duplicates. Daily
date triples are unique and strictly ordered under the declared calendar. File
metadata declares `record_coverage = complete_run | partial_import |
single_storm`:

- `complete_run` must contain exactly the declared simulation span;
- `partial_import` must declare its first and last included dates and the
  reason/source for partial coverage;
- `single_storm` follows the selected-storm profile rather than pretending to
  cover a complete year.

Float64 is proposed for the stable Parquet schema because native mode and the
observed-Parquet pipeline are f64 targets. Serializing a faithful f32 value as
f64 is exact; the widening occurs at the output boundary and does not feed
back into faithful computation. The format specification must still
adjudicate float64 versus fixed-scale Parquet DECIMAL against these contracts:

- faithful generated Parquet can be rendered through the legacy formatter to
  byte-identical `.cli` daily records;
- imported legacy decimal tokens retain their value under canonical
  re-rendering;
- breakpoint times and depths do not lose their source precision.

If empirical adjudication selects DECIMAL for public rendered values, scales
must be field-specific and versioned. Implementations may not choose physical
types independently while claiming the same schema version.

### Parametric precipitation

For ordinary CLIGEN output:

- `precip_mm`, `duration_h`, `time_to_peak`, and
  `peak_intensity_ratio` carry the legacy daily values or their more precise
  pre-format equivalents as specified by the generation profile;
- `storm_start_h` and `storm_end_h` are null unless the producing profile
  defines them independently;
- `breakpoints` is null, meaning breakpoint representation is not applicable;
- dry days have zero precipitation and duration, with the parametric fields
  following the producing profile's documented dry-day convention.

### Breakpoint precipitation

The nested Arrow/Parquet type is:

```text
breakpoints: list<
  element: struct<
    time_after_midnight_h: float64 not null,
    cumulative_precip_mm:  float64 not null
  >
>
```

Lists are ordered, so no redundant point index is stored. The legacy
`nbrkpt` value is the list length and is not an independent source of truth.

For breakpoint files:

- a dry day has `breakpoints = []`, distinguishing it from parametric
  `breakpoints = null`;
- an empty breakpoint day has `precip_mm = 0`, `duration_h = 0`, and null
  `storm_start_h`/`storm_end_h`;
- a wet day has at least two ordered points unless the governing import
  profile explicitly supports a legacy one-point case;
- `time_after_midnight_h` stores the original absolute time in `[0, 24]`;
- times are strictly increasing under the strict profile;
- cumulative precipitation is finite, non-negative, and non-decreasing;
- zero-depth intervals are retained because they represent zero-intensity
  gaps;
- the first point is not normalized to time zero;
- for a non-empty list, `storm_start_h` is required and equals the first point
  time;
- for a non-empty list, `storm_end_h` is required and equals the last point
  time;
- for a non-empty list, `duration_h = storm_end_h - storm_start_h`, not merely
  the last point time;
- for a non-empty list, `precip_mm` equals the last cumulative depth;
- `time_to_peak` and `peak_intensity_ratio` are null rather than synthesized.

The physical type is a variable-length list. The storage schema does not
encode the historical 50-point WEPP limit: existing ecosystem compatibility
paths exercise larger cardinalities. Validation profiles may impose a strict
legacy limit, while the Parquet representation remains capable of preserving
larger valid inputs.

Breakpoint intensity segments and 10/15/30/60-minute peak intensities are
derived products, not substitutes for the cumulative points. They may be
published as versioned derived columns or a separate analytical view, but the
canonical record retains the source points so different consumers can
reconstruct and audit the hyetograph.

### Why nested Parquet is the canonical breakpoint representation

Parquet stores the struct leaves as typed columns plus repetition/definition
levels; it does not store each list as JSON. This provides:

- one copy of daily weather values regardless of breakpoint count;
- effectively empty breakpoint payloads for dry days;
- independent projection of daily weather or breakpoint leaves;
- good compression of ordered times and monotone cumulative depths;
- a single atomic file rather than daily and breakpoint files that can become
  separated or version-skewed.

An optional exploded analytical view may expose:

| Field | Meaning |
|---|---|
| `sim_day_index` | join key to the daily row |
| `breakpoint_index` | zero- or one-based ordinal fixed by that view's spec |
| `time_after_midnight_h` | source breakpoint time |
| `cumulative_precip_mm` | source cumulative precipitation |

That view is derived and must not replace the nested canonical record.

### File metadata and provenance

Parquet standardizes storage, not CLIGEN semantics. Every conforming file
must carry namespaced key/value metadata including:

```text
dataset_version = 1.0
dataset_version_major = 1
dataset_version_minor = 0
schema_version = 1
cligen.schema = org.openwepp.cligen.cli/v1
cligen.calendar = proleptic_gregorian
cligen.precipitation_representation = parametric | cumulative_breakpoints
cligen.record_coverage = complete_run | partial_import | single_storm
cligen.writer.name = cligen-rs | wepppy | ...
cligen.writer.version = ...
cligen.origin.kind = generated | imported
cligen.generation_profile = faithful-5.32.3 | native-f64-v1 | ...  # generated only
cligen.provenance = <versioned JSON object>
```

The provenance object covers, as applicable:

- writer name, version, source revision, and Parquet/Arrow library version;
- origin kind (`generated` or `imported`);
- generator name/version/source revision and generation profile for generated
  climates;
- original producer identity, source format/version, source filename, and
  source hash for imported climates;
- reference CLIGEN version and reference source hash;
- seed selection, burn count, and any other replay-relevant RNG inputs;
- station identifier, name, coordinates, elevation, and observation years;
- parameter schema/version and parameter-content hash;
- beginning simulation year and number of simulated years;
- command/options with secrets and host-specific paths excluded;
- transformation history;
- record coverage and its declared span;
- the typed legacy-header projection described below.

`imported` is never used as a producer name. For example, when WEPPpy converts
an externally produced breakpoint `.cli`, WEPPpy is the writer, the origin kind
is imported, and the original producer remains separately identified when
known.

Rich provenance should live in one versioned JSON value so adding optional
members does not create an uncontrolled set of footer keys. A small set of
scalar keys remains duplicated for discovery and predicate-free inspection.

Critical identifiers such as `run_id`, `station_id`, and
`generation_profile` should also be available as dictionary-compressed table
columns when datasets will be merged. Generic Parquet rewrites frequently
discard file metadata; critical identity must not depend exclusively on the
footer.

Field-level schema metadata records canonical units and descriptions. Readers
must bind to the cligen schema identifier and field contract, not merely to
column spelling.

### Typed legacy-header projection

A conforming file carries a versioned, typed projection sufficient to render a
canonical legacy `.cli` header. It includes:

- legacy data/version value;
- simulation mode;
- breakpoint mode/flag;
- wind/ET flag;
- station identifier and free-text station name;
- latitude, longitude, elevation, observation years, beginning year, and
  declared simulation years;
- generator command text under an explicit normalization/redaction policy;
- four fixed 12-value vectors for observed maximum temperature, minimum
  temperature, solar radiation, and precipitation;
- the declared numeric width/precision contract for each value family.

This projection belongs to the cligen schema rather than an untyped bag of JSON
values. Its Arrow representation may be schema metadata or a dedicated typed
structure ratified by `SPEC-CLI-PARQUET`, but readers and writers must validate
the same fields and widths. Header reconstruction and daily-record
reconstruction are separate acceptance gates so a complete daily table cannot
mask missing header state.

### Physical layout

Initial writer policy:

- rows sorted by `sim_day_index`;
- contiguous indices, unique date triples, and declared-calendar progression
  validated before writing;
- one row group for small individual climate files;
- bounded row groups for large files or multi-run datasets, selected by
  measured byte size rather than an arbitrary day count;
- Zstandard compression by default, with an explicitly recorded codec;
- statistics enabled for scalar daily columns;
- no requirement for byte-identical Parquet files across writer-library
  versions; equivalence is schema and value based;
- atomic write to a temporary file followed by rename;
- required schema and metadata validation before publication;
- configurable fail-closed reader limits for file size, row count, row-group
  count, decompressed allocation, metadata size, nesting depth, and per-day
  breakpoint list length.

Resource limits protect implementations and are distinct from scientific
strict/compatibility policies. A reader may support high-cardinality events
without accepting unbounded allocation from an untrusted file.

Large studies should eventually use a partitioned Parquet dataset instead of
millions of tiny files. Dataset partitioning is a separate specification: it
must not be improvised into the single-run file contract.

## Relationship to the existing WEPPpy Parquet sidecar

WEPPpy currently emits `climate/wepp_cli.parquet` as an analytical derivative
of `.cli`. Its breakpoint path skips the two-column source points and retains
daily totals, duration-like values, nullable `tp/ip`, and derived peak
intensities. That artifact is useful for reporting but is not lossless and
cannot currently replace the source breakpoint `.cli`.

WEPPpy will migrate this sidecar in place to the cligen-rs schema. The migrated
producer must:

- retain the existing canonical path `climate/wepp_cli.parquet`;
- emit the required `cligen.schema` identifier and provenance metadata;
- preserve the ordered nested breakpoint list rather than discard the source
  points;
- conform its common daily fields, units, types, and nullability to the
  cligen-rs specification;
- attach the authoritative Arrow schema, including every required `units` and
  `description` field-metadata entry, rather than rely on dataframe inference;
- retain useful reporting fields such as versioned peak-intensity products
  only as schema-approved derived fields;
- derive any flattened breakpoint reporting view from the conforming nested
  representation.

Existing pre-migration sidecars are not retroactively conforming. WEPPpy needs
an explicit migration/backfill path or must continue to treat them as its
legacy flattened schema. File metadata, not the unchanged filename, tells a
reader which contract applies.

## openWEPP consumption contract

openWEPP will become a direct consumer of `.cli.parquet`. The intended flow is:

```text
cligen-rs generation ────────────────────────┐
                                             ├─> conforming .cli.parquet
legacy/imported .cli ─> WEPPpy sidecar ─────┘              │
                                                            v
                                                 openWEPP typed climate runtime
```

The openWEPP reader must:

- validate `cligen.schema` and reject unsupported major versions;
- validate required provenance, physical/logical types, field `units` and
  `description` metadata, nullability, row order, date fields, and
  precipitation representation;
- map parametric daily records onto its non-breakpoint typed climate variant;
- map nested breakpoint points directly onto its breakpoint day/point model;
- preserve absolute time-after-midnight until the WEPP runtime boundary, where
  storm-relative time is derived;
- reject inconsistent redundant values such as `precip_mm` not matching the
  final cumulative breakpoint depth;
- fail closed rather than falling back to legacy `.cli` after a selected
  Parquet file fails validation;
- retain explicit legacy `.cli` input support for existing runs and comparison
  workflows.

The Parquet reader becomes another adapter into the same openWEPP typed climate
model used by its legacy parser; it must not create a parallel runtime
interpretation. Direct-consumer acceptance and parity tests belong to an
openWEPP work package, using fixtures versioned by the cligen-rs specification.

## Legacy support strategy

### Support lifetime

No legacy removal date is proposed.

- Legacy `.par` read support remains indefinite because the station corpus is
  scientifically and operationally valuable.
- A canonical legacy `.par` writer remains available indefinitely for
  conversion and compatibility. It promises semantic/bit equivalence, while
  exact original bytes remain available through retained source lexemes.
- Legacy `.cli` write support remains indefinite for WEPP execution, faithful
  byte-identity gates, comparison with reference CLIGEN, and existing tools.
- Legacy `.cli` read support remains available for imports and conversion,
  including breakpoint records once that extension lands.

Legacy support is frozen rather than abandoned:

- no modern-only concept is backfilled into a legacy syntax unless the legacy
  format represents it exactly;
- no new aliases or permissive autodetection are added casually;
- malformed files continue to fail closed;
- a modern value that cannot be exported faithfully to legacy format produces
  a typed error instead of being rounded, dropped, or approximated silently;
- compatibility adapters are tested but are not allowed to become alternative
  domain models.

### Format selection

Selection is explicit by API option and filename:

- `.par` -> legacy parameter reader/canonical writer;
- `.par.yaml` -> schema-bound YAML reader;
- `.cli` -> legacy climate reader/writer;
- `.cli.parquet` -> schema-bound Parquet reader/writer.

Readers may verify Parquet magic bytes after extension selection, but do not
guess between text and binary formats by trying multiple parsers. Failed
parsing in the selected format is an error, not a fallback trigger.

### Canonicalization and round-trip promises

The contracts differ deliberately:

| Path | Required invariant |
|---|---|
| legacy `.par` parse -> legacy bytes | byte identity through retained lexemes |
| legacy `.par` -> `cligen-legacy-v1` YAML -> station model | bit-identical consumed values |
| `cligen-legacy-v1` YAML -> canonical legacy `.par` -> model | bit-identical consumed values |
| `si-v1` YAML -> station model/legacy `.par` | declared post-conversion equivalence; explicit quantization or fail-closed exact projection |
| faithful generator -> legacy `.cli` | byte identity with reference fixture |
| faithful generator -> Parquet -> legacy formatter | byte-identical legacy header and daily values under separately gated typed projections |
| imported parametric `.cli` -> Parquet -> canonical `.cli` | semantic field identity; original whitespace is not promised |
| imported breakpoint `.cli` -> Parquet -> canonical `.cli` | ordered point and daily-field identity; original whitespace is not promised |

Original imported files remain the authority when byte-for-byte archival
reproduction matters. Modern files carry their hashes rather than pretending
that arbitrary legacy presentation can be reconstructed from typed values.

## Adoption sequence

### Phase 0: decision and fixture inventory

- Ratify this direction with an ADR because it establishes canonical public
  formats and long-lived compatibility obligations.
- Inventory `.par` producer variants and both parametric and breakpoint `.cli`
  corpora.
- Capture breakpoint fixtures covering nonzero storm starts, dry days,
  zero-intensity intervals, large events, and malformed/non-monotone input.
- Record external authority and provenance for breakpoint fixtures; do not
  imply they came from reference CLIGEN.

### Phase 1: normative specifications

Author before implementation:

- `SPEC-PAR-YAML` — YAML profile, complete schema, units, widths,
  `si-v1`/`cligen-legacy-v1` conversion and quantization, canonicalization,
  provenance, and legacy mapping;
- `SPEC-CLI-PARQUET` — Arrow/Parquet schema, metadata, physical types,
  required wepppyo3-compatible `units`/`description` field metadata, typed
  legacy-header projection, calendar/coverage rules, breakpoint semantics,
  reader resource limits, and compatibility rules;
- `SPEC-PROVENANCE` — shared generation/import/mutation lineage and profile
  representation;
- any amendment needed to `SPEC-PAR`, `SPEC-GENERATOR-CORE`, and the future
  complete legacy `.cli` specification.

Publish machine-readable schema artifacts where practical, but keep the
Markdown specifications authoritative for numerical and behavioral details
that JSON Schema or Arrow schema metadata cannot express.

### Phase 2: `.par.yaml` implementation

- Add YAML parsing for both unit profiles into the typed raw parameter model.
- Add deterministic canonical YAML rendering.
- Add `.par` -> `.par.yaml` and `.par.yaml` -> canonical `.par` conversion,
  including explicit SI selection and quantization reporting.
- Prove bit-identical `sta_parms` state and full generator streams for legacy
  units and every exactly convertible SI fixture; characterize or fail closed
  on explicitly quantized SI inputs.
- Add mutation/provenance operations only after basic conversion is closed.

### Phase 3: parametric `.cli.parquet`

- Complete the typed climate-record model and legacy text writer first.
- Implement the Parquet writer from the same generated records.
- Implement a schema-validating reader and legacy formatter.
- Gate faithful Parquet through separate legacy-header and daily-table byte
  formatters plus full-stream evidence.
- Expose explicit `cli`, `parquet`, and `both` output selections; initially
  retain legacy text as the default.

### Phase 4: breakpoint import and interchange

- Specify and implement the legacy breakpoint `.cli` parser as an extension.
- Map daily records to nested breakpoint lists without normalizing source
  times or dropping zero-depth intervals.
- Implement `.cli` <-> `.cli.parquet` conversion for breakpoint files.
- Validate against WEPP/openWEPP/wepppyo3 fixtures and independent readers.
- Keep breakpoint generation out of scope unless a separate generation-profile
  package is approved.

### Phase 5: ecosystem adoption

- Upgrade WEPPpy's existing `climate/wepp_cli.parquet` sidecar in place to a
  pinned cligen schema version, including nested breakpoint preservation.
- Add an explicit WEPPpy compatibility/backfill path for pre-schema flattened
  sidecars.
- Add openWEPP `.cli.parquet` intake, schema validation, and projection into
  its existing typed parametric/breakpoint climate model.
- Share or generate the cligen Arrow field manifest so cligen-rs, WEPPpy, and
  openWEPP validate identical names, types, units, and descriptions.
- Gate openWEPP legacy `.cli` and `.cli.parquet` paths on equivalent runtime
  climate requests for the shared fixture corpus.
- Add Arrow/PyO3 handoff without requiring intermediate flat files.
- Offer dual-write migration periods for operational workflows.
- Promote `.par.yaml` and `.cli.parquet` as defaults for new native/API
  workflows only after consumer and conversion gates are green.
- Continue emitting legacy `.cli` whenever WEPP or faithful comparison is the
  selected consumer.

## Acceptance gates

### `.par.yaml`

- Every committed `.par` fixture converts to `cligen-legacy-v1` YAML and
  produces bit-identical raw typed fields.
- Legacy `.par` and `cligen-legacy-v1` YAML inputs produce identical
  `sta_parms` snapshots and faithful RNG/output streams.
- Every document declares `si-v1` or `cligen-legacy-v1`; mixed unit-suffixed
  fields and missing/unknown profiles fail closed.
- Legacy-to-SI fixture conversion reproduces the specified post-conversion
  generator parameters, or reports an explicit non-invertible quantization.
- Boundary vectors pin inches/mm, feet/meters, Fahrenheit/Celsius,
  Langley/MJ-per-square-meter, and intensity conversions at rounding and
  integer-quantization edges.
- Every monthly array is exactly 12 finite values.
- Every wind map has exactly the 16 required directions and 12 values per
  direction.
- Wind interpolation sources preserve exactly three ordered slots, including
  blank station names and zero weights.
- Duplicate keys, aliases, unknown fields, non-finite values, missing required
  fields, and unsupported schema versions fail closed.
- Canonical YAML output is deterministic for a pinned schema/writer version.
- `cligen-legacy-v1` YAML -> canonical `.par` -> typed model is a bit-exact
  semantic fixpoint; `si-v1` satisfies its declared post-conversion equivalence
  or fails closed when exact projection was requested.
- Decimal-to-f32 conversion is exercised at rounding boundaries, not just on
  friendly corpus values.

### Parametric `.cli.parquet`

- All required schema fields, units, nullability, and metadata are validated.
- Every scalar field and nested leaf carries the exact authoritative `units`
  and `description` metadata, and the wepppyo3 dataset-version keys agree with
  `cligen.schema`.
- Faithful generated records survive Parquet round-trip and legacy formatting
  with byte-identical `.cli` output.
- Typed legacy-header and daily-table reconstruction pass separate
  byte-identity gates.
- Simulation-year values such as 1 are preserved without forced timestamp
  conversion.
- The proleptic-Gregorian calendar, contiguous day index, unique ordered dates,
  record coverage, and declared simulation span are mutually consistent.
- Dry-day conventions and nullable fields are explicit and tested.
- Files interoperate with arrow-rs, PyArrow, and DuckDB; Polars should be
  included when available in the supported environment.
- Projection tests demonstrate that scalar daily queries do not require
  breakpoint leaf reads.
- Writer failure cannot expose a partial final file.

### Breakpoint `.cli.parquet`

- `null` distinguishes non-breakpoint representation from an empty breakpoint
  list on a dry breakpoint day.
- Empty breakpoint days have zero precipitation/duration and null storm
  start/end.
- Ordered time/depth points round-trip exactly at the declared physical
  precision.
- Nonzero storm starts remain absolute times after midnight.
- For non-empty lists, storm start/end equal the first/last point times and
  `duration_h` equals end minus start.
- Zero-depth intervals remain present.
- Total precipitation equals the last cumulative depth.
- `time_to_peak` and `peak_intensity_ratio` remain null.
- Strictly decreasing depths, non-increasing times under the strict profile,
  invalid dates, mismatched list/count legacy records, and truncated events
  fail closed.
- Fixtures cover at least 0, 1, 2, 42, 51, and a high-cardinality compatibility
  event; storage itself remains variable length.
- A conforming Parquet file can regenerate a WEPP-consumable canonical
  breakpoint `.cli` without losing any source point.
- Reader limits reject excessive files, metadata, row groups, decompressed
  allocations, nesting, or point lists independently of scientific
  cardinality policy.

### Repository gates

Each implementation package also runs the repository gates from `AGENTS.md`,
including coverage/CRAP gates for production functions, and records commands
and exit codes under the package's artifacts.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| YAML permits too many equivalent or unsafe constructs | Constrain to one YAML 1.2 profile; reject aliases, tags, duplicate and unknown keys |
| Decimal parsing changes faithful f32 inputs | Parse to declared width and gate state/stream identity at rounding boundaries |
| SI and legacy fields are mixed or converted differently by implementations | Require one document-level unit profile, pinned conversions, single-rounding rules, and quantization evidence |
| Month or wind axes become misaligned | Fixed 12-element month arrays; named, required wind directions; deterministic ordering |
| Legacy and modern paths diverge | One typed model and one generator; adapters only at boundaries |
| Writer identity is confused with imported-source origin | Record writer, origin kind, generator, and original producer as distinct provenance fields |
| Daily values round-trip but the legacy header does not | Require a typed legacy-header projection and gate header reconstruction separately |
| Row order or leap-day semantics drift across consumers | Fix the v1 calendar and validate contiguous indices, dates, coverage, and declared span |
| Parquet metadata disappears during generic rewrites | Duplicate critical identity in compressed columns; validate metadata at trusted ingest boundaries |
| Nested breakpoint fields are awkward in some tools | Keep nested canonical form and publish an optional exploded derived view |
| Existing WEPPpy Parquet is mistaken for the new schema | Migrate the sidecar producer in place, require `cligen.schema`, and retain an explicit pre-schema compatibility path |
| openWEPP develops a second climate interpretation | Make Parquet a validated adapter into its existing typed climate model and require legacy/Parquet runtime-request parity |
| cligen-rs, WEPPpy, and openWEPP drift on Parquet field meaning | Publish one field manifest and require exact Arrow names, types, `units`, and `description` metadata |
| Derived intensity columns become stale or algorithm-dependent | Keep cumulative points canonical; version derived products and algorithms |
| High-cardinality events exceed historical limits | Variable-length storage; separate strict and compatibility validation profiles |
| Parquet bytes vary across library versions | Specify semantic equivalence, record writer provenance, and avoid byte hashes as the data-identity gate |
| Modern-only data are silently lost on legacy export | Typed representability checks and fail-closed conversion errors |
| Dual support becomes permanent duplicated complexity | Freeze legacy semantics and isolate adapters; modern schema alone receives extensions |

## Decisions proposed for ratification

1. `.par.yaml` is the canonical modern station-parameter authoring format.
2. `.cli.parquet` is the canonical modern climate-series and analytical
   interchange format.
3. Monthly station parameters use variable-grouped, fixed January-December
   arrays rather than month mappings.
4. `.par.yaml` supports explicit `si-v1` and `cligen-legacy-v1` unit profiles;
   `mean_daily_mm` belongs to SI and mixed profiles fail closed.
5. Breakpoint precipitation uses an ordered nested list of
   `(time_after_midnight_h, cumulative_precip_mm)` structs in the daily row.
6. cligen-rs owns the breakpoint Parquet specification while labeling
   breakpoint support as interoperability, not reference CLIGEN behavior.
7. Legacy `.par` read/canonical-write and `.cli` read/write support have no
   planned removal date, but their semantics are frozen.
8. Modern-only extensions do not appear silently in legacy files and require
   versioned profiles/provenance.
9. WEPPpy's `climate/wepp_cli.parquet` sidecar adopts the cligen-rs schema in
   place; existing flattened files remain pre-schema legacy artifacts.
10. openWEPP consumes `.cli.parquet` directly through a validating adapter into
   its existing typed climate runtime, while retaining legacy `.cli` support.
11. `.cli.parquet` adopts the wepppyo3 Arrow convention: authoritative
    `units` and `description` metadata accompany scalar fields and nested
    leaves, with compatible dataset-version metadata.
12. Writer identity, generated/imported origin, generator identity, and
    original imported producer are separate provenance concepts.
13. V1 uses a declared proleptic-Gregorian calendar, explicit record coverage,
    and a typed legacy-header projection.

## Open adjudications for the specification package

These questions should be resolved empirically before implementation rather
than left to individual writers:

- float64 versus field-specific DECIMAL physical types for the stable
  `.cli.parquet` schema;
- exact SI conversion/elevation quantization rules and canonical emitted
  decimal precision for `.par.yaml`;
- the exact station identifier model across USDA, international, generated,
  and user-authored parameters;
- which scientific domain ranges can be enforced without rejecting valid
  legacy corpora;
- strict versus compatibility breakpoint validation profiles and their names;
- the minimal provenance subset that must also be duplicated as table columns;
- the Arrow/metadata representation of the typed legacy-header projection;
- final ratification of `peak_intensity_ratio` and its explicit mapping from
  the legacy `peak_intensity` field;
- final unit-string vocabulary and descriptions in the cligen/wepppyo3 field
  manifest;
- canonical legacy rendering widths for imported breakpoint values whose
  producers use more precision than historical WEPP documentation;
- whether derived peak-intensity products live in the same Parquet file under
  versioned optional fields or exclusively in a derived view;
- promotion timing for modern defaults in CLI, Rust API, and future PyO3
  surfaces.

## References

- [ADR-0001: source-code-authority port](../decisions/0001-source-code-authority-port.md)
- [SPEC-PAR](../specifications/SPEC-PAR.md)
- [SPEC-GENERATOR-CORE](../specifications/SPEC-GENERATOR-CORE.md)
- [SPEC-CLI-DIFF](../specifications/SPEC-CLI-DIFF.md)
- [Rust scientific coding standard](../standards/rust-scientific-coding-standard.md)
- [Apache Parquet overview](https://parquet.apache.org/docs/overview/)
- [Apache Parquet logical types](https://parquet.apache.org/docs/file-format/types/logicaltypes/)
- [YAML 1.2.2 specification](https://yaml.org/spec/1.2.2/)
