# A11E5 test results

Date: 2026-08-27

## Prospective source gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 5 tests.
- Strict manifest validation: PASS; canonical digest
  `757d2d6340604215f441a8d8e1e75f547abf7c7528f1d98b061c97393d0bf227`.
- Prospective review: GO, no unresolved P0/P1.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS; repository-declared evidence tests remain ignored.
- `git diff --check`: PASS.

## Execution and replay

- Published source: `2eb57485c53d6a85af0cd8ce502314769fe50702`.
- One incorrect abbreviated-SHA expansion was rejected at source identity
  before data loading or generation; the exact published SHA then executed.
- Calendar, role, dependency, selector, and fit authentication: PASS.
- Grid: PASS, 160 paired rows / 320 streams, finite metrics, zero daily
  invariant failures, confirmation=false.
- Frozen disposition: `NOT_VIABLE_ON_FROZEN_CRITERION`; 142 materially
  improved, 9 neutral, 9 materially worse.
- First execution elapsed 267.299 seconds; replay elapsed 267.443 seconds.
  Operational elapsed time is excluded from scientific identity.
- Byte-identical replay hashes:
  - calendar preflight: `66d014f8d24799c765e95b0e204353a1c154203b2f7075cb04133f5eb6bbd6e9`;
  - fit authentication: `8f67885f7330c7a32b8a170a523c5ab4284020cfd827669195594df83a9cf788`;
  - development evidence: `b85fc59a9925557565ba26163e165f834f6bd8d272122baebbb71b0da9673f47`;
  - development decision: `0d808f9ccc5cf5e9317ea328d1e480aff38861f2d30412ca4c1b1659cda5056d`.
- Evidence review: GO, exact decision arithmetic reproduced, no unresolved
  P0/P1.
- Final synthetic suite, manifest validation, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, `cargo test`, evidence self-hash,
  `git diff --check`, and changed-document link validation: PASS.
