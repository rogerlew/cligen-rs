# A12R2 localizability and repair comparison ExecPlan

This is a living plan maintained under `.agent/PLANS.md`. A new agent can
resume from the progress ledger and exact commands below without prior chat
context.

## Purpose / Big Picture

Decide whether ordinary-localizability filtering or explicit all-dry repair is
the more defensible exploratory station-selection strategy. The visible result
is a cryptographically bound 240-site feasibility matrix, six-arm observed
comparison, deterministic decision, and review record. It cannot change a
runtime default or open confirmation.

## Progress

- [x] 2026-08-26: operator authorized the prospective corpus-wide comparison.
- [x] 2026-08-26: froze six arms, 240 by 10 feasibility, two-pass execution,
  paired inference, provenance, replay, and confirmation firewall.
- [x] 2026-08-26: first independent review returned NO-GO; corrected method
  identity, executable predecessor gates, strict schema, f64 probability snap,
  named HOLD receipts, two-pass ordering, provenance checks, and disposition
  table.
- [x] 2026-08-26: obtained independent GO on original and amended prospective source.
- [x] 2026-08-26: published amended source commit `866d0401ab757708d80a58ad9dda5683f6e000bc` and built its locked release.
- [x] 2026-08-26: executed all 2,400 feasibility cells and closed quality scoring on the frozen repair gate.
- [x] 2026-08-26: independently replayed byte-identical preflight and feasibility evidence.
- [x] 2026-08-26: closure review returned GO; terminal gates and reconciliation passed.

## Surprises & Discoveries

- A probability snapped to F6.2 is a decimal f64 in the Rust repair algebra;
  widening an already-rounded f32 changes boundary rendering of the target-
  anchored wet-day mean.
- Merely naming predecessor commits in prose does not authenticate imported
  evaluator code. A12R2 now verifies historical git blobs before import.
- The first exact-source attempt failed safely before publication because the
  inherited `1e-13` absolute component tolerance was smaller than cross-libm
  haversine drift. A complete diagnostic found maximum drift `6.68e-13 km`;
  the amendment uses `1e-12` while ranks, scores, pools, and winners stay exact.
- That authenticated diagnostic also found four current raw winners that the
  explicit A12R1 repair cannot localize. The formal A12R2 run is now expected
  to publish the full feasibility census and close on
  `HOLD-REPAIR-INELIGIBLE` before quality scoring.

## Decision Log

- Cross all three selectors with both strategies, producing six arms; do not
  collapse repair into a single current-selector arm.
- Keep all-ten ranks fixed before filtering.
- Complete all candidate feasibility, raw repair feasibility, and production
  parity before observed scoring.
- Require universal matched-family support for a strategy preference. Partial
  support is mixed; no support is no uniform advantage.
- Use the 240 fit-validation sites only. Confirmation stays sealed.
- Preserve the frozen repair gate despite the prospectively discovered four
  failures; do not retrofit zero-target or one-sided absorbing-chain behavior
  into A12R2.

## Outcomes & Retrospective

A12R2 closed before quality scoring at `HOLD-REPAIR-INELIGIBLE`. Ordinary
localization succeeded for 2,362/2,400 cells and every site retained at least
three eligible donors. Eleven raw-policy instances failed across four sites.
The first/replay preflight and feasibility files are byte-identical. No six-arm
quality estimand exists. A localizability-only selector evaluation is the
least-complex successor; zero-target and one-sided repair semantics require a
separate scientific contract.

## Context and Orientation

A12 is the immutable failed first comparison at source commit
`d94f6eab53c9103c797b332ae51aea3a87341bcb`. It stopped before scoring because
one selected donor had an all-dry June. A12R1 source commit
`de1502ad4d80a7205ac128c24e1851a42380f5b7` added the explicit opt-in
`independent-prism-v1` repair and retained ordinary localization unchanged.

The A12R2 authority is
`docs/specifications/SPEC-A12R2-LOCALIZABILITY-REPAIR-COMPARISON.md`. The
package is `docs/work-packages/20260826-a12r2-localizability-repair-comparison/`.
Its evaluator imports only the hash-authenticated A12 evaluator for established
calendar, station, PRISM, descriptor, and bootstrap primitives. The registered
station archive is external and must hash to
`f3bf68bb39e65378c1eefc9a956b514fc7cf0fb8e3377e868852f7b3f7b25ab9`.

