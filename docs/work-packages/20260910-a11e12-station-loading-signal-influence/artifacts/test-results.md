# A11E12 test results

Date: 2026-09-10

- Python 3.12.14 / NumPy 2.3.5 tests: PASS, 3 tests.
- Manifest digest: `a3b83f9f50f37d8d788b4fba4ddabc92c50338649dd7fb9f7682154115cba0c0`.
- Exact-source analysis and independent replay: PASS; evidence and decision
  were byte-identical.
- Exact input hashes, 20 stations, seven predictors, three failure surfaces,
  leave-one-out arithmetic, evidence self-hash, JSON, links, and
  confirmation=false: PASS.
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`,
  and `git diff --check`: PASS.
- Coverage/CRAP not triggered; no production function changed.
