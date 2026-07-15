# A5f1 — Retired A5e0 Runtime Cleanup

Status: `EXECUTED-COMPLETE`
Date: 2026-07-14
Evidence mode: Mixed
Execution authorization: operator authorized execution on 2026-07-14

## Objective

Remove the unshipped, retired A5e0 experimental runtime from the current Rust
crate while preserving its immutable scientific record and historical
reproducibility. This is retirement hygiene after A5f0; it does not add a
replacement climate mechanism or change faithful behavior.

## Scope

Included:

- audit crates.io, repository releases/tags, package version, and source
  history to determine whether the public `cligen::a5e0` module shipped;
- capture a hash manifest of every runtime file to remove and the principal
  A5e0/A5f0 records that must remain;
- remove `crates/cligen/src/a5e0.rs`, its crate-root export, the A5e0 example
  runner, and the package-local generator hook;
- remove exact-skip, period, raw-update accounting, and tests added only for
  A5e0 faithful-stream partition evidence;
- restore the ordinary resolved-generation path to a single faithful/native
  entry without an optional retired extension branch;
- update the specification registry, roadmap, and work-package catalog; and
- verify faithful byte parity, package contents, public-surface absence, and
  the complete repository/coverage gates.

Excluded:

- deletion or rewriting of A5e0/A5f0 specifications, schemas, reports,
  campaign artifacts, review records, or coefficient evidence;
- rewriting historical producers so they execute from current `main`;
- removal of any generic RNG primitive with an independently documented
  non-A5e0 consumer;
- a replacement annual state, A7 precipitation behavior, public profile,
  station schema, output schema, or default change; and
- a new crate release or crates.io publication.

## Authority

- [ADR-0001](../../decisions/0001-source-code-authority-port.md) protects the
  faithful generator and its reference authority.
- [ADR-0004](../../decisions/0004-a5b-interannual-no-promotion.md) prohibits
  promotion of the failed research candidates.
- [A5f0](../20260714-a5f0-annual-state-failure-attribution/package.md)
  retires only `a5e0_direct_annual_state_v1` with its exact fit recipe.
- The operator-ratified [roadmap](../../ROADMAP.md) directs removal when the
  surface is unshipped and semver-safe deprecation only if it shipped.
- The active Rust scientific coding standard governs all touched generator
  code; no faithful numerical expression is intentionally changed.

## Release-exposure decision

The package audit found no published `cligen` crate: both the official
crates.io API and exact sparse-index object returned HTTP 404, and crates.io
reported that crate `cligen` does not exist. The repository's only two release
tags predate A5e0; the A5e0 implementation first appeared at commit
`1ca40bbe006ed5d823d2dd8e373f720f20d60ba0`. The workspace remains version
`0.1.0`. Removal, rather than a deprecation layer, is therefore the selected
path. Exact Git dependencies can continue to use the historical implementation
commit.

## Plan

1. Scaffold this package and capture the clean `9eada92` baseline manifest.
2. Remove only the runtime/export/example/generator/RNG surfaces identified in
   the manifest, using the pre-A5e0 source shape as a review comparator.
3. Preserve and verify the closed scientific record; mark only its registry
   status as runtime-retired.
4. Verify source absence, historical commit reachability, faithful byte parity,
   example/package contents, and package-specific invariants.
5. Run formatting, clippy, full tests, LLVM coverage, and CRAP; review and
   close the roadmap item.

## Execution result

The official registry and repository audit selected removal: no `cligen`
crate exists on crates.io, and no tag or release containing A5e0 exists. The
runtime module, example, crate export, generator branches, and A5e0-only RNG
partition utilities were removed. The affected runtime paths now exactly match
pre-A5e0 commit `27e5e7754bdfafcca649a71d0f5576910433d0d3`.

All pinned A5e0/A5f0 scientific records retained their pre-removal hashes, and
implementation commit `1ca40bbe006ed5d823d2dd8e373f720f20d60ba0`
remains reachable. The terminal disposition is `A5E0-RUNTIME-RETIRED`; A7a is
now the first active roadmap item.

## Execution & dispatch

This package executes locally on `main`, starting from clean commit
`9eada9229606667ff083f69fe968364dead31d10` and targeting `main`. No side
branch, pull request, release, or crates.io publication is in scope.

## Gates

- official registry/release exposure audit supports removal;
- baseline hashes exist for all removed and preserved records;
- no A5e0 runtime source, export, example target, generator hook, or A5e0-only
  RNG support remains under `crates/`;
- the A5e0 implementation commit remains reachable;
- pinned A5e0/A5f0 specifications, schemas, reports, and artifacts retain
  their baseline hashes;
- `cargo metadata` and `cargo package --list` contain no A5e0 runtime target;
- faithful `.cli` goldens remain byte-identical;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`;
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`; and
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`.

## Exit criteria

`EXECUTED-COMPLETE` requires an unshipped-removal decision, complete source
cleanup, unchanged historical records, faithful parity, review acceptance, and
all gates passing. The terminal scientific/engineering disposition is
`A5E0-RUNTIME-RETIRED`. If publication evidence is discovered after removal
was selected, the package holds `EXECUTED-HOLD-RELEASE-EXPOSURE` before code
changes. Any faithful parity or record-identity failure holds with no A7
authorization.

## Artifacts

- `artifacts/release-exposure-audit.md` — official registry and repository
  release evidence.
- `artifacts/capture-a5f1-baseline.py` — pre-removal manifest producer.
- `artifacts/a5f1-baseline-v1.json` — removed/preserved source identities.
- `artifacts/verify-a5f1.py` — retirement, preservation, and scope verifier.
- `artifacts/removal-inventory.md` — final surface disposition.
- `artifacts/review.md` — correctness and compatibility review.
- `artifacts/gate-results.md` — executed commands and outcomes.
