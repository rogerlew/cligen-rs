# SPEC-CLI-TEXT — Frozen WEPP-Compatible Climate Text

Status: active (revision 1; A1 documentation of the existing faithful surface)
Surface: generated `.cli` text and its projection from retained pre-format
generator state.

## Authority and compatibility

`reference/cligen532/cligen.f:3055-3056,3175-3176,3722-3754,965-966`
defines the faithful bytes. `crate::output` implements its formats through the
pinned Fortran formatter. The 12 golden files remain the acceptance authority.
A1 does not add bytes to this format.

The header is an owned typed projection of the values used by the faithful
writer: version/mode flags, exact padded station identity, location,
observation/simulation spans, command echo, and four monthly climatology
vectors. Daily values are the source-shaped f32 `DailyRow` fields after the
source's output-boundary unit conversions.

| Typed field | Text column | Units |
|---|---|---|
| `jd`, `mo`, `iyear` | `da`, `mo`, `year` | calendar integer |
| `xr` | `prcp` | mm |
| `dur` | `dur` | h |
| `tpr` | `tp` | fraction |
| `xmav` | `ip` | dimensionless peak/mean ratio |
| `tmxg`, `tmng`, `tdp` | `tmax`, `tmin`, `tdew` | degree Celsius |
| `radg` | `rad` | Langley/day |
| `wv` | `w-vl` | m/s |
| `th` | `w-dir` | degree clockwise from north |

The formatted decimals are a compatibility projection, not the modern typed
authority. A1 Parquet stores exact f64 widenings of the pre-format f32 values.

## Provenance

Changing the text would break WEPP consumers and faithful fixtures. Each text
artifact therefore declares provenance through the mandatory adjacent
`<file.cli>.provenance.json` specified by SPEC-PROVENANCE. The companion's
artifact schema is `org.openwepp.cligen.cli.text`, version 1. The optional
quality report repeats the same provenance; disabling quality never disables
the mandatory companion. Its content SHA-256 binds the companion to the exact
text bytes.

## Acceptance

- all 12 goldens are byte-identical before and after A1;
- continuous/observed text and Parquet consume the same generated f32 rows;
- deprecated storm text retains its independent source-calendar behavior and
  is not forced through Gregorian `ClimateRowV1`;
- header and daily projections are tested independently;
- no provenance field is inferred by parsing the arbitrary command echo.
