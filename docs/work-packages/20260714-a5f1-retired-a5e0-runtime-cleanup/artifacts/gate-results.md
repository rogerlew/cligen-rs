# A5f1 Gate Results

Run date: 2026-07-14

## Package evidence gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Release-exposure classification | PASS | `release-exposure-audit.md`; A5e0 classified unshipped |
| Baseline evidence capture | PASS | `a5f1-baseline-v1.json` |
| Runtime-absence verifier | PASS | `python artifacts/verify-a5f1.py` |
| Pre-A5e0 source restoration | PASS | Affected production paths equal commit `27e5e7754bdfafcca649a71d0f5576910433d0d3` |
| Cargo target absence | PASS | `cargo metadata --no-deps --format-version 1` exposes no A5e0 target |
| Package-file absence | PASS | `cargo package -p cligen --list --allow-dirty` contains no A5e0 path |
| Faithful CLI parity | PASS | `cargo test --test cli_parity` |
| Historical-record preservation | PASS | All preserved hashes match `a5f1-baseline-v1.json` |

Verifier terminal output:

```text
A5f1 runtime absence, source restoration, and record preservation: PASS
```

## Repository gates

| Gate | Result | Notes |
| --- | --- | --- |
| `cargo fmt --check` | PASS | No formatting differences |
| `cargo clippy --all-targets -- -D warnings` | PASS | No warnings |
| `cargo test` | PASS | Full workspace suite; declared ignored tests remain ignored |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | PASS | LCOV evidence written to `target/lcov.info` |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | PASS | 730 functions analyzed; 0 functions above CRAP 30 |
| `git diff --check` | PASS | No whitespace errors |

## Terminal package state

`A5E0-RUNTIME-RETIRED`
