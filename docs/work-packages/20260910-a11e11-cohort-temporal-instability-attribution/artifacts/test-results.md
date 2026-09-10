# A11E11 test results

Date: 2026-09-10

- Python 3.12.14 / NumPy 2.3.5 tests: PASS, 2 tests.
- Manifest digest: `bff6a2367faec2eca73c9134eeb2e149c73fafef18795527d0c0d5b93fd13934`.
- Exact-source authenticated analysis and independent replay: PASS.
- Evidence and decision byte identity, 640-record reconstruction, three exact
  failure surfaces, evidence self-hash, input/output hashes, JSON, links, and
  confirmation=false: PASS.
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`,
  and `git diff --check`: PASS.
- Coverage/CRAP not triggered; no production function changed.
