# A11E9 test results

Date: 2026-09-10

- Python 3.12.14 / NumPy 2.3.5 synthetic tests: PASS, 3 tests.
- Manifest digest: `49de9d52a9bb9860edcff27e44f3e332c3cfb205ccebacbba78850f18ed40fb1`.
- Exact-source 640-stream execution: PASS.
- Compact-input scientific replay: PASS, byte-identical preflight, evidence,
  and decision.
- Complete 640-record/five-arm grid, zero-sum balancing, evidence self-hash,
  output hashes, JSON, links, and runtime cleanup: PASS.
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`,
  and `git diff --check`: PASS.
- Coverage/CRAP not triggered; no production function changed.
