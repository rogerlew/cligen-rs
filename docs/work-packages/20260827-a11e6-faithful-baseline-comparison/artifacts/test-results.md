# A11E6 test results

Date: 2026-08-27

## Prospective gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 3 tests.
- Strict manifest validation: PASS; canonical digest
  `bd283c199e84f523f8408400ff930dd1a37fc8b13524f97c7823bcc3f5fecf54`.
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`,
  `cargo test`, and `git diff --check`: PASS.

## Execution and replay

- Initial published source `cf0ee5cbd8485962f31178d20751f098c1aa6c7d`
  failed closed before stream generation on missing inherited fit
  materialization; no scientific output was published.
- Repaired published source:
  `2ae1d5d9204781a54e6f3762624d215958b26597`.
- Fresh `cargo build --release --locked --bin cligen`: PASS twice; binary
  SHA-256 `9dc8d7a1699b2ee3941903dcb472819500e54755ea6dbf3e7c3b911b309dd9d7`
  on both executions.
- Exact station database and 20 source `.par` identities: PASS.
- Faithful grid: PASS, 160 streams and 935,040 daily rows, finite metrics,
  exact generated calendar coverage, confirmation=false.
- Scientific replay: PASS, byte-identical:
  - calendar/missingness preflight:
    `b671b95d5c3cda901c5dd82e6ec67b83e8b8e5b8af2c6f559835f93d042a8f5c`;
  - development evidence:
    `debe78506bfa2a8184b68e32b55bc6ce05907c3bf392cea9699c914247d0bb3b`;
  - development decision:
    `0bc147cdeb3cf422c25bd9b0fb02df89e576e97d930f265decda26dedc1084be`.
- Evidence review: GO, no unresolved P0/P1.
- Final evidence self-hash, 160 per-stream provenance-chain checks,
  changed-document links, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, `cargo test`, and
  `git diff --check`: PASS.
