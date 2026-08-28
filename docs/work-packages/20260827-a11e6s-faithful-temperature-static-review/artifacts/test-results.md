# A11E6S test results

Date: 2026-08-27

- Exact SHA-256 source inventory: PASS, 12/12 files.
- Source-authority temperature and QC trace: PASS.
- Fortran/Rust correspondence review: GO, no unresolved P0/P1.
- A11E6 comparison-path audit: PASS; no mismapped temperature field or
  aggregation defect identified.
- Existing identity evidence reviewed: 26,402,148 `DSTN1` values, 2,584
  `RANSET` calls, 189,207 `clgen` days, and 12 golden `.cli` outputs recorded
  bit- or byte-identical to the reference implementation.
- Changed-document link validation: PASS.
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`,
  `cargo test`, and `git diff --check`: PASS.
- Production Rust changes: none; coverage/CRAP gate not triggered.
