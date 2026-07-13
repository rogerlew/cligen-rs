# A4a Design Decisions

Status: ratified for package execution, 2026-07-12

## Independent compatibility axes

The station-document schema version, station-model identifier, runspec
generation profile, and future typed-output schema version are independent.
The A4a document therefore carries no generation-profile or output-schema
field.

## Serialization

Use strict, pretty JSON with one trailing LF and the conventional suffix
`*.station.json`.

- `serde_json` is already a production dependency with `float_roundtrip`.
- JSON has an exact Draft 2020-12 machine-schema interpretation and excludes
  YAML tags, aliases, and non-finite scalar spellings.
- Struct field order, fixed arrays, pretty serialization, and the trailing LF
  follow the repository's deterministic quality-report precedent.
- The installed `serde_yaml 0.9.34+deprecated` remains limited to the existing
  runspec surface; A4a does not expand dependence on it.

Runspecs select `station.par` or `station.document` explicitly. Filename
extensions are never used to infer an input format.

## Shared state and losslessness

Both syntaxes produce one `FixedMonthly5323` before RNG initialization or
station distribution. The modern path never regenerates fixed-width `.par`
text.

“Lossless” means:

- exact `i32` values and exact fixed-width ASCII station strings;
- every `f32` compared by `to_bits`, including `-0.0`;
- exact 12-month, 16-direction, four-wind-parameter, and three-source ordering;
- unchanged `sta_parms` snapshots and faithful generated trajectories.

It does not mean reconstruction of source row labels, numeric lexemes, skipped
TP5 text, unread tail records, or line endings. The required source SHA-256
preserves the identity of those legacy bytes.

## Units and transformations

Schema version 1 retains source-native values and declares their units
explicitly: degrees north/east, feet, inches, inches/hour, degrees Fahrenheit,
Langleys/day, metres/second, percent, fraction, and years. No SI conversion is
performed. The faithful `sta_parms` unit conversions and the `timpkd(0:11)`
window quirk remain unchanged and occur exactly once.

## Lineage

The document requires the legacy `.par` source format and lowercase SHA-256,
plus adapter identity/version. It contains no timestamp or source path, so the
same source bytes and converter version produce identical document bytes.

Until A1 adds generic station-input identities, a modern run's quality report
retains the existing `par_sha256` field and fills it from this required legacy
source hash. Targets are computed from the shared typed state.

## Corpus preflight (Ran)

The five Q2 manifests were tokenlessly synced and hash-verified under the
gitignored `target/a4a-collection-scan`. Embedded manifest JSON SHA-256:
`86039805acc0a160cb44773b9f02d04cd68173690df34337d794ab5e727c96ef`.

Catalog rows: 18,119. Current faithful `ParFile` parse succeeds for 18,077:

| Collection | Parseable | Catalog rows |
|---|---:|---:|
| us-legacy | 2,642 | 2,642 |
| us-2015 | 2,765 | 2,765 |
| ghcn-intl | 12,662 | 12,704 |
| au | 7 | 7 |
| chile | 1 | 1 |

The 42 inherited ghcn-intl failures have station names longer than the
normative record-1 `A41` field, shifting the `I2` state-code columns; Fortran
and the faithful parser reject them. A4a reports these rows separately and
does not truncate or infer values. Directory walking also finds one
uncatalogued us-legacy `temp.par`; the acceptance scan follows the catalog of
record.

The parseable corpus contains 120 negative-zero fields across 108 stations.
This makes bitwise float comparison and explicit `-0.0` serialization hard
acceptance requirements rather than theoretical edge cases.
