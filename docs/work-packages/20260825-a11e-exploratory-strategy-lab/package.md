# A11E — Exploratory Stochastic-Generator Strategy Lab

Status: `EXECUTED-COMPLETE`

Date: 2026-08-25

Evidence mode: Mixed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Replace A11's brittle one-shot confirmatory posture with a versioned,
research-only strategy laboratory that can compare different non-neural
annual/monthly generators while preserving honest provenance. Implement two
initial strategies and a shared conditional daily core, validate them on
synthetic fixtures, and publish the exact source before any observed-data
execution.

## Scope

Included:

- an additive strategy registry with immutable per-strategy IDs;
- explicit permission for exploratory results to motivate later registered
  strategies;
- within-site standardized variation fitting;
- a latent Gaussian scalar-AR(1) strategy;
- a fixed-length circular block-bootstrap strategy;
- deterministic annual/monthly covariance reconciliation;
- a support-valid joint precipitation/wet-count law;
- exact-count occurrence, exact-total amounts, conditioned temperature, and
  positive-range daily primitives;
- strict configuration validation, synthetic fixtures, reproducibility tests,
  review, and source publication.

Excluded:

- observed Daymet fitting or development output in this package;
- confirmation data, promotion, public generation profiles, or consumer
  integration;
- claiming storm/context/WEPP capability for the initial core-only strategies;
- output-selected fallback or changing an executed strategy in place.

## Authority

- `SPEC-A11-EXPLORATORY-STRATEGY-LAB` defines the research interface.
- ADR-0001 keeps the work isolated from faithful behavior.
- The prior `20260825-a11-forced-monthly-annual-stochastic-generator` terminal
  supplies defect findings, not reusable scientific evidence.

The operator's 2026-08-25 direction explicitly selects an exploratory posture
and authorizes flexible strategy development.

## Plan

1. Freeze the laboratory rules and two initial strategy manifests.
2. Implement strict registry/config parsing and shared numerical primitives.
3. Implement both initial annual strategies.
4. Add synthetic tests for leakage prevention, persistence, reconciliation,
   support, exact conditioning, replay, and malformed inputs.
5. Run independent review and repository gates, then commit and push the exact
   source to `main` before observed-data execution.

## Data calendar and missingness preflight

Not applicable to this implementation package: it consumes only synthetic
fixtures. A later observed-data execution must complete the full per-object
`SPEC-A10-CORPUS` preflight before fitting.

## Execution and dispatch

Work runs locally from current `origin/main` and pushes only to `main`. This
package deliberately produces no observed-data strategy output, eliminating
the prior uncommitted-source identity failure. A later execution names this
package's published commit as its source.

Published implementation source:
`b842430cb665a1219e01061312357688e04e6c62` on `origin/main`.
This package produced synthetic evidence only. Any observed-data execution
must use that commit or register a new source/strategy revision before output.

## Gates

- strict manifest validation and mutation tests;
- package-local synthetic unit tests with NumPy 2.3.5 / Python 3.12.13;
- deterministic replay and covariance/support fixtures;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`;
- `git diff --check` and local Markdown-link validation.

No production function under `crates/` changes, so coverage/CRAP is not
triggered.

## Exit criteria

Complete when both registered strategies and shared primitives pass synthetic
tests, the manifest is strict and hashable, review findings are dispositioned,
the roadmap/catalog/spec registry are reconciled, and the exact source is
published to `main`. Hold on invalid numerics, unversioned strategy behavior,
unresolved P0/P1 review findings, or repository-gate failure.

## Artifacts

- `artifacts/strategy-manifest-v1.json`
- `artifacts/strategy-manifest-v1.schema.json`
- `artifacts/strategy_lab.py`
- `artifacts/test_strategy_lab.py`
- `artifacts/test-results.md`
- `artifacts/review.md`
