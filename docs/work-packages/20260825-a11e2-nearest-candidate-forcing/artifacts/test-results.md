# A11E2 test results

Date: 2026-08-25

## Prospective source gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 11 tests.
- Strict runtime manifest validation: PASS; canonical digest
  `47eb68e304d10fc5c57d5fabf2cc6e35dbfcb5072f3d689e7021b7ee0c254442`.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS (repository-declared ignored evidence tests remain ignored).
- `git diff --check`: PASS.

- Independent corrected-source review: GO, no unresolved P0/P1.
