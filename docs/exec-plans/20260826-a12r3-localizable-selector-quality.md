# A12R3 Localizable Selector Quality — ExecPlan

Status: active

## Purpose

Execute the bounded localizability-only successor named by A12R2. This plan is
living operational guidance; the specification and package retain authority.

## Progress

- [x] Freeze the three arms, corpus, estimand, decision rule, and predecessor identities.
- [x] Obtain independent prospective review.
- [x] Commit and push prospective source.
- [x] Amend the prospective source inventory after its clean-build preflight
      exposed a nonexistent `distribution.rs` path before compilation.
- [x] Amend wet-day descriptor eligibility after the first staged science run
      found two sparse June cells; preserve the failed build receipt and bind
      the complete diagnostic before re-execution.
- [ ] Build the exact locked release binary and record its SHA-256.
- [ ] Execute the first 240-site evaluation.
- [ ] Execute a separately staged byte-identical replay.
- [ ] Obtain independent closure review and run all gates.
- [ ] Reconcile package, roadmap, catalog, and specification registry; commit and push.

The first complete/replay pair at source `6b42aa6` was preserved as attempt 1
after closure review found shared mutable station dictionaries had overwritten
582 site-specific published distances. Selection, hashes, metrics, inference,
and disposition reproduced, but evidence integrity did not. The corrected
source snapshots every selected arm immediately; it receives a new commit,
build receipt, execution, and replay.

## Commands

Use the bundled Python 3.12.13 / NumPy 2.3.5 runtime:

    python artifacts/evaluate.py --validate-manifest
    python artifacts/test_evaluate.py
    python artifacts/evaluate.py --build --source-commit <prospective-commit>
    python artifacts/evaluate.py --execute --source-commit <prospective-commit> \
      --cligen-binary target/release/cligen --build-receipt artifacts/build-receipt-v1.json \
      --station-archive /tmp/cligen-a12r2-input/us-2015-2026.07.tar.gz

Run the execute command a second time for immutable replay, then run repository
format, clippy, and test gates.

## Recovery

The evaluator publishes only complete staged artifact sets. A partial set or
identity mismatch fails closed. First artifacts remain immutable; replay uses
separate names and staging.
