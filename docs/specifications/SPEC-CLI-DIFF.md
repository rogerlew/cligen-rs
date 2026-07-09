# SPEC-CLI-DIFF

Status: Active
Work package: `docs/work-packages/20260709-golden-fixture-harness/`

## Surface

Field-wise comparison of CLIGEN `.cli` text outputs for fixture and
trajectory evidence. The comparison surface is exposed by the `cligen`
crate's `cli_diff` module and the `cligen-cli-diff` binary.

## Producers / Consumers

- Producers: CLIGEN reference builds and, later, cligen-rs faithful-mode
  runs.
- Consumers: port work packages, golden fixture gates, and debugging tools
  that need the first divergent daily field rather than aggregate climate
  statistics.

## Authority Basis

The `.cli` daily table is written by `reference/cligen532/cligen.f`:

- Header and daily-table column labels: `wxr_gen`, around lines 3678-3698.
- Daily WEPP rows: `day_gen`, format `2000`, around lines 3054-3057 and
  the unit-7 write around lines 3173-3176.

This differ is a harness tool, not generator behavior. It does not define
the `.cli` format beyond the subset needed to locate the daily table and
compare its fields.

## Semantics

The differ locates the first line whose first three whitespace-separated
tokens are `da`, `mo`, and `year`. The following line is treated as the
units line. Every later non-empty line is parsed as a daily row with these
13 fields:

| Field | Units / Meaning |
|---|---|
| `day` | day of month |
| `month` | month |
| `year` | output year |
| `precip_mm` | precipitation, mm |
| `duration_h` | storm duration, h |
| `time_to_peak` | fraction of storm duration |
| `peak_intensity` | peak intensity ratio |
| `tmax_c` | maximum air temperature, C |
| `tmin_c` | minimum air temperature, C |
| `solar_langley_day` | solar radiation, Langleys/day |
| `wind_velocity_m_s` | wind velocity, m/s |
| `wind_direction_deg` | wind direction, degrees |
| `tdew_c` | dew point, C |

Field values are validated as numeric text and then compared by exact token
equality. This intentionally catches both trajectory differences and output
rounding/formatting differences. The first mismatch is reported with row
index, date, field name, source line numbers, and the expected/actual value
pair.

If one file has fewer daily rows, the first missing or extra row is the
reported divergence.

## Failure Behavior

Malformed input fails closed:

- missing daily header;
- missing units line;
- no daily rows;
- any non-empty daily row with a field count other than 13;
- non-numeric daily values.

No defaults are inferred.

## Provenance Obligations

Diff evidence must name both compared files and the reference build
provenance used to generate any fixture output.
