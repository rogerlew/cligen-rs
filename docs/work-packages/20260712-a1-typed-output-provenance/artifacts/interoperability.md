# A1 Interoperability Evidence

Status: Ran — arrow-rs conformance plus independent PyArrow and JSON Schema
readers passed on 2026-07-12.

## PyArrow readback

Python `pyarrow 16.1.0` independently opened all 10 generated
continuous/observed `.cli.parquet` files and materialized every table.

| Observation | Result |
|---|---|
| Files / rows | 10 / 78,538 |
| Field count | 17, in the published manifest order |
| Coverage identities | 4 `complete_run`; 6 `observed_source_end` |
| Compression | ZSTD on every inspected column chunk |
| Largest row group in the corpus | 15,340 rows, below the 65,536 maximum |
| `created_by` | `cligen-rs parquet-writer-v1` on every file |
| Embedded provenance | Parsed for every file; emitted-day counts equal table rows |

The exact independent field order was:

```text
run_id, generation_profile, station_parameter_set_sha256, sim_day_index,
year, month, day_of_month, precip_mm, duration_h, time_to_peak_fraction,
peak_intensity_ratio, tmax_c, tmin_c, solar_langley_day, wind_velocity_m_s,
wind_direction_deg, tdew_c
```

PyArrow exposes its normalized `format_version` label as `2.6` for these
files. That reader-facing label is recorded rather than silently rewritten;
the pinned arrow-rs conformance reader independently verifies footer version
2, `created_by`, ZSTD, encodings, statistics, row groups, logical schema,
metadata, and values for files that identify the A1 writer.

## JSON Schema interoperability

Python `jsonschema 4.23.0` used a fully offline Draft 2020-12 registry. It
strictly parsed and checked all seven changed schema resources, resolved both
versioned resources and mutable latest aliases, and demonstrated that the
historical quality-report v1 and current v2 envelopes remain independent.

The external validator accepted 57 provenance sidecars, 41 quality reports,
10 embedded Parquet provenance values, 12 runspecs, and 24 station documents.
It rejected 23 mutations expressible in JSON Schema. Rust tests separately
recomputed content, effective-runspec, station-parameter, and run identities
and enforced semantic relationships that Draft 2020-12 cannot encode.

## Reader contract and limits

The public compatibility contract is the versioned logical schema, values,
field metadata, normalized file metadata, and provenance—not byte identity
across Parquet libraries. Exact repeat bytes remain a diagnostic under the
59.1.0 writer pin. The logical Rust reader does not require a foreign/future
writer to claim the current implementation revision; exact physical-policy
checks apply only when the file names the pinned A1 writer.

DuckDB and Polars were not installed on the execution host, so no result is
claimed for them. PyArrow supplies the package's required independent Parquet
reader evidence.
