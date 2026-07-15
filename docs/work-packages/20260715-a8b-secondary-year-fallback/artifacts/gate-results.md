# A8b gate results

Date: 2026-07-15

Terminal: `USE-LEGACY-DAILY-FALLBACK`

## Prospective and parent gates

- A8a parent authorization: PASS — terminal
  `CONTINUE-A8B-DRY-PARTITION`, all eight parent guards true, and exactly five
  development plus five confirmation fallback identities reproduced.
- Alternative set: PASS — exactly `legacy_daily_only_v1` and
  `bounded_eof2_copula_ar1_reallocation_v1`; no scalar-IID or A5 identifier.
- Feasibility contract SHA-256:
  `59dcb9f53a9f551d7eb296e1413697e7e1f1b577a60774af870caf2a6520bf1b`.
- Initial prospective freeze SHA-256:
  `b66f0c8d3788e0230db5958c301a7a4a68d2448d1bd871eb83676daf5bc9fdfc`.
- Amendment 001: PASS — first fit reached in-memory annual aggregation and
  station-month standardization, but no coefficient, metric, or decision
  artifact; amendment only reports frozen candidate failure and cannot select
  it. Amendment SHA-256:
  `3baa2e005fa99f99309185cc5f1a6dd1de3a5097062314aeaa64b35bb2b1bc4e`.
- Successor freeze SHA-256:
  `dcd2ecf84b5f3e99cf3f93c6d800e65dd673f4f6cd53e8be164f557165d4e3bf`.

## Candidate and decision gates

- Registered training/validation intake: PASS — 300 training and 160
  validation station-years over ten fallback stations.
- Independent failure confirmation: PASS — all 30 `ca042713` June totals in
  1980--2009 are exactly 0.0 mm in archived Daymet source
  `5a052c0180e0501056fe7b0dadc73b48d6cae70fdedb905edfaf7aad23f7b1bd`;
  sample SD is exactly zero.
- Fail-closed fit: PASS — no EOF, coefficient, monthly budget, or validation
  metric was emitted; all candidate guards false.
- Null certification: PASS — selected `legacy_daily_only_v1`, no secondary
  state and no additional RNG.
- Exact output reproduction:
  `python3 artifacts/verify-a8b.py --reproduce` — PASS.
- Coefficient sentinel SHA-256:
  `4015e85261e0f9c01d094938113f7b958b32bdd47e6794ed3fa7e0e5afa42ef4`.
- Analysis SHA-256:
  `c235e9a96f10c9df9df94c89b1929a54b630b8e2c8eef4055d0acce830dbdcc9`.
- Decision SHA-256:
  `b227951faa72287afd859fb9872eb75aa559714ab6b5efd2303560b73e5a1efb`.
- Climate-output exclusion: PASS — zero `.cli` files under the package.
- Consolidated review: ACCEPT — zero open P1/P2 findings; four scoped P3
  observations retained in `review.md`.

## Repository gates

- `cargo fmt --check` — PASS.
- `cargo clippy --all-targets -- -D warnings` — PASS.
- `cargo test` — PASS; 192 passed, 10 ignored, zero failed.
- `git diff --check` — PASS.

Coverage and CRAP gates are not applicable: A8b changes no production function
under `crates/`.
