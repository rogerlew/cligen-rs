# SPEC-PROVENANCE — Generated Climate Artifact Provenance

Status: active (revision 2; A8c adds independently versioned station/profile
vocabularies while retaining envelope schema version 1)
Surface: deterministic provenance shared by text companions, Parquet metadata,
and run-emitted quality reports.

## Purpose

Provenance says what produced one artifact without conflating independent
compatibility axes. It is not a replay bundle: hashes identify inputs, while
reproduction still requires their bytes. Producers are `cligen run` and the
library output API; consumers are operators, quality tooling, Parquet readers,
and future openWEPP/WEPPpy adapters.

## Canonical envelope

Revision 1 is a declaration-ordered JSON object with:

- `provenance_schema_version`: integer `1`;
- `producer`: cligen-rs name, package version, repository, and nullable
  implementation revision (null unless deliberately supplied at build time);
- `origin`: `generated`;
- `source_authority`: CLIGEN version `5.32.3` and the pinned reference-tree
  SHA-256 `24966eaed920c2b9fd0b8a9ab1242b32053a730f0691a6a18dc4f44a3096bd5b`;
- `station`: selected input schema ID/version, exact selected bytes SHA-256,
  station model ID, syntax-independent parameter-set SHA-256, explicit fit
  and collection status, and legacy-source lineage;
- `generation`: profile, nullable QC policy, mode, interpolation, and the
  profile-specific RNG scheme plus burn-per-stream (burn is not called a seed);
- `effective_runspec`: canonical resolved defaults and lexical paths;
- `effective_runspec_sha256`: SHA-256 of compact canonical JSON for that
  effective runspec and the `run_id` duplicated in Parquet columns;
- `observed_input`: null or its schema ID/version and exact bytes SHA-256;
- `actual`: emitted day count, first/last date, and coverage;
- `artifact`: output schema ID/version, media type, calendar,
  precipitation representation, numeric origin, and an exact text-content
  SHA-256 (`null` only for self-embedded Parquet provenance).

All SHA-256 values are 64 lowercase hexadecimal characters. Struct field order
is canonical; pretty JSON plus one LF is the companion rendering. There are no
maps, timestamps, UUIDs, host names, environment values, or absolute resolved
paths.

## Independent identities

| Axis | Revision-1 values |
|---|---|
| Station input schema | `cligen_par` / `5.32.3`, or `org.openwepp.cligen.station` / `1` or `/2` |
| Station model | `fixed_monthly_5_32_3` or `a8c_integrated_daily_v1` |
| Generation profile | `faithful_5_32_3`, `fast_batch_v0`, or `a8c_routed_daily_v1` |
| Text output schema | `org.openwepp.cligen.cli.text` / `1` |
| Parquet output schema | `org.openwepp.cligen.cli.parquet` / `1` |
| Provenance schema | `1` |

A change to one cell does not imply a change to another. The Parquet library
version belongs to producer/writer identity, not the climate output schema.
Faithful generation uses `cligen_randn_5_32_3`; the retired experimental
profile truthfully names `splitmix64_monthly_v0`.
The A8c routed profile names
`cligen_randn_5_32_3_plus_splitmix64_daily_v1`. Its station fit is reported as
the validated revision-2 `fit_id`; existing profiles retain the exact
`unreported` fit object. These are additions on independent versioned axes,
not a structural envelope change, so `provenance_schema_version` remains `1`
and existing faithful provenance bytes are unchanged.

## Station and fit identity

`station.input_sha256` hashes the exact selected `.par` or station JSON bytes,
so modern and legacy intake are truthfully distinct. `parameter_set_sha256`
hashes exactly the compact canonical JSON serialization of the modern station
document's declaration-ordered `parameters` object (`StationParameters`),
excluding schema/model/units/lineage; it is identical when legacy and modern
syntaxes represent the same model. `legacy_source_sha256` is the A4a lineage source.

Existing faithful and retired experimental-profile artifacts do not report
their fitter, target dataset, or fit revision. They therefore require:

```json
"fit": { "status": "unreported", "id": null }
```

The A8c profile instead requires one exact model/fit pair carried by its
validated revision-2 station document:

| Station model | Required reported fit ID |
|---|---|
| `a8c_integrated_daily_v1` | `a8a_o2_logqspline_gaussian_copula_v1` |
| `fixed_monthly_5_32_3` | `legacy_daily_only_v1` |

No path, station name, or source hash is relabeled as a scientific fit method,
and an A8c model or reported fit is invalid under any other generation profile.

