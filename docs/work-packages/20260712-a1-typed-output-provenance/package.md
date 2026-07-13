# A1 — Independently Versioned Typed Output and Provenance

Status: `EXECUTED-COMPLETE`
Date: 2026-07-12
Evidence mode: Mixed
Execution model: one integrated implementation with delegated read-only
architecture, Parquet, and contract audits. Start from current `origin/main`;
push target is `main` only on operator direction.

## Objective

Execute ROADMAP A1: retain the generator's pre-format daily values as a public,
versioned typed row stream; add an optional deterministic `.cli.parquet`
companion; and attach complete, independently versioned provenance without
changing one byte of legacy `.cli` output.

## Scope

Included:

- SPEC-CLI-TEXT, SPEC-CLI-PARQUET, and SPEC-PROVENANCE;
- `ClimateRowV1`, derived by exact `f32` to `f64` widening from the existing
  faithful `DailyRow` stream before legacy formatting;
- optional `output.parquet` while `output.cli` remains required;
- parametric continuous and observed Parquet output, including observed
  source-end coverage;
- required field units/descriptions, canonical footer metadata, and Zstandard
  Parquet 2.0 physical policy pinned to arrow-rs 59.1.0;
- mandatory `<output.cli>.provenance.json` and the same shared provenance in
  Parquet metadata and run-emitted quality reports;
- independently named station-input schema, station model, parameter-set/fit,
  generation profile, output schema, input sources, and writer/source
  authority identities;
- quality-report envelope versioning independent of `metrics_version`;
- same-directory staged Parquet publication and fail-closed collision policy;
- Rust and independent PyArrow interoperability evidence where available.

Excluded:

- Parquet-only runs; `output.cli` remains required in A1;
- single/design-storm Parquet, breakpoint precipitation, or legacy `.cli`
  import/conversion (the deprecated storm surface remains a later companion);
- observed Parquet input, f64 substitution, leap imputation, or A3 behavior;
- openWEPP/WEPPpy consumer implementation;
- fitted-model metadata absent from current station artifacts: its status is
  recorded as `unreported`, never inferred;
- native-f64 generation or any generator/RNG/model behavior change.

## Authority

- Typed values and legacy formatting: `reference/cligen532/cligen.f:3055-3056,
  3175-3176,3722-3754` and the 12 faithful goldens.
- Station/schema/model separation: SPEC-STATION-DOCUMENT and A4a.
- Extension surface: SPEC-CLI-PARQUET revision 1, SPEC-PROVENANCE revision 1,
  SPEC-RUNSPEC revision 7, and SPEC-QUALITY-REPORT revision 7.
- Quality vector authority: ADR-0002. A1 changes its envelope, not its metric
  vector; `metrics_version` remains 2.

## Plan

1. Record output selection, schema, numeric, provenance, fit, path, calendar,
   coverage, and publication decisions; author specifications first.
2. Retain one generated typed row stream and project it independently into the
   frozen `.cli` renderer and semantic `ClimateRowV1` values.
3. Implement canonical provenance and integrate station/observed/runspec
   identities before their lexical/source information is discarded.
4. Implement the pinned Parquet writer and output orchestration, including
   collision preflight and staged publication.
5. Add exact-row, schema, metadata, provenance, quality, parity,
   interoperability, malformed-input, and publication gates.
6. Run repository and complexity gates, review the complete diff, close A1,
   remove it from ROADMAP, and leave A5a active.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`
- All 12 legacy `.cli` goldens remain byte-identical with Parquet absent; the
  10 continuous/observed cases remain byte-identical with Parquet enabled.
- Parquet rows equal exact widened pre-format values, including signed zero
  and f32-boundary vectors; no text reparse is permitted.
- Published field order, Arrow/Parquet types, nullability, units,
  descriptions, footer identities, and canonical provenance validate exactly.
- Legacy and modern station syntax produce identical climate values/date
  indices after excluding the deliberately syntax-bound run ID; their
  parameter hashes match while run IDs and input schema/byte identities remain
  truthfully distinct.
- Canonical effective runspecs contain resolved defaults, lexical paths, and
  content hashes; no runtime-resolved path or timestamp is inferred, and
  repeated emission is deterministic. A user-authored lexical path is retained
  verbatim even when that lexical value is absolute.
- Continuous year 1/leap behavior and observed early-source-end coverage are
  explicit; storm Parquet, malformed fields, collisions, and non-finite rows
  fail closed.
- A writer failure cannot expose a partial final Parquet file.
- Quality report metrics remain unchanged while its independently versioned
  envelope carries generic station content and shared run provenance.

## Exit criteria

`EXECUTED-COMPLETE` requires every gate above, an adversarial review with no
open P1/P2, a published schema/provenance record sufficient for independent
readers, and no `.cli` divergence. A legitimate hold names a faithful byte
regression, a pre-format value that cannot round-trip through the selected
Parquet physical type, an interoperability failure, or a provenance identity
that cannot be stated truthfully from retained inputs.

## Artifacts

- `artifacts/design-decisions.md` — specification rulings and dependency pin.
- `artifacts/gate-results.md` — commands, versions, counts, and hashes.
- `artifacts/interoperability.md` — independent reader evidence.
- `artifacts/review.md` — final review and dispositions.

## Closeout

Executed complete on 2026-07-12. All repository, faithful-parity, schema,
interoperability, publication, coverage, and CRAP gates passed. The final
adversarial review verdict was **ACCEPT**, with no P1/P2 findings and four
non-blocking P3 follow-ups recorded in `artifacts/review.md`. A1 leaves the
legacy text format frozen and advances A5a to the active roadmap head.
