# A12R4 — Station Source CLI and Runtime

Status: `EXECUTING — IMPLEMENTATION GO`

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
