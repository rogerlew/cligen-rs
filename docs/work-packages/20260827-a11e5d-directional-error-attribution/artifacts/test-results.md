# A11E5D test results

Date: 2026-08-27

## Prospective gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 5 tests.
- Strict manifest validation: PASS; canonical digest
  `5d73bd58da622d326717dca8f63196840cb7bd43b879828c14292e2153e88425`.
- Prospective review: GO, no unresolved P0/P1.
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`,
  `cargo test`, and `git diff --check`: PASS.

## Execution and replay

- Published source: `a5e896a61db61d0b057684859c2b78ef2576d86e`.
- One incorrect abbreviated-SHA expansion was rejected before data access; the
  exact Git-reported SHA then executed.
- Exact A11E5 metric and stream-hash replay: PASS for all 320 arms.
- Directional grid: PASS, 160 paired rows, finite metrics, zero daily invariant
  failures, confirmation=false.
- Scientific output replay: PASS, byte-identical:
  - replay preflight: `4c1d396abfb8dbdb3c552bd56132e5d5b66461c8f9748de1cc159327af768c2d`;
  - directional evidence: `47c30b45116a962862be08aaa56b684df478591a7866124629df35b38aa4ae6c`;
  - directional decision: `3d12659ae3a19e387c47d0918e8b5801eb0d8a37549ccdc8f7eb1457c5f20bb7`.
- Replay elapsed 268.278 seconds; elapsed time is operational and excluded from
  scientific identity.
- Evidence review: GO, directional arithmetic and scope reproduced, no
  unresolved P0/P1.
- Final synthetic suite, manifest validation, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, `cargo test`, evidence self-hash,
  `git diff --check`, and changed-document link validation: PASS.
