# A12 station selection heuristic evaluation ExecPlan

## Purpose / Big Picture

Decide whether cligen-rs should retain its current PRISM-aware automatic
station heuristic or prefer the simpler closest-station policy, using an
authenticated validation corpus that was not used to fit either policy.

## Progress

- [x] 2026-08-26: operator authorized A12 and required source `.par` and
  executing cligen binary SHA-256 values in the station-selection receipt.
- [x] 2026-08-26: selected the 240 registered `fit_validation` locations and
  kept development and confirmation roles out of selector evaluation.
- [x] 2026-08-26: froze and independently reviewed prospective source; closure
  review returned GO with no unresolved P0/P1 or blocking P2.
- [ ] Publish, execute, and replay A12.
- [ ] Review evidence, run gates, and reconcile the terminal package.

## Surprises & Discoveries

- The active PRISM specification already promised a source `.par` hash in
  `station-selection.json`, but the implementation placed it only in
  `localization.json`.
- The existing artifact manifest hashes the executable, but the selection
  decision itself is not bound to that executable.

## Decision Log

- Evaluate the selector directly on the 240 fit-validation objects; do not
  reuse A11's 20 development stations.
- Compare structural station parameters against observed daily descriptors
  because PRISM localization intentionally replaces monthly precipitation and
  temperature levels.
- Treat the WEPPpy-style selector as a named reference candidate with Daymet
  target elevation, not as port authority or claimed behavior identity.

## Outcomes & Retrospective

Pending execution.

## Context and Orientation

The current public `cligen prism run` command uses a deterministic ten-station
rank-sum selector, localizes six `.par` rows to PRISM normals, and then invokes
the unchanged faithful generator. A12 evaluates only the donor-selection
decision. The selected donor continues to supply stochastic structure that
PRISM does not observe.

## Plan of Work

Amend the PRISM receipt contract and implementation first. Build a strict
source-bound evaluator that authenticates the A10 cohort, Daymet shards, PRISM
runtime, station collection, source `.par` files, and release binary. Recreate
all three selectors, compute observed monthly structural descriptors, apply the
frozen paired decision rule, replay the scientific artifacts, and close the
package after independent review.

## Concrete Steps

From `/Users/roger/src/cligen-rs`:

```sh
python3 docs/work-packages/20260826-a12-station-selection-heuristic-evaluation/artifacts/test_evaluate.py
python3 docs/work-packages/20260826-a12-station-selection-heuristic-evaluation/artifacts/evaluate.py --validate-manifest
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

After publication, use the evaluator's `--build --source-commit COMMIT` mode;
it runs `cargo build --release --locked --bin cligen` and writes the
source/toolchain/Cargo.lock/binary-bound build receipt. Execute with the exact
40-character `origin/main` commit, `target/release/cligen`, that build receipt,
and the registered `us-2015-2026.07.tar.gz` archive. Repeat once and require
byte-identical evidence and decision artifacts.

## Validation and Acceptance

Acceptance requires exact identities, complete 240-site evidence, one frozen
disposition, deterministic replay, independent GO, human CLI documentation,
and all repository gates. A result preferring closest is complete evidence.

## Idempotence and Recovery

Scientific JSON outputs are atomic. Failed preflight publishes no scientific
decision. A retry is allowed only after resolving the named identity or input
failure. Replay may change elapsed time only.

## Artifacts and Notes

Package artifacts live under
`docs/work-packages/20260826-a12-station-selection-heuristic-evaluation/artifacts/`.

## Interfaces and Dependencies

Rust stable toolchain, the bundled Python 3.12.13/NumPy 2.3.5 runtime, the
registered PRISM runtime, `us-2015@2026.07`, and the A10 normalized Daymet
fit-validation corpus. No network access occurs during evaluation.

Revision note (2026-08-26): initial prospective plan.
