# A11E3 test results

Date: 2026-08-25

## Prospective source gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 17 tests.
- Strict runtime manifest/schema validation: PASS; canonical digest
  `9e8bf3b3eac8cff8c81c4e96c67532a891ccfbc71fcbb3313dd2a63fe665b8b7`.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS (repository-declared ignored evidence tests remain ignored).
- `git diff --check`: PASS.
- Independent corrected-source review: GO, no unresolved P0/P1.

Observed execution and replay gates pending publication of this source.
