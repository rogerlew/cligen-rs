# A11E2 test results

Date: 2026-08-25

## Prospective source gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 11 tests.
- Strict runtime manifest validation: PASS; canonical digest
  `47eb68e304d10fc5c57d5fabf2cc6e35dbfcb5072f3d689e7021b7ee0c254442`.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS (repository-declared ignored evidence tests remain ignored).
- `git diff --check`: PASS.

- Independent corrected-source review: GO, no unresolved P0/P1.

## Observed execution and closure gates

- Published execution source: `e15369ad26f4e0b646f5f4665912dd6a37e35e3a`.
- Inherited source/dependency and complete input authentication: PASS.
- Metadata selector: PASS, 20 station-keyed selections and 20 distinct
  candidate-fit points; mapping independently reproduced.
- Calendar/role preflight: PASS, 1,440 fit-corpus objects and 20 development
  objects with exact inherited masks.
- Development generation: PASS, 20/20 unique common-RNG streams, finite metrics,
  and zero invariant failures.
- Confirmation target access: false.
- Receipt/output hashes, evidence self-hash, A11E1 baselines, primary medians,
  bootstrap, and decision recomputation: PASS in independent review.
- Deterministic replay: PASS; all five scientific output files were
  byte-identical. The execution receipt's elapsed time is operational and was
  regenerated.
- Final synthetic suite: PASS, 11 tests.
- Repository gates: PASS (`cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test`).
- `git diff --check` and changed-document relative links: PASS.
- Independent evidence review: final closure GO; no remaining P0/P1.
