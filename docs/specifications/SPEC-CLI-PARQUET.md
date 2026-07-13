# SPEC-CLI-PARQUET — Parametric Typed Climate Output

Status: active (revision 1; A1)
Surface: optional `.cli.parquet` output and public `ClimateRowV1` values.

## Scope and authority

Revision 1 represents generated continuous and observed parametric climate.
It does not represent breakpoint precipitation, import legacy `.cli`, or emit
single/design-storm Parquet. Those require later schema/profile work. The
values originate in `DailyRow` before Fortran text formatting; faithful f32
values widen exactly once to f64 at this output boundary and never feed back
into generation.

The runspec keeps required `output.cli` and adds optional `output.parquet`,
which must be a non-empty distinct path ending in `.cli.parquet`. Explicit
selection, not extension sniffing, chooses the writer.

## Logical schema

Machine-readable field manifest:
[`cli-parquet-v1.fields.json`](cli-parquet-v1.fields.json).

Fields occur in this exact order and are non-nullable:

| Field | Arrow/Parquet type | Units | Meaning |
|---|---|---|---|
| `run_id` | UTF8 / BYTE_ARRAY String | `1` | effective-runspec SHA-256 |
| `generation_profile` | UTF8 / BYTE_ARRAY String | `1` | declared profile ID |
| `station_parameter_set_sha256` | UTF8 / BYTE_ARRAY String | `1` | syntax-independent station-model content identity |
| `sim_day_index` | Int32 | day | one-based contiguous row index |
| `year` | Int32 | year | CLIGEN/WEPP output year, 1–99,999 (frozen text `i5` domain) |
| `month` | Int8 | month | calendar month 1–12 |
| `day_of_month` | Int8 | day | valid day in month |
| `precip_mm` | Float64 | mm | total daily precipitation |
| `duration_h` | Float64 | h | parametric storm duration; source value on dry days |
| `time_to_peak_fraction` | Float64 | 1 | time-to-peak / duration; source value on dry days |
| `peak_intensity_ratio` | Float64 | 1 | peak / mean rainfall intensity; source value on dry days |
| `tmax_c` | Float64 | degree_Celsius | daily maximum air temperature |
| `tmin_c` | Float64 | degree_Celsius | daily minimum air temperature |
| `solar_langley_day` | Float64 | langley/day | daily solar radiation |
| `wind_velocity_m_s` | Float64 | m/s | daily wind velocity |
| `wind_direction_deg` | Float64 | degree | clockwise from north |
| `tdew_c` | Float64 | degree_Celsius | daily dew-point temperature |

Every Arrow field carries exactly `units` and `description` metadata. The
first three repeated identity columns remain available if generic tooling
drops file metadata; the writer enables dictionary encoding for them only.
There are no nullable placeholder breakpoint columns in v1.

## File metadata and provenance

Required ordered footer keys include:

```text
cligen.output_schema = org.openwepp.cligen.cli.parquet
cligen.output_schema_version = 1
cligen.provenance_schema_version = 1
cligen.station_input_schema = <id>/<version>
cligen.station_model = fixed_monthly_5_32_3
cligen.generation_profile = <profile>
cligen.calendar = proleptic_gregorian
cligen.precipitation_representation = parametric
cligen.coverage = complete_run | observed_source_end
cligen.writer.name = cligen-rs
cligen.writer.version = <package version>
cligen.writer.parquet = <non-empty implementation identity>
cligen.provenance = <canonical compact SPEC-PROVENANCE JSON>
```

Top-level Arrow schema metadata repeats the output schema/version. Readers
bind to identifiers, exact field order/types/nullability, field metadata, and
SPEC-PROVENANCE; a suffix alone does not establish conformance.

## Physical writer policy

- the A1 writer pins `arrow-rs-parquet/59.1.0` exactly;
- Parquet writer version 2.0, Zstandard level 3;
- fixed `created_by = cligen-rs parquet-writer-v1`;
- at most 65,536 rows per row group, deterministic input order;
- scalar statistics enabled; repeated identity strings dictionary encoded;
- one Arrow record batch per row group;
- same-directory staging, successful close, and rename before the final path
  becomes visible.

Logical schema, values, normalized metadata, and provenance are normative.
Raw Parquet bytes are not a compatibility contract across writer-library
versions. The exact pin nevertheless has a repeat-write byte diagnostic.
Readers require writer name/version to agree with embedded producer identity,
but do not compare producer version to the reader build. Exact
compression/encoding/`created_by` diagnostics apply when the footer names the
pinned A1 writer; a foreign/future writer may retain logical schema v1.

## Validation

Before writing, rows must be non-empty, contiguous from index 1, finite, exact
binary32 widenings (including signed zero), date
valid and strictly ordered under proleptic Gregorian rules, and consistent
with provenance day/span/coverage. Identity strings/hashes must agree with
the embedded provenance. Unsupported modes, path collisions, schema drift,
or non-finite values fail closed.

## Acceptance

- every continuous/observed golden retains byte-identical `.cli` with
  Parquet enabled;
- readback equals exact f32-to-f64 widened rows and round-trips to the original
  f32 bits, including signed zero vectors;
- schema, units, descriptions, footer keys, provenance, dates, coverage, and
  row-group policy validate through arrow-rs and an independent reader;
- modern/legacy station variants share rows/model/parameter hash but retain
  distinct station-input schema and byte hashes;
- a failed/colliding write leaves no partial final Parquet file.
