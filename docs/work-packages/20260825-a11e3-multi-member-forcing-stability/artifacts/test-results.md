# A11E3 test results

Date: 2026-08-25

## Prospective source gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 17 tests.
- Strict runtime manifest/schema validation: PASS; canonical digest
  `9e8bf3b3eac8cff8c81c4e96c67532a891ccfbc71fcbb3313dd2a63fe665b8b7`.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS (repository-declared ignored evidence tests remain ignored).
- `git diff --check`: PASS.
- Independent corrected-source review: GO, no unresolved P0/P1.

## Observed execution and closure gates

- Published execution source:
  `ac254ee4fc2bc0073a4f4c351e555cc517c49f3d`.
- Runtime and complete source/dependency/input authentication: PASS.
- Calendar/role preflight: PASS; 1,440 fit objects (1,200 candidate-fit and
  240 fit-validation), 20 development objects, exact official-365 masks.
- RNG preflight: PASS; 160 annual, 160 hurdle, 30,720 daily ordinals, and
  153,600 daily domain streams without collision.
- Selector, inherited fit, regional locations, and nearest locations: PASS.
- Development grid: PASS; 160 paired rows / 320 cells, finite metrics, zero
  invariant failures, exact member-0 anchor replay, confirmation=false.
- Frozen decision: PASS; all 16 primary deltas strictly negative,
  `STABLE_FOR_EXPLORATION`.
- Deterministic replay: PASS. First execution elapsed 260.405071292 seconds;
  replay elapsed 260.400116750 seconds. Elapsed time is operational and excluded
  from scientific identity. Both passes produced the exact same hashes:
  - calendar/RNG preflight: `49d86f2da3a00ad05a115c17b91a5c820a740f5b8acbbf0127a0b192bb5eb6a4`;
  - fit authentication: `5cdcddec1e411e1b0a726439ea0944db2141462de451dcebe7d04e28e232d523`;
  - development evidence: `834d9af57679a0a252622d7c29fb223985833b85022a8bc55656f7a24daaa930`;
  - development decision: `06537916809199ed0857ce8d8af2dab77f86975bb67bb536f41651ce5d424d37`.
- Receipt output hashes/sizes and evidence self-hash: PASS.
- Independent evidence review: final closure GO; no remaining P0/P1.
- Final synthetic suite and manifest validation: PASS, 17 tests and canonical
  digest unchanged.
- Final repository gates: PASS (`cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test`).
- `git diff --check` and changed-document relative links: PASS.