Path-only runs also cannot prove that selected bytes came from a synced
SPEC-STATION-DB release. Revision 1 therefore requires
`collection: {status: unreported, name: null, version: null,
archive_sha256: null}` rather than inferring a collection from cache layout.
An explicit collection-aware selector is required before those three release
identities may be reported; this dispositions SPEC-STATION-DB's future
provenance obligation without fabricating lineage.

## Effective runspec and paths

The canonical effective runspec contains all materialized defaults,
mode-conditional values, lexical station/observed/output paths, exact input
hashes, and the final command echo. Lexical paths are retained verbatim, so an
operator-authored absolute lexical path remains visible. The producer never
adds a runtime-resolved filesystem path: inferred resolution is context, leaks
host/cache layout, and is already bound to bytes by hashes. This revision
supersedes SPEC-RUNSPEC revision 6's requirement to serialize resolved paths.

## Coverage

- `complete_run`: continuous output completed its requested span, or observed
  output reached its requested cap;
- `observed_source_end`: observed source EOF/sentinel ended the run first;
- `single_event`: legacy text only for single/design storm.

Continuous/observed artifacts use `proleptic_gregorian`. Legacy storm text
uses `source_storm_calendar`; A1 rejects a Parquet destination for storm modes.
For deprecated storms, the requested source-calendar date and the emitted row
date remain separate truths (for example, a source-calendar February 29 can
advance through the faithful date conversion before emission).

Counts and dates are cross-validated semantically: complete output exactly
matches the requested span; observed source-end output is a nonempty prefix;
single-event output has one date; and continuous/observed day counts equal the
inclusive Gregorian span. Generated years must fit the frozen text `i5`
surface (1–99,999; storm source years −9,999–99,999). Effective storm numeric
values and typed climate values must be exact finite f32 widenings.

## Canonicalization and machine validation

Compact declaration-ordered serde JSON is the revision-1 hash payload. Public
literal vectors pin both the effective-runspec digest and the fixed-monthly
parameter-set digest; serializer or field-order drift is therefore a contract
failure, not an implicit identity migration.

Language-neutral canonical bytes are UTF-8 with no BOM or insignificant
whitespace; object members occur in the declaration order published by the
schema/model structs; arrays retain source order; `null`/booleans/integers use
their lowercase/minimal JSON tokens; strings escape quote/backslash, use the
standard short escapes for `\b`, `\t`, `\n`, `\f`, `\r`, and `\u00xx` for
other C0 controls (non-ASCII scalar values remain UTF-8); finite floats use the
shortest round-tripping binary64 spelling while retaining the `.0` form for an
integral typed float and `-0.0` for negative zero. Exponents use lowercase `e`,
an explicit sign only when required by the pinned formatter, and no leading
zeroes (`e-7`, not `e-07`). The
revision-1 implementation pins `serde_json = 1.0.150`/`zmij` behavior. Acceptance
vectors pin a continuous payload/hash, a storm payload containing the exact
`0.4f32` widening `0.4000000059604645`, and the New Meadows parameter-set
hash. Independent implementations must reproduce those bytes and digests.
Pretty companions and compact metadata use identical scalar token lexemes.
An independent verifier may therefore extract the raw `effective_runspec`
subtree and remove only insignificant JSON whitespace with a token-aware
scanner; it must not parse and reformat numbers or strings before hashing.

The JSON Schema is the portable structural/closed-vocabulary validator.
Revision 1 is permanently published as `provenance-v1.schema.json`; the
unversioned filename is only a latest-version alias. Quality envelope v2
references the versioned provenance resource, never the mutable alias.
Cross-field equality and calendar arithmetic that Draft 2020-12 cannot express
(input-hash equality, burn/profile agreement, inclusive day counts, requested
span, and effective-runspec SHA recomputation) remain normative and are
implemented by `ArtifactProvenanceV1::validate`. Independent readers must
perform those semantic checks in addition to JSON Schema validation.

## Emission and failure

Every `.cli` gets `<file.cli>.provenance.json` even when quality is disabled.
Its `artifact.content_sha256` binds the companion to exact adjacent text bytes;
`verify_cli_bytes` implements the check.
Every `.cli.parquet` embeds canonical JSON under `cligen.provenance` and
duplicates discovery identifiers in scalar footer keys/columns. Unknown
versions, non-finite values, malformed hashes, missing identities, or an
unsupported mode/output pairing fail closed.

Successful bundle publication is serialized by a same-directory lock. The
implemented order is text, mandatory provenance, optional Parquet, then
optional quality. Each companion and Parquet file is staged and atomically
renamed; the multi-file bundle is not a filesystem transaction, so a later
I/O failure may leave the successfully published prefix and returns an error.
