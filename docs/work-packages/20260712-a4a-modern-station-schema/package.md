# A4a — Modern Fixed-Monthly Station Schema + Lossless Adapter

Status: `EXECUTED-COMPLETE`
Date: 2026-07-12
Evidence mode: Mixed
Execution model: single integrated implementation with delegated read-only
architecture, interface, and corpus preflights; Codex is the executor. Start
from current `origin/main`; push target is `main` only on operator direction.

## Objective

Execute ROADMAP A4a: add an independently versioned, unit-explicit,
provenance-bearing station document for the existing fixed-monthly CLIGEN
5.32.3 model. Legacy `.par` and modern station documents must converge on one
typed state before generation, without changing faithful calculations, random
draw order, or `.cli` bytes.

## Scope

Included:

- `SPEC-STATION-DOCUMENT` and a Draft 2020-12 JSON Schema for deterministic
  `*.station.json` documents;
- a syntax-independent `FixedMonthly5323` typed station state preserving every
  currently parsed `f32`, `i32`, and fixed-width string;
- deterministic legacy `.par` → modern-document conversion with legacy-source
  SHA-256 lineage and no timestamp/path-dependent fields;
- `cligen stations convert` with fail-closed overwrite behavior;
- SPEC-RUNSPEC revision 6: exactly one of `station.par` or
  `station.document`, with no extension sniffing;
- typed-state generation and quality-target seams; the quality report's
  existing `par_sha256` field uses the converted document's declared legacy
  source hash until A1 introduces generic station-input identities;
- fixture, malformed-input, deterministic-serialization, typed-state,
  `sta_parms`, quality-sidecar, and 12-golden modern-intake gates;
- a non-default full scan over the five hash-pinned Q2 collections.

Excluded:

- yearly SD, covariance, Fourier/EOF, or any other interannual fields;
- a new generation profile or any generation-behavior change;
- SI conversion, fixed-width `.par` regeneration, mutation/localization, and
  repair of malformed upstream station payloads;
- typed/Parquet climate output and A1 provenance;
- observed Parquet input, PyO3, and single-storm changes.

## Authority

- Faithful station values: `reference/cligen532/cligen.f:2459,2753-2815,
  2881-2927` and SPEC-PAR. Load-time feet→metres and intensity→depth
  conversions remain solely in `sta_parms`.
- Faithful generation: ADR-0001 and SPEC-FAITHFUL-GENERATION; the 12 golden
  `.cli` files are the trajectory authority.
- Extension surface: SPEC-STATION-DOCUMENT and SPEC-RUNSPEC revision 6. The
  station-file schema, station-model identifier, generation profile, and
  output schema are independent compatibility axes per the 2026-07-12 roadmap
  ruling.

## Plan

1. Record serialization, losslessness, unit, lineage, and corpus decisions;
   author specifications and machine schemas before integrating the runtime.
2. Extract the shared fixed-monthly typed state from `ParFile`; implement the
   strict modern DTO and deterministic legacy adapter.
3. Integrate exactly-one runspec intake, the typed generation seam, the
   quality-report bridge, and the explicit converter command.
4. Add executable fixture, malformed-input, snapshot, quality, CLI, and
   golden-parity gates.
5. Run the collection-wide ignored gate and every repository/complexity gate;
   record results, review the diff, close the package, move A4a from ROADMAP to
   the work-package catalog, and leave A1 active.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`
- Four fixtures: `.par` → document → parse has exact integers/strings and
  bit-identical `f32` values, including negative zero.
- Four fixtures × interpolation 0..3 reproduce existing `sta_parms` snapshots.
- All 12 golden runs through modern station documents reproduce `.cli` and
  quality sidecars identically to their legacy-station counterparts.
- Wrong/missing schema, model, units, fields, shapes, non-finite values,
  invalid station type, both/neither runspec sources, and output collisions
  fail closed with typed errors.
- The ignored Q2 corpus scan reports every catalog row and requires exact
  modern round-trip identity for every legacy-parseable station; inherited
  malformed `.par` rows are counted separately, never normalized.

## Exit criteria

`EXECUTED-COMPLETE` requires all default and complexity gates green, all
fixture/parity requirements satisfied, deterministic JSON validated against
the published schema, and collection evidence recorded with zero adapter
mismatches among legacy-parseable rows. A legitimate hold names either a
faithful parity failure, a non-round-tripping `f32`/string corpus case, or a
schema defect that cannot be corrected without changing fixed-monthly model
state.

## Artifacts

- `artifacts/design-decisions.md` — serialization, compatibility axes,
  losslessness, lineage, and corpus preflight.
- `artifacts/collection-scan.md` — five-collection Ran evidence.
- `artifacts/gate-results.md` — commands, exit codes, and test counts.
- `artifacts/review.md` — final implementation/spec review and dispositions.

## Closeout

All exit criteria passed on 2026-07-12. The adapter preserved every typed
value for all 18,077 legacy-parseable rows in the five pinned Q2 collections;
42 inherited malformed rows remained fail-closed. Both station intake paths
reproduced all 12 faithful `.cli` goldens and identical quality sidecars. A4a
is removed from the forward-only roadmap, and A1 is the next active package.
