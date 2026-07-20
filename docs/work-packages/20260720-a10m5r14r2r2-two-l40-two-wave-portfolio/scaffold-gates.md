# Scaffold gates

- exact R14R2R1 published source and execution-hold identity
- exact reconstruction of its prepared manifest from the R14R2 parent
- unchanged candidate, objective, calendar, seed, selector, metric, and replay
  science surfaces
- exact composed checker slots 0 and 1
- fresh occupancy requires four-L40 inventory and at least two idle devices
- exactly two allocated NVIDIA L40 devices
- exactly two deterministic waves and two children per wave
- no overlap between waves; four total children launched and reaped
- token index 0/1 reused only after the prior wave is fully reaped
- disjoint output and cache roots across all four children
- unchanged per-candidate publication and parameter totals
- 515 GPU-minute-equivalent ceiling
- protected confirmation and solar roles sealed
- package tests, Python compilation, JSON parsing, shell syntax,
  `cargo fmt --check`, clippy with warnings denied, full Rust tests, toolkit
  tests, and `git diff --check`

Coverage/CRAP is not triggered because no production function under `crates/`
changes.

## Prepublication result

All scaffold gates pass. The observed changed-file roster is the exact frozen
twelve-asset operational set, and the selected frozen science set is
byte-identical. Live authority, admission, execution, collection, replay, and
cleanup remain postpublication gates.

## Corrective r2 result

The authenticated `r1` execution exposed one stale four-token uniqueness
predicate before any candidate launched. The `r2` transform now generates
exactly two distinct-token checks both in `allocation_ok` and in the named
wave-binding gate while retaining four children in waves `[0,0,1,1]`.

Fresh 51-asset generation contains only `r2` run-bound executable identities
and keeps protected roles sealed. The strengthened regression test fails
against the `r1` transform. Four focused package tests, 86 toolkit tests,
generated Python compilation and shell syntax, `cargo fmt --check`, clippy with
warnings denied, the full Rust suite, and `git diff --check` pass.
