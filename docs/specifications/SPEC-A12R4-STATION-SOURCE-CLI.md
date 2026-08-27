# SPEC-A12R4-STATION-SOURCE-CLI — PRISM station-source runtime

Status: revision 1; active implementation contract

## Surface and authority

This specification governs station-source choice for `cligen prism run`. It
implements the operator decision following A12R3: closest ordinarily
localizable is the automatic default; exact user sources and the two evaluated
heuristics remain explicit alternatives. This is a preprocessing extension,
not faithful-generator behavior. The unchanged faithful generator still runs
from the localized `.par` emitted by this surface.

The exploratory evidence authority is A12R3 source commit
`5644a89185b087f7be2eb4b415db4a06a92203d4`, evidence SHA-256
`5711af00c28fa4d55a9af913024fe1ddf2b9460496a053a929be4c1d77c91e3d`,
and decision SHA-256
`243ef5d529dddb518fb4f01ce9337362189fdcde6214ca9369cd159b5e027b16`.

## CLI contract

`cligen prism run` accepts one station-source request:

- no station option, or `--station-selection closest-localizable`: the default;
- `--station-selection prism-rank-sum-localizable`;
- `--station-selection elevation-prism-reference-localizable
  --target-elevation-m <metres>`;
- `--station-id <exact-id>`: exact case-sensitive ID in registered
  `us-2015@2026.07`; or
- `--station-par <path>`: exact legacy `.par` bytes at that path.

The three source axes are mutually exclusive. `--target-elevation-m` is finite
and required only for elevation-reference selection. Existing longitude,
latitude, years, output, and optional repair arguments remain required or
optional as before. Selection never touches the network.

## Automatic selection

Automatic modes construct exactly the nearest ten `us-2015` candidates by
haversine distance and station-ID tie break. Compute all ranks over the full
ten before filtering. Parse and hash all ten source `.par` files, execute the
complete ordinary six-row localization algebra including F6.2 render/reparse
and encoded constraints, and record each eligibility result and first rejection
reason. Malformed, unreadable, or identity-drifting station data is fatal; only
a scientifically valid parse that cannot complete ordinary localization is an
ineligible candidate.

Choose among eligible candidates without reranking:

- closest: `(distance, station_id)`;
- current rank-sum: `(distance_rank + latitude_rank + 3*ppt_rank +
  1.5*tmax_rank + 1.5*tmin_rank, distance, station_id)`;
- elevation reference: `(distance_rank + latitude_rank + elevation_rank +
  3*ppt_rank, distance, station_id)`, where elevation error is absolute metres.

Station elevation comes only from the parsed `.par` `elev` field, stored as
integer feet, converted to metres by multiplication with exact f64 `0.3048`.
The parser always supplies an integer; a non-finite target elevation is invalid.
Elevation errors rank ascending with station-ID tie break. Candidate receipts
include station elevation feet/metres, target elevation metres, elevation
error/rank, and reference score for elevation mode. In the other automatic
modes, target elevation, elevation error/rank, and reference score are JSON
`null`; common current-selector components/ranks and current score are still
computed and reported for all automatic modes.

If no candidate is eligible, fail atomically. There is no silent switch between
selectors and no expansion beyond ten.

## Exact sources

`--station-id` resolves exactly one registered ID and never substitutes another
station. `--station-par` canonicalizes and reads exactly the requested file;
its stable receipt identity is `external-par:<sha256>`. Both sources are parsed,
hashed, localized, and validated. Ordinary failure is terminal unless the user
explicitly requested the existing repair method and that method covers the
failure. Exact sources do not synthesize an automatic candidate pool.

Station ID matching is byte-for-byte, case-sensitive equality against the
catalog `par` column. Zero or more than one matching row is an error, even if
multiple rows would resolve to the same bytes. Its stable source identity is
`registered:us-2015@2026.07:<id>`.

An exact `.par` request may name a symlink. The receipt retains the lexical
requested path and the canonical resolved path. After canonicalization, read
the file exactly once; that immutable byte snapshot is the sole input to
SHA-256, parse, localization, `source-station.par`, and provenance. Later path
mutation cannot change the run. An unreadable/dangling symlink or non-file is
an atomic error.

Automatic eligibility always means ordinary localization and is unaffected by
`--degenerate-occurrence-repair`. Thus an automatic request with the repair
flag selects the same donor as without it and normally records zero repairs.
The repair method can rescue only an exact ID/file request; it never changes
the automatic candidate filter.

## Method and receipt identity

This behavior advances the preprocessing profile to
`stochastic_prism_localized_par_v2`. Repair runs use
`stochastic_prism_localized_par_v2_degenerate_occurrence_independent_v1`.
The station-selection receipt advances to schema 3 and records:

- requested and effective selection method IDs (equal in revision 1);
- `fallback_applied: false`;
- exact requested station ID or requested `.par` path when applicable;
- collection identity when applicable;
- complete automatic candidate rows with source `.par` SHA-256, both selector
  scores/ranks, ordinary-localizable status, and rejection reason;
- selected source ID/path/SHA-256; and
- exact executing cligen binary SHA-256.

The five frozen method IDs are `closest_localizable_v1`,
`cligen_prism_rank_sum_localizable_v1`,
`elevation_prism_reference_localizable_v1`,
`exact_registered_station_id_v1`, and `exact_par_file_v1`. Automatic receipts
contain exactly ten candidate rows and a rejection record for every ineligible
row. Candidate common fields are station metadata/path/source SHA-256,
distance, latitude/precipitation/Tmax/Tmin errors and ranks, current score,
ordinary eligibility, and nullable rejection reason. Elevation-only fields use
the null rule above. Exact-source receipts contain zero automatic candidates
and zero candidate rejections, plus their requested identity fields and stable
selected-source identity. No schema field is omitted conditionally.

`request.json`, `method.json`, runspec command provenance, localization,
artifact manifest, source `.par`, and selection receipt agree on the requested
and effective mode and profile. The top-level artifact manifest hashes every
artifact and the executable. Failure publishes no output directory.

## Acceptance

Tests and execution evidence must cover default behavior, each heuristic,
elevation validation, exact ID, exact `.par`, argument conflicts, unlocalizable
candidate filtering, no-eligible failure, exact-source no-fallback behavior,
source/executable hashes, atomic failure, receipt agreement, and deterministic
repeatability. Existing ordinary and repair localization vectors remain green.
Human documentation must provide runnable examples and explain selection,
failure, provenance, and the lack of silent fallback.

Acceptance also covers zero/duplicate exact-ID resolution, lexical/canonical
symlink receipts, dangling/non-file input, mutation after the one-time read,
null elevation fields outside elevation mode, complete elevation fields within
it, and invariant automatic selection when the repair flag is toggled.
