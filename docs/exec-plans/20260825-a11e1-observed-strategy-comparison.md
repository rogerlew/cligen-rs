# A11E1 observed exploratory comparison ExecPlan

## Purpose / Big Picture

Compare two integrated A11E strategies on real non-confirmatory development
data. Success is a reproducible diagnostic and a useful next hypothesis, not a
production winner.

## Progress

- [x] 2026-08-25: identified the published base source and authenticated local inputs.
- [x] 2026-08-25: independent review held the initial fit-validation/PRISM draft.
- [x] 2026-08-25: corrected role, strategy identity, dry support, calendar estimand, schema, and authentication design.
- [x] 2026-08-25: published initial corrected source and passed synthetic gates.
- [ ] Publish the pre-output daily-range correction and rerun.
- [ ] Preflight, fit, cross-validate, and execute development generation.
- [ ] Review, gate, publish evidence, and close.

## Decisions and discoveries

- Use the inherited 20 `development` objects from 2010–2025, not a
  `fit_validation` alias.
- Use a named 30.4375-day equivalent precipitation estimator and wet fraction
  so masked leap-year December 31 does not change the estimand.
- Use a two-part hurdle/positive law so generated dry months remain possible.
- Use candidate-region pooled locations because the available PRISM archive has
  no development station identities. This is deliberately a coarse exploratory
  forcing test.
- Use one member per site and label the paired bootstrap as spatially
  descriptive, not Monte Carlo uncertainty.
- The first published-source invocation failed before artifact publication on
  a candidate day with zero diurnal range. The specification requires a
  positive monthly mean, not a strictly positive daily range. The corrected
  source preserves that monthly value and censors only the daily log-texture
  input at 0.01 °C.

## Plan of work

The exact executor and contracts are committed and pushed before observed values
are read. Runtime then verifies `origin/main`, all source blobs, every candidate
shard, the cohort manifests, the development manifest, and all 20 objects. It
writes calendar evidence before fitting, compact fit/CV evidence before held-out
evaluation, then 40 aggregate-only stream receipts and a descriptive decision.

Run from `/Users/roger/src/cligen-rs` with the bundled Python 3.12 runtime:

```sh
python3 -m unittest -v docs/work-packages/20260825-a11e1-observed-strategy-comparison/artifacts/test_execute.py
python3 docs/work-packages/20260825-a11e1-observed-strategy-comparison/artifacts/execute.py --source-commit SOURCE_COMMIT --execute
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
git diff --check
```

Expected observations are 1,440 authenticated fit-corpus objects, 1,200 used
candidate-fit objects, 20 development objects, 40 streams, and zero invariant
failures. Execution is deterministic for the frozen source and inputs and uses
atomic compact JSON writes. Raw observed and generated streams remain local.

## Outcomes & retrospective

Pending execution.
