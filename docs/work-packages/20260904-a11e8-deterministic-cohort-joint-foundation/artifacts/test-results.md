# A11E8 test results

Date: 2026-09-06

## Prospective gates

- Bundled Python 3.12.14 / NumPy 2.3.5 synthetic suite: PASS, 9 tests.
- Strict manifest validation: PASS; canonical digest
  `6aa07fd460acb5b30ed4e9863b38a26787f75891a3d67caae0113844ec711aa1`.
- Exact published execution source:
  `00babe13e88c2af90b10b89e71728155a8a999bb`.

## Execution and replay

- Fresh `cargo build --release --locked --bin cligen`: PASS twice; binary
  SHA-256 `4dccfd0163aaa6859a7b46a7f614a6820ca16ec72b7d753fdf65f1454d58cb16`
  on the recorded replay.
- Exact station database and 20 source `.par` identities: PASS.
- Calendar/missingness preflight: PASS; 5,844 normalized axis rows, 5,840
  observed rows, four expected masked dates per object, and confirmation=false.
- Grid: PASS; 640 faithful streams, 640 derived candidates, 1,280 finite score
  records, 80 mixed-model selections, and 80 faithful-only selections.
- Scientific replay: PASS, byte-identical:
  - calendar/missingness preflight:
    `e494480265aeb4ee72c7bdf41722cb78774d9e94b7d4d98f6fa86bad4fca4231`;
  - thermal loading bundle:
    `55f4a4d8d0f256768b9e4ca529723487c3214808d8696bf8328baaf9c891eb59`;
  - development evidence:
    `a0de09b4691826067286aaedd5495c03c43f6e64c4d203d8fdb7723692f18922`;
  - development decision:
    `bd6fe639c3993ca5c2d5cb45c8374d7c2aadc13d427125f9613158f915b0a797`.
- Provenance receipts differ only in the execution-receipt hash; elapsed time
  is operational and excluded from scientific replay by specification.
- Evidence review: GO, no unresolved P0/P1.

## Final gates

- Evidence self-hash, execution-output hashes, complete model/selection counts,
  JSON parsing, changed-document links, and runtime cleanup: PASS.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS.
- `git diff --check`: PASS.
- Coverage/CRAP: not triggered; no production function under `crates/` changed.
