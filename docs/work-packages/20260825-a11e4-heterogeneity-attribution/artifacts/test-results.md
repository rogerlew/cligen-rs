# A11E4 test results

Date: 2026-08-25

## Prospective source gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 15 tests.
- Strict manifest/schema validation: PASS; canonical digest
  `358ff235f70aa69b7216419e8864e06c312a84457dbc08df5e8997381442f666`.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS (repository-declared ignored evidence tests remain ignored).
- `git diff --check`: PASS.
- Independent corrected-source review: GO, no unresolved P0/P1.

Attribution execution and replay pending publication of this source.