## Plan of Work

Milestone 1 freezes and independently reviews the evaluator. Milestone 2
publishes that source to main and builds the exact commit. Milestone 3 executes
one complete feasibility/parity pass followed by scoring, then repeats the
execution and compares evidence and decision bytes. Milestone 4 independently
reviews the realized artifacts, updates this plan/package/registries, reruns
all gates, and publishes closure.

## Concrete Steps

Run from `/Users/roger/src/cligen-rs` with:

```sh
PY=/Users/roger/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
$PY docs/work-packages/20260826-a12r2-localizability-repair-comparison/artifacts/test_evaluate.py
$PY docs/work-packages/20260826-a12r2-localizability-repair-comparison/artifacts/evaluate.py --validate-manifest
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

Expected observations are a passing Python suite, one manifest digest, and all
Rust gates passing. After prospective commit `SOURCE` is pushed:

```sh
$PY docs/work-packages/20260826-a12r2-localizability-repair-comparison/artifacts/evaluate.py --build --source-commit SOURCE
$PY docs/work-packages/20260826-a12r2-localizability-repair-comparison/artifacts/evaluate.py --execute --source-commit SOURCE --cligen-binary target/release/cligen --build-receipt docs/work-packages/20260826-a12r2-localizability-repair-comparison/artifacts/build-receipt-v1.json --station-archive /tmp/cligen-a12r2-input/us-2015-2026.07.tar.gz
```

The command exited on the named HOLD after publishing preflight, complete
feasibility evidence, and failure receipt. Closure replay called the same
source-bound `execute_science` into an isolated output root, required the same
named HOLD, and required byte-identical preflight and feasibility hashes. It
published `hold-replay-receipt-v1.json`; no quality evidence or decision exists.

## Validation and Acceptance

HOLD acceptance requires: exact manifest/schema agreement; 240 sites and
exactly 2,400 candidate cells; a complete per-candidate matrix; authenticated
source `.par`, binary, station archive/tree, PRISM, Daymet, predecessor, and
output identities; production success/failure parity for the current selector;
an authenticated named failure receipt; byte-identical preflight/feasibility
replay; no quality evidence or decision; confirmation access false;
independent GO with no unresolved P0/P1; and fmt, clippy, and test passing. The
realized artifacts satisfy the scientific HOLD branch. No production functions
change, so the coverage/CRAP gate is not triggered.

## Idempotence and Recovery

Scientific JSON writes are staged outside the package, then copied into their
distinct final paths with the execution receipt copied last as the completion
marker. Existing first-run artifacts are never removed or overwritten. An I/O
interruption during publication can leave a detectable partial set; the
evaluator refuses to proceed until the operator removes only those incomplete
A12R2 outputs after inspection. A second invocation stages distinct replay artifacts, compares
the four scientific hashes to the preserved first run, and publishes them plus
a replay receipt only on identity. A frozen feasibility failure publishes the
complete 2,400-cell census, preflight, and authenticated named failure receipt,
but no quality evidence or decision. Other evaluator defects leave no partial
terminal set.

## Artifacts and Notes

Prospective sources are the manifest, schema, evaluator, tests, spec, and
package. Realized artifacts are the first-attempt and amended build receipts,
selector-parity diagnostic, calendar preflight, complete feasibility evidence,
execution failure receipt, HOLD replay receipt, review, and test results in
the package `artifacts/` directory. Large runtime inputs and temporary CLIGEN
outputs remain outside git.

## Interfaces and Dependencies

Rust stable from `rust-toolchain.toml`; locked Cargo dependencies; bundled
Python 3.12.13 and NumPy 2.3.5; registered PRISM 2026.07 runtime; registered
`us-2015@2026.07`; authenticated A10 normalized Daymet fit-validation shards;
git history containing the two predecessor source commits. Network is used
only to obtain the registered station archive before execution; evaluation is
isolated and offline.

Revision note (2026-08-26): initial prospective plan expanded after independent
NO-GO review.
