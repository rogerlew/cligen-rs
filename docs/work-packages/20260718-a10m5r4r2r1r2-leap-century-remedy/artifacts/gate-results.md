# Gate results

All entries are `Ran` on 2026-07-18 from `main`.

| Gate | Result |
|---|---|
| `verify_freeze.py` against the exact 354-file comparator tree | PASS — `A10M5R4R2R1R2-FREEZE-READY` |
| Two complete scoring runs | PASS — byte-identical SHA-256 `d1f877f0dc298f129019dbf7d093de8033f9df10d5a694f3038c9e76b832e0a6` |
| `verify_result.py` | PASS — `A10M5R4R2R1R2-RESULT-VERIFIED` |
| Python compilation for package scorer and verifiers | PASS |
| Comparator scratch cleanup | PASS — exact evaluation scratch root absent; recoverable Trash copy recorded |
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS |

No production function in `crates/` changed, so the production-function
coverage and CRAP gates do not apply to this package.
