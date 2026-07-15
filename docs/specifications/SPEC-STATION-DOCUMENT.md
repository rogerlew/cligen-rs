# SPEC-STATION-DOCUMENT — Modern Fixed-Monthly Station Document

Status: active (revision 2; A8c adds an explicit routed extension while
revision 1 remains unchanged)
Surface: deterministic `*.station.json`, its Draft 2020-12
[`station-document.schema.json`](station-document.schema.json), the
syntax-independent `FixedMonthly5323` model, and legacy conversion.

Revision 1 is the fixed-monthly compatibility document described below and
remains byte/schema stable. Revision 2 is accepted only with the non-default
`a8c_routed_daily_v1` pilot profile. It retains the exact revision-1 units,
lineage, and parameters, adds the explicit `daily_precipitation` route and
coefficients, and is normatively specified by
[SPEC-A8C-ROUTED-DAILY](SPEC-A8C-ROUTED-DAILY.md) and
[station-document-v2.schema.json](station-document-v2.schema.json). Missing
or unknown routing information fails closed; existing profiles reject
revision-2 documents.

## Purpose and authority

This document modernizes station storage without changing the climate model.
It represents exactly the raw typed station values that CLIGEN 5.32.3 reads
from records 1–83 of a legacy `.par`; it does not represent row labels,
numeric lexemes, skipped TP5 text, the unread tail, or line endings.

The authority for values and ordering remains SPEC-PAR and
`reference/cligen532/cligen.f:2459,2753-2815,2881-2883`. The JSON envelope,
units, lineage, and failure rules are A4a extension surfaces. The modern
document is behaviorally inert: both input syntaxes produce one
`FixedMonthly5323` before RNG initialization or `sta_parms` distribution.

Producers: `cligen stations convert`, the public conversion API, and future
fitters that can truthfully provide the required lineage. Consumers:
SPEC-RUNSPEC `station.document`, `FixedMonthly5323`, `sta_parms`, and the
quality-target builder.

## Independent identities

Every document requires:

```json
{
  "station_schema_version": 1,
  "station_model": "fixed_monthly_5_32_3",
  "units": {},
  "lineage": {},
  "parameters": {}
}
```

`station_schema_version` versions the JSON envelope. `station_model` versions
the scientific parameterization. Neither is a generation profile or an
output-schema version, and neither implies a revision of those independent
axes. Revision 1 accepts only the values above. Annual SD, covariance,
Fourier/EOF, and other interannual fields are unknown fields and fail closed;
they require a distinct station-model identifier and ADR-0002 adjudication.

## Serialization

- UTF-8 JSON, one object, no BOM or trailing value.
- Unknown and duplicate fields fail at every object level.
- Canonical emission is `serde_json` pretty form in declared struct-field
  order plus one LF. No maps or timestamp/path-dependent values occur.
- Every number used by the model is deserialized directly to `f32` or `i32`.
  All `f32` values must be finite. `-0.0` is significant and must survive
  parse/serialize by `to_bits` equality.
- Arrays are fixed: month vectors 12, directional wind arrays 16 × 12, and
  wind interpolation sources/weights 3.

Canonical bytes are deterministic for one document value. A canonical
document reparses and re-emits byte-identically.

## Units

Revision 1 performs no unit conversion. The required `units` object contains
these exact closed values:

| Key | Value | Fields governed |
|---|---|---|
| `latitude` | `degree_north` | location latitude |
| `longitude` | `degree_east` | location longitude |
| `elevation` | `foot` | raw station elevation |
| `record_length` | `year` | record years |
| `precipitation_depth` | `inch` | precipitation mean/SD and six-hour depth |
| `precipitation_intensity` | `inch_per_hour` | raw maximum half-hour intensity; halved only by `sta_parms` |
| `temperature` | `degree_fahrenheit` | maximum/minimum/dew-point means and SDs |
| `solar_radiation` | `langley_per_day` | solar mean and SD |
| `wind_speed` | `meter_per_second` | directional wind speed mean/SD |
| `frequency` | `percent` | wind-sector and calm frequency |
| `probability` | `fraction` | wet transitions and time-to-peak CDF |
| `interpolation_weight`, `skew` | `dimensionless` | interpolation weights and skew parameters |

Changing a unit string is not a conversion request; it is an unsupported
units variant and fails closed.

## Lineage

The required object is:

```json
{
  "source_format": "cligen_par_5_32_3",
  "source_sha256": "<64 lowercase hexadecimal characters>",
  "adapter": "cligen_rs_legacy_par_to_fixed_monthly",
  "adapter_version": 1
}
```

No source path or timestamp is recorded, so identical source bytes and adapter
revision produce identical document bytes. The hash identifies the complete
legacy input, including presentation bytes excluded from the model.

## Parameter mapping

All strings retain the fixed-width A-edit value exactly: `station_name` is 41
ASCII bytes; each `interpolation_source_names` entry is 19 ASCII bytes.
Padding is model state because the faithful `.cli` header writes
`station_name` directly. No trimming or inferred padding is accepted.

