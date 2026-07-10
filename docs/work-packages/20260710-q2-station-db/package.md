# Q2 — Station Databases + crates.io Deployability (SPEC-STATION-DB)

Status: `SCAFFOLDED`
Date: 2026-07-10
Evidence mode: — (set at close; evidence in `artifacts/gate-results.md`)
Execution model: single-executor (operator direction, 2026-07-10 —
the staged S/C split is forgone for this package's shape): Claude
Code executes end-to-end, then dispatches Codex for the review pass
and dispositions its findings.

## Objective

Close ROADMAP Q2: a typed station database over the five production
collections (`jimf-cligen532/db`), a `cligen stations` subcommand
(list / nearest / sync), and crates.io deployability with **data
shipped outside the crate** — hash-pinned collection manifests
in-crate, payloads fetched to a local cache only by the explicit
`sync` subcommand. Simulation and `run` never touch the network.

## Scope

Included (operator rulings 2026-07-10 folded in: GitHub hosting;
payloads are **verbatim trees, include everything**; SQLite catalogs
**ship** — python is the catalog producer, Rust consumes):
- SPEC-STATION-DB (new, `docs/specifications/`): manifest schema,
  payload format, catalog-to-file resolution, cache layout,
  nearest-query semantics, sync verification, network posture.
- Payload build: one `.tar.gz` per collection — the verbatim
  collection tree plus its python-produced SQLite catalog at the
  payload root — SHA-256 pinned in embedded manifests; hosted as
  GitHub release assets on this repo.
- `crates/cligen/src/stations/`: embedded manifests, cache
  resolution, `sync` (https with optional bearer token, `--from`
  air-gap source, hash-verified before extraction, traversal-guarded,
  catalog cross-checked), haversine nearest over the shipped catalog
  with pinned tie-break (stable under the known GHCN duplicate-record
  quirks — 63 coordinate collisions, 158 duplicate names, carried
  as-is).
- `cligen stations list | nearest | sync` subcommands.
- Acceptance evidence per the Q2 ROADMAP row.

Excluded:
- crates.io **publication** (only `--dry-run`; publishing is an
  operator action).
- PRISM localization and all par mutation (A4).
- Runspec coupling (no station-by-id field in `inp.yaml`; `nearest`
  emits cache paths that feed `station.par` as ordinary paths).
- Payload-hosting visibility policy: the repo is currently private,
  so release-asset fetch requires a token (`CLIGEN_SYNC_TOKEN`);
  making the data publicly fetchable is an operator decision recorded
  at close.
- Catalog production or repair: the SQLite catalogs are
  python-produced and ship verbatim; Rust never creates, mutates, or
  deduplicates them.

## Authority

Extension surface (no Fortran authority): SPEC-STATION-DB, authored
in this package. The typed `.par` read is SPEC-PAR's `ParFile`.
FSWEPP's `climNearest` is historical reference for the nearest-query
role, not behavioral authority. Collection inventory: operator
correction 2026-07-10 + Ran survey of `/workdir/jimf-cligen532/db`
(counts, GHCN duplication proof, payload health census) —
`artifacts/design-notes.md`.

## Plan

1. Survey collections; pin design decisions (`design-notes.md`).
2. SPEC-STATION-DB before code.
3. Build + hash payload archives; create the GitHub release; embed
   manifests.
4. Implement `stations` module + subcommands + tests (the au
   collection, 7 pars, vendored as the in-repo fixture collection).
5. Evidence: independent-Python nearest oracle across all five
   collections; fresh-install → `sync` → `nearest` → `run` round-trip
   (target: byte-identical golden — `2015_par_files/id106388.par` is
   byte-identical to the golden fixture par, verified Ran);
   `cargo publish --dry-run` under the size limit; full gates.
6. Dispatch Codex review (MCP); disposition; remediate; close.

## Gates

- `cargo fmt --check`; `cargo clippy --all-targets -- -D warnings`;
  `cargo test --release`; ignored identity suites (must be untouched
  by this package); `cargo llvm-cov` + `cargo crap` (CRAP ≤ 30, no
  allow-lists); `cargo deny check` (new dependencies: http client +
  tar + flate2).
- Q2 acceptance rows (all Ran, exit codes direct):
  `cargo publish --dry-run` clean under the crates.io size limit with
  data excluded; fresh `cargo install --path` + `cligen stations
  sync` + `cligen run` round-trip; manifests carry SHA-256 +
  provenance lineage; nearest matches the pinned independent oracle.

## Exit criteria

`EXECUTED-COMPLETE` after the review cycle closes with findings
dispositioned. Legitimate holds: payload hosting blocked (falls back
to `--from` evidence + named operator decision), or a dependency
failing `cargo deny` with no lean alternative.

## Artifacts

- `artifacts/design-notes.md` — survey evidence + design rulings.
- `artifacts/gate-results.md` — Ran gate + acceptance evidence.
- `artifacts/payload-build.md` — archive build commands, hashes,
  exclusions.
- `artifacts/review-codex.md` / `artifacts/disposition-claude.md` —
  the review cycle.
