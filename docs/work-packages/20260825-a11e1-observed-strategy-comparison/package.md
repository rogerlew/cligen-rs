# A11E1 — Observed Exploratory Strategy Comparison

Status: `ACTIVE`

Date: 2026-08-25

Evidence mode: observed development; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Execute the first source-bound comparison of two integrated A11E strategies on
the same authenticated candidate-fit corpus and 20 role-correct development
stations, using a two-part physical adapter and mask-normalized calendar
estimands.

## Authority

- `SPEC-A11-EXPLORATORY-STRATEGY-LAB`
- `SPEC-A11-OBSERVED-EXPLORATORY-EXECUTION`
- `SPEC-A10-CORPUS`
- published base implementation `b842430cb665a1219e01061312357688e04e6c62`

The operator authorized this bounded exploratory run, not confirmation or
production access.

## Scope

Included: published execution source; complete identity/calendar preflight;
candidate-fit-only adapter and strategy fitting; conditional five-fold annual
strategy diagnostics; 16-year daily development streams for 20 stations, two
strategies, and one member; descriptive paired site bootstrap; review; gates;
and terminal campaign reconciliation.

Excluded: confirmation, fit-validation scoring, WEPP, storm/context fields,
public profiles, output-selected fallback, and mutation of executed identities.

## Review disposition carried into execution

The scaffold review returned HOLD on the first draft. Before publication this
package replaces the relabeled fit-validation roster with actual development
objects, registers new integrated strategy IDs, adds dry-month mass, freezes the
leap-mask-normalized estimand, removes stale PRISM/roster dependencies, makes
the schema strict, and authenticates the published source and complete inputs.
The original HOLD remains recorded in `artifacts/review.md`; observed execution
may begin only after the corrected source passes review and is pushed.

## Plan and gates

1. Publish the exact implementation, specification, manifest, schema, and tests.
2. Verify all source/input identities and calendar objects before fitting.
3. Fit both strategies on candidate-fit data only and run conditional CV.
4. Generate and evaluate 40 development streams.
5. Review evidence, run repository gates, close, commit, and push.

Required gates are synthetic tests, strict manifest validation, complete A10
preflight, zero role leakage and confirmation access, 40 complete streams, zero
daily invariant failures, independent review with no unresolved P0/P1,
`cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`,
`git diff --check`, and changed-document link validation. No production Rust
function changes occur, so coverage/CRAP is not triggered.

## Exit

Complete with a descriptive disposition for each arm and no authority beyond
development. Hold on source, calendar, role, numerical, support, evidence, or
review failure, naming the smallest corrective successor. A lower composite
score is not a promotion decision.

## Artifacts

- `artifacts/execution-manifest-v1.json` and strict schema
- `artifacts/execute.py` and `artifacts/test_execute.py`
- calendar, fit, conditional-CV, development evidence, decision, and receipt
- `artifacts/test-results.md` and `artifacts/review.md`
