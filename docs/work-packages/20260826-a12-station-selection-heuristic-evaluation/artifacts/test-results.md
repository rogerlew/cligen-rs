# A12 test results

## Prospective source — 2026-08-26

| Gate | Result | Evidence |
|---|---|---|
| Evaluator synthetic suite | PASS | 16 tests |
| Manifest validation | PASS | canonical SHA-256 `1e18770b05dd1a7ab11896308807c685806f1367c812b148e8f1a879cab37250` |
| `cargo fmt --check` | PASS | no formatting drift |
| `cargo clippy --all-targets -- -D warnings` | PASS | no warnings |
| `cargo test` | PASS | complete workspace suite; declared long evidence tests remain ignored |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | PASS | regenerated coverage input |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | PASS | 0/830 functions above 30 |
| `git diff --check` | PASS | no whitespace errors |
| Changed-document relative-link check | PASS | all local relative Markdown targets resolved |
| Independent prospective review | GO | no unresolved P0/P1 or blocking P2 |

Execution, replay, completed-evidence review, and terminal gates remain pending.
