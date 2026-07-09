# Repository Scaffold

Status: `EXECUTED-COMPLETE`
Date: 2026-07-09
Evidence mode: Mixed — docs authored (Static analysis of the Fortran
source); build gates Ran at close.

## Objective

Stand up the cligen-rs repository: posture decision, governance DNA
(deliberately slimmed from openWEPP), first-pass Fortran decomposition,
forward-only roadmap, vendored reference source, and an empty-but-building
Rust workspace.

## What landed

- `README.md`, `CLAUDE.md`, `AGENTS.md` — identity, operating guides,
  gates.
- `docs/decisions/0001-source-code-authority-port.md` — the founding
  posture: Fortran source as faithful-mode specification; dual
  faithful/native modes; versioned generation profiles; fixture provenance
  rules; the kept/excluded openWEPP DNA list.
- `docs/specifications/README.md` — lightweight spec model + registry
  (SPEC-PAR, SPEC-CLI-TEXT, SPEC-CLI-PARQUET, SPEC-OBSERVED-INPUT,
  SPEC-GENERATOR-CORE, SPEC-PROVENANCE, SPEC-PYO3 planned).
- `docs/port/fortran-decomposition.md` — first-pass unit inventory
  (30 subprograms, 13 common blocks), functional clusters, proposed Rust
  module map, port order, known hazards. Marked draft; ratification is
  roadmap item 2.
- `docs/ROADMAP.md` — port queue (fixtures → decomposition → RNG/deviates
  → par/monthlies → daily → storm → observed → output parity) then
  augmentations (provenance/parquet first).
- `docs/work-packages/` — this record + template + catalog.
- `reference/cligen532/` — vendored CLIGEN 5.32.3 source (`cligen.f`,
  13 `.inc`, `makefile`) + `PROVENANCE.md` (public domain; upstream and
  local 5.322/5.323 lineage).
- Rust workspace: `crates/cligen` stub lib, pinned stable toolchain.

## Notable analysis findings (Static, from targeted source reads)

- `RANDN` is pure integer arithmetic — the RNG is trivially
  bit-replicable.
- `DSTG` contains `double precision` islands — the faithful-mode precision
  map is heterogeneous and must be audited unit-by-unit.
- Meyer's recode ships built-in distributional self-tests (`chitst`,
  `ks_tst`, `conflm`, `confls`) — a free second validation instrument.
- The in-line changelog documents the storm-duration/`DSTG` bug history —
  a ready-made pinned-test list for roadmap item 6.

## Gates

Ran at close: `cargo fmt --check`, `cargo clippy --all-targets -- -D
warnings`, `cargo test` (stub crate), results in
`artifacts/gate-results.md`.

## Follow-ons

- License for the Rust code not yet declared (operator decision).
- Roadmap item 1 (reference build + golden fixture harness) is the next
  package; nothing may port before it.