| Legacy typed field | JSON path under `parameters` | Shape | Units |
|---|---|---:|---|
| `stidd`, `nst`, `nstat`, `igcode` | `identity.station_name_raw`, `state_code`, `station_code`, `wind_et_flag` | scalar | text / code |
| `ylt`, `yll`, `elev_ft`, `years` | `location.latitude`, `longitude`, `elevation`, `record_years` | scalar | declared above |
| `itype`, `tp6`, `timpkd` | `storm.single_storm_type`, `max_six_hour_precipitation`, `time_to_peak_cdf` | scalar / 12 | code / inch / fraction |
| `rst(:,1..3)` | `precipitation.mean_daily`, `standard_deviation_daily`, `skew` | 12 each | inch / inch / dimensionless |
| `prw(:,1..2)` | `precipitation.probability_wet_given_wet`, `probability_wet_given_dry` | 12 each | fraction |
| `wi_raw` | `precipitation.max_half_hour_intensity` | 12 | inch/hour |
| `obmx`, `obmn`, `stdtx`, `stdtm`, `rh` | `temperature.maximum_mean`, `minimum_mean`, `maximum_standard_deviation`, `minimum_standard_deviation`, `dew_point_mean` | 12 each | °F |
| `obsl`, `stdsl` | `solar_radiation.mean_daily`, `standard_deviation_daily` | 12 each | Langley/day |
| `wvl(:,1,:)` | `wind.directions[*].frequency` | 16 × 12 | percent |
| `wvl(:,2,:)` | `wind.directions[*].mean_speed` | 16 × 12 | m/s |
| `wvl(:,3,:)` | `wind.directions[*].standard_deviation_speed` | 16 × 12 | m/s |
| `wvl(:,4,:)` | `wind.directions[*].skew` | 16 × 12 | dimensionless |
| `calm` | `wind.calm_frequency` | 12 | percent |
| `site`, `wgt` | `wind.interpolation_stations[*].station_name_raw`, `weight` | 3 objects | text / dimensionless |

Wind direction index order is the source record order: N, NNE, NE, ENE, E,
ESE, SE, SSE, S, SSW, SW, WSW, W, WNW, NW, NNW. No matrix transpose is
permitted at the typed boundary.

## Validation and failure behavior

Parsing fails closed with a typed, field-addressable error for malformed
JSON, missing/unknown/duplicate fields, foreign schema/model/unit/lineage
identifiers, invalid SHA-256, wrong fixed-array shape, non-finite or
non-`f32`-convertible numbers, non-ASCII/wrong-width strings, or a storm type
outside `1..=4`. Revision 1 deliberately adds no speculative physical bounds
that the legacy source did not enforce.

Legacy conversion first applies SPEC-PAR. A malformed `.par` is returned as a
legacy parse error; the adapter never truncates overflowing names, guesses
shifted integer fields, or supplies defaults.

## Adapter and runtime seam

```text
legacy .par bytes -> ParFile -> FixedMonthly5323
station JSON      -> StationDocumentV1 -> FixedMonthly5323
FixedMonthly5323  -> sta_parms -> faithful generator
```

The modern path never renders and reparses fixed-width `.par`; doing so would
introduce decimal-width quantization and couple future models to an obsolete
transport. Feet→metres, intensity→depth, derived CVs, wind accumulation, and
monthly interpolation remain exactly where SPEC-PAR assigns them in
`sta_parms`.

## Runspec, quality, and provenance bridge

SPEC-RUNSPEC selects exactly one explicit path: `station.par` or
`station.document`. There is no extension sniffing. The default compatibility
header echo for the modern path is `--station-document=<lexical-path>`;
explicit `output.command_echo` remains verbatim and lets converted golden
vectors retain their historical header bytes.

A1 replaces the temporary `identity.content.par_sha256` bridge with the
syntax-independent station model/parameter-set identity plus the declared
legacy-source SHA-256. Full run provenance truthfully distinguishes selected
legacy and document input schema/bytes. Quality targets still come from the
same typed state; standalone `cligen quality --par` remains legacy intake.
The parameter-set identity is SHA-256 over compact canonical JSON for the
declaration-ordered `parameters` object only; envelope, model, units, and
lineage are excluded.

## Acceptance

- Four fixture `.par` files convert and reparse with exact integers/strings and
  bit-identical `f32`, including explicit negative-zero vectors.
- Modern state reproduces all existing four-station × interpolation 0..3
  `sta_parms` snapshots.
- All 12 runspec goldens reproduce `.cli` bytes through either station syntax
  when the historical `command_echo` is explicit. Quality metric content is
  identical; A1 provenance intentionally distinguishes selected input syntax
  and bytes.
- Deterministic bytes validate against the published JSON Schema; malformed
  vectors cover every failure class above.
- The ignored five-collection gate follows the Q2 SQLite catalogs and requires
  identity for every legacy-parseable row. Inherited legacy parse failures are
  reported separately and never normalized.
