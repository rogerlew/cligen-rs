# A12R4 — Station Source CLI and Runtime

Status: `EXECUTED-COMPLETE — CLOSEST_DEFAULT`

Date: 2026-08-26

Starting branch and push target: current `origin/main`, push `main`

## Objective

Implement the operator-approved PRISM station-source interface: default
closest-localizable, exact registered station ID, exact `.par` path, and
explicit localizable current/elevation heuristics, with cryptographic
provenance and human documentation.

## Authority

- [SPEC-A12R4-STATION-SOURCE-CLI](../../specifications/SPEC-A12R4-STATION-SOURCE-CLI.md)
- [SPEC-A10-STOCHASTIC-PRISM-COMPARATOR](../../specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md)
- [A12R3 disposition](../20260826-a12r3-localizable-selector-quality/package.md)

## Plan

1. Freeze and independently review the public CLI, failure, selection, and
   receipt contract.
2. Implement selection/source types, full-ten feasibility filtering, exact
   source resolution, profile/receipt revisions, and CLI parsing.
3. Add focused unit/integration tests, deterministic end-to-end evidence, and
   human guide examples.
4. Run format, clippy, test, coverage, and CRAP gates; obtain independent GO.
5. Reconcile specification registry, package catalog, roadmap, and commit/push.

## Required gates

- selector and exact-source tests;
- end-to-end artifact/receipt hash verification and atomic failures;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`;
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`;
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`.

## Exit

Complete when every mode is implemented and documented, default behavior is
closest-localizable, exact sources never fall back, receipts carry source and
binary SHA-256 identities, gates pass, and independent review returns GO.

## Disposition

Completed at implementation commit
`1e558b553412bfdc0f1b61ccd5c331ced056de54`. `cligen prism run` now defaults
to `closest_localizable_v1`; the prior PRISM rank-sum and the evaluated
elevation-reference heuristic remain explicit modes. Users may instead request
one exact registered station ID or one exact `.par` file. No mode falls back.

Station-selection receipt schema 3 and preprocessing profile v2 bind requested
and effective method identity, full automatic feasibility evidence, selected
source `.par` SHA-256, and exact executable SHA-256. Full station semantics are
validated before feasibility classification. Exact files use one immutable byte
snapshot and retain lexical plus canonical path identity.

The release binary SHA-256 is
`a6491ed5e4b39dc52ae8fc2426cb7eef5a8fa1ee37e20bfc48df55c73ec7bac0`.
Default/replay artifacts were byte-identical; all success manifests and source
and binary identities verified; all declared failure cases published no output.
Repository, coverage, and CRAP gates passed, and independent final closure
review returned GO with no remaining P0/P1.

This is an exploratory selector surface, not a claim that the optional
heuristics improve climate quality. A12R3 remains the evidence for preferring
closest as the default. Future selector strategies can add distinct method IDs
without changing exact-source or no-fallback behavior.
