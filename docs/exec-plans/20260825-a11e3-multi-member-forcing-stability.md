# A11E3 multi-member forcing stability ExecPlan

## Purpose / Big Picture

Determine whether A11E2's location-conditioning signal survives eight fixed
stochastic members without changing any scientific surface.

## Progress

- [x] 2026-08-25: inherited the independently recommended A11E2 successor.
- [x] 2026-08-25: fixed the eight-member grid, common-RNG mapping, and strict rule.
- [x] 2026-08-25: published independently reviewed source `ac254ee`.
- [x] 2026-08-25: preflighted and executed the 320-cell development grid.
- [x] 2026-08-25: replayed byte-identically, reviewed, gated, and reconciled.

## Surprises & Discoveries

- A11E1's evaluator hardcodes member 0, so A11E3 requires a local member-aware
  transcription with an exact member-0 replay gate.

## Decision Log

- Use members 0–7, matching the earlier A11 eight-member design precedent.
- Require both primary median improvements in every member; ties are failures.
- Keep secondary summaries descriptive and prohibit result-driven tuning.

## Outcomes & Retrospective

All 16 fixed primary deltas were negative with zero invariants, exact member-0
parity, and confirmation false, yielding `STABLE_FOR_EXPLORATION`. Scientific
outputs replayed byte-identically. The result is an across-site-median mechanism
signal, not stationwise dominance: both metrics improve in 66/160 cells and
only four stations do so in every member. Independent review recommends closing
without automatic succession; confirmation remains sealed pending a separately
authorized prospective decision.

## Context and Orientation

A11E1 established the regional-median circular-block arm at member 0. A11E2
changed only its location vector to a coordinate-selected candidate and found
both primary medians improved. A11E3 holds both adapters fixed and changes only
stochastic member identity.

## Plan of Work

Publish manifest/schema/executor/tests first. Runtime then authenticates the
published commit and all inherited sources/evidence, repeats calendar and
selector/location preflight, verifies the full RNG identity grid before draws,
fits once, evaluates both adapters for members 0–7, checks member-0 parity,
applies the frozen rule, writes atomic evidence, and replays it.

## Concrete Steps

From `/Users/roger/src/cligen-rs`, use the bundled Python 3.12 runtime to run
the synthetic suite and manifest validation. Commit/push the prospective source
to `main`, then execute with that exact 40-character commit. Preserve first-run
scientific outputs, rerun, and compare their bytes; elapsed time is operational.

The concrete prospective commands are:

```sh
/Users/roger/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 docs/work-packages/20260825-a11e3-multi-member-forcing-stability/artifacts/test_execute.py
/Users/roger/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 docs/work-packages/20260825-a11e3-multi-member-forcing-stability/artifacts/execute.py --validate-manifest
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

Expect all synthetic tests to pass, one canonical manifest digest, and all
three Cargo commands to exit zero. After the prospective commit is pushed, run:

```sh
/Users/roger/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 docs/work-packages/20260825-a11e3-multi-member-forcing-stability/artifacts/execute.py --execute --source-commit <published-40-character-commit>
```

Expect 1,440 fit objects, 1,200 candidate-fit objects, 20 development objects,
160 paired rows, 320 cells, zero invariants, exact member-0 replay, and
confirmation access false. Repeat the same command once and compare the four
scientific output files byte-for-byte.

## Validation and Acceptance

Acceptance requires the gates in the package, terminal consistency across all
records, and independent review without unresolved P0/P1. A valid scientific
non-improvement is complete evidence, not a blocker.

## Idempotence and Recovery

Outputs are atomic JSON files. A failed or interrupted run may be repeated only
after source/input identities are rechecked. Scientific replay must be exact;
only the execution receipt's elapsed field may change.

## Artifacts and Notes

All compact artifacts live under
`docs/work-packages/20260825-a11e3-multi-member-forcing-stability/artifacts/`.
No confirmation series or raw restricted data is copied.

## Interfaces and Dependencies

The executor imports the authenticated A11E2 and A11E1 Python research
executors and strategy lab. It consumes their frozen manifests, receipts, and
existing local A10/A9 data paths. It introduces no production interface.

Revision note (2026-08-25): initial prospective plan.

Revision note (2026-08-25): recorded published execution, replay, independent
evidence review, terminal disposition, and campaign stop boundary.
