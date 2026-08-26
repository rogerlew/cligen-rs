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

## Terminal HOLD closure — 2026-08-26

| Gate | Result | Evidence |
|---|---|---|
| Locked release build | PASS | source commit `d94f6eab53c9103c797b332ae51aea3a87341bcb`; binary SHA-256 `5dcf78ef99dd8908c3580e070fabf662235666100004292ec139941d1900b698` |
| Calendar preflight | PASS | 240 sites; 40 per regime; SHA-256 `cb489ef3ad4a6fcf1463364db427d2fc47a3dc2e0642c39a8e2967488552677d` |
| Scientific execution | HOLD | stopped at site index 49 on production `month 6 cannot be localized`; no decision emitted |
| Failure receipt integrity | PASS | semantic self-hash `0f5e786af89b0281eea429503cd6ecefe56a674136c6494cab13bbb7b0879da6` |
| Scientific replay | NOT APPLICABLE | no scientific evidence or decision artifact was emitted |
| Confirmation firewall | PASS | target series access remained false |
| Completed-evidence review | GO | no unresolved P0/P1; exact failure reconstructed independently |
| `cargo fmt --check` | PASS | terminal tree |
| `cargo clippy --all-targets -- -D warnings` | PASS | terminal tree |
| `cargo test` | PASS | terminal tree |
| LLVM coverage + CRAP | PASS | regenerated lcov; 0/830 functions above 30 |
| `git diff --check` and relative links | PASS | terminal tree |
