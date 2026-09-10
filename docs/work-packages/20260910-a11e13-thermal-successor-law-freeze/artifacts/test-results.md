# A11E13 test results

Date: 2026-09-10

- Python 3.12.14 / NumPy 2.3.5 tests: PASS, 3 tests.
- Manifest digest: `b3e04e5175aa9699bebab99ae1f261f3085bf5f80c97ba7a11b3dae42edfba58`.
- Exact-source analysis and independent replay: PASS; evidence, decision, and
  retirement record were byte-identical.
- Complete 640-pair/four-cohort grid, finite centered normalized AR(1) states,
  zero-sum tenths, evidence self-hash, input/output hashes, JSON, links, and
  confirmation=false: PASS.
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`,
  and `git diff --check`: PASS.
- Coverage/CRAP not triggered; no production function changed.
