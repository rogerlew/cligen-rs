# Gate results

- Published source on `main`: PASS, `7cc30f85720828faf8d79d8b21ff92d5c3dcb482`.
- Independent scaffold review: ACCEPT after corpus-pin authentication.
- Package tests: PASS, 24 tests.
- Toolkit tests: PASS, 79 tests.
- Science, freeze, and real corpus-layout verifiers: PASS.
- Full 1,440-object calendar replay: PASS and byte-identical, SHA-256
  `7f58a20eae635d9453ea86a473072b9e2597195ffc1d71660184d3e70b130a68`.
- Asset preparation, staging, and exact remote verification: PASS.
- Authority/plan initialization: PASS, `e1533b19…` / `eb8a988f…`.
- Control admission: PASS, 16/16 gates.
- Portable setup, corrected corpus root, and calendar preflight: PASS.
- Control training: HOLD; the parent science launcher lacked the deterministic
  CuBLAS workspace assignment exported only in its child bootstrap.
- Candidate admission/submission/science: NOT RUN; all ten roles were stopped
  as `NOT_EXECUTED_UPSTREAM_FAILURE`.
- Authenticated sparse collection: PASS, 13 present / 140 absent.
- Job-local and exact remote cleanup: PASS.
- Recovery reserve release and toolkit closure: PASS.
- Final independent execution review: ACCEPT after one precision correction;
  no findings remain.
- Repository formatting, lint, and test gates: PASS after record
  reconciliation (`cargo fmt --check`, `cargo clippy --all-targets -- -D
  warnings`, and `cargo test`).

Coverage/CRAP was not required because no production function under `crates/`
changed.
