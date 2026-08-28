# A11E7 test results

Date: 2026-08-28

## Prospective and corrective gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 4 tests.
- Strict manifest validation: PASS; canonical digest
  `5606a0ae4c9782e42db159d6f774b94ad2b724afe1d62a817a22437284ef42b7`.
- Initial scaffold source:
  `84baddf0e5e26adb0e9b8a6cd819bfbd172e742f`.
- The first exact-source attempt failed closed at station `co050130`, burn
  `53`, before any scientific artifact publication. The quality-report
  relational correction and regression test were published as
  `984b983e6d058aa8b190cef02667e328aad39ebc`.
- Corrective `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`,
  `cargo test`, targeted regression, and `git diff --check`: PASS.
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`: PASS.
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**'
  --fail-above`: PASS; 861 production functions analyzed and none exceeds
  CRAP 30.

## Execution and replay

- Fresh `cargo build --release --locked --bin cligen`: PASS twice; binary
  SHA-256 `2136e940208b134e7bbaac677abdc038030fb406a62014847ab2dad67d4db665`
  on both executions.
- Exact station database and 20 source `.par` identities: PASS.
- Grid: PASS, 1,280 streams, 7,480,320 daily rows, 640 finite paired metric
  rows, exact generated calendar coverage, confirmation=false.
- A11E6 faithful anchor: PASS, 160 stream-summary and metric replays.
- Scientific replay: PASS, byte-identical:
  - calendar/missingness preflight:
    `532159a54cf40a26ec48abbfcc2ceb82bf83c2fbc5e2018935a11045090c950d`;
  - development evidence:
    `809b400f6126714373f09638bc04a6340e75caffb543dcbed0731bfdfe67f7b5`;
  - development decision:
    `41143b9b5fdce8e3bc22a024252c167d0fe15ed7bbde675918105227c416f582`.
- Evidence review: GO, no unresolved P0/P1.
- Final evidence self-hash, 1,280 per-stream provenance-chain checks,
  execution-output hashes, changed-document links, package tests, standard
  Cargo gates, coverage/CRAP, and `git diff --check`: PASS.
