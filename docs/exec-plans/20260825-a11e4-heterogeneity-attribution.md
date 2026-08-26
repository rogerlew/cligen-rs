# A11E4 heterogeneity attribution ExecPlan

## Purpose / Big Picture

Determine whether distance or regime mismatch provides a simple stable
explanation for A11E3's station-level response heterogeneity.

## Progress

- [x] 2026-08-25: operator separately authorized the post-A11E3 diagnosis.
- [x] 2026-08-25: fixed one joint model, exact max-|t| inference, stability gates, and stop rules.
- [x] 2026-08-25: published independently reviewed prospective source as `dfef66c`.
- [x] 2026-08-25: executed and replayed the closed-evidence attribution.
- [x] 2026-08-25: independently reviewed, gated, and reconciled the terminal package.

## Surprises & Discoveries

- Cross-regime candidates were descriptively farther away on average, but the
  joint conditional association was negligible and unstable.
- Ranked distance retained its positive sign across member omissions but changed
  sign under station omission; regime mismatch changed sign under both checks.

## Decision Log

- Use stations, not 160 correlated site/member cells, as independent units.
- Reduce member response to an eight-member success fraction before attribution.
- Test only distance and regime mismatch in one station-regime-adjusted model;
  do not add post-result predictors.

## Outcomes & Retrospective

The package closed `NO_STABLE_METADATA_ASSOCIATION`. Ranked distance had
coefficient `0.037254810384821986`, adjusted `p=0.9290846836419753`, and failed
the station-omission sign gate. Regime mismatch had coefficient
`-0.016770749395648543`, adjusted `p=0.9981794945987654`, and failed both sign
gates. Scientific evidence and decision replayed byte-identically. No simple
distance/regime selector refinement is supported, no confirmation evidence was
accessed, and this package launches no automatic successor.

## Context and Orientation

A11E3 found stable across-site median benefits but material stationwise
heterogeneity. Its closed JSON evidence contains all required metric rows.
A11E2's closed selector receipt supplies candidate regime and distance. No raw
observations or confirmation targets are needed or authorized.

## Plan of Work

Publish source/manifest/schema/tests first. The analyzer authenticates itself and
all inputs, validates the exact grid and joins, constructs 20 station summaries,
runs all 1,327,104 within-regime assignments plus frozen leave-one-member and
leave-one-station checks, writes compact atomic JSON evidence and a four-way
disposition, then replays once.

## Concrete Steps

From `/Users/roger/src/cligen-rs` run:

```sh
/Users/roger/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 docs/work-packages/20260825-a11e4-heterogeneity-attribution/artifacts/test_analyze.py
/Users/roger/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 docs/work-packages/20260825-a11e4-heterogeneity-attribution/artifacts/analyze.py --validate-manifest
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

After publication, invoke `analyze.py --execute --source-commit` with the exact
40-character `origin/main` commit. Expect 160 authenticated rows, 20 station
summaries, two test results, confirmation=false, and one fixed disposition.
Repeat once and require attribution evidence and decision bytes to match.

## Validation and Acceptance

Acceptance requires every package gate, honest signal/no-signal interpretation,
and consistent terminal records. A valid null result completes the package.

## Idempotence and Recovery

Outputs are atomic JSON. A failed preflight may be retried only after resolving
identity drift. The published source and input evidence are immutable; replay
must reproduce scientific output bytes exactly, excluding elapsed time.

## Artifacts and Notes

Artifacts live under
`docs/work-packages/20260825-a11e4-heterogeneity-attribution/artifacts/`.

## Interfaces and Dependencies

Python 3.12.13 and NumPy 2.3.5 are frozen. Inputs are the closed A11E3 evidence,
decision, and receipt plus the A11E2 selection receipt. No production interface
is introduced.

Revision note (2026-08-25): completed with no stable metadata association.
